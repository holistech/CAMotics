# CAMotics — Code Review & Test Coverage Analysis

**Date:** 2026-06-21
**Scope:** Entire own source code (`src/`, ~46,800 LOC excluding bundled third-party libraries clipper/dxflib/cairo)
**Methodology:** Module-by-module review (G-code engine, simulation/rendering, GUI, language bindings/IO) plus structural test coverage analysis. The build and test suite were previously run successfully (25/25 tests green).

> **Implementation status (branch `test-suite`):** The findings were addressed across 6 projects
> — see [`docs/improvement/STATUS.md`](docs/improvement/STATUS.md). Both CRITICAL and all
> HIGH findings are fixed; the test suite grew from 25 to **45** (new suites for
> simulation, planner, error paths, Python bindings). Some MEDIUM/LOW findings were deliberately
> **not** patched after verification (false positive, regression risk, or design/UX decision)
> — each justified in STATUS.md. Measured line coverage of the tested (non-GUI) code: **40.3%**.

---

## 1. Management Summary

CAMotics is a mature, functionally rich CNC simulation software. The architecture is cleanly layered (G-code → planning → simulation → rendering → GUI), the concurrency of the voxel computation is soundly designed, and the worker→GUI threading pattern is correctly implemented.

The review nonetheless surfaces a number of **concrete correctness and robustness defects** that lead in some cases to silent mis-simulations, in others to crashes or hangs on unusual inputs. Key areas:

- **Silent mis-simulation:** An unsigned truncation bug causes material removal to fail completely for small tools (`Sweep.cpp`); division by zero in the G-code evaluator silently returns `0` instead of an error.
- **Robustness against untrusted inputs:** STL/DXF parsers and the `.camotics` project format validate inputs insufficiently (DoS through huge allocations, infinite loops, path traversal, possible XXE).
- **Memory/reference errors in the Python bindings:** several reference leaks and a Rule-of-Three violation (`PyPtr`) with potential for use-after-free.
- **One user-driven memory leak in the GUI** (Qt model on every window resize).

**By far the greatest weakness is test coverage** (see Section 4): The core piece — the simulation engine — is touched by **not a single automated test**. The 25 existing tests cover only 2 of the 6 programs and ~5% of the G/M-code table.

### Findings overview by severity

| Severity | Count | Core risk |
|-------------|:------:|------------|
| CRITICAL    | 2      | Silent mis-simulation, double DECREF (use-after-free) |
| HIGH        | 9      | Dead guard checks, DoS hangs, reference leaks, dangling data, GUI leak |
| MEDIUM      | 21     | Numerical robustness, missing validation, resource leaks, XXE/path traversal |
| LOW         | 14     | Dead code, deprecated APIs, maintainability |

---

## 2. Critical Findings (fix immediately)

### K-1 — Material removal silently fails for small tools
**`src/camotics/sim/Sweep.cpp:33-35`** — CRITICAL

```cpp
const unsigned maxLen = radius * 16;   // <-- truncation to unsigned
```
For tools with radius < 1/16 unit (common with imperial units or engraving gravers), `maxLen == 0`. Then `steps = len / maxLen` yields a division by 0 → `inf`, whose cast to `unsigned` is **undefined behavior**.

**Clarification after verification (fix in `test-suite` branch):** The symptom is platform-dependent. On x86/gcc, `(unsigned)inf` here happens to yield a large value, so that *too many* BBoxes are generated and the simulation runs through with incorrect metrics but a non-empty result (measured: 3356 instead of the correct 3740 facets in the regression test). On platforms where `(unsigned)inf == 0`, the BBox loop runs zero times → **the entire sweep is discarded, no material removal**. In every case the result is wrong and the behavior is UB.

**Fix (implemented):** `double maxLen = radius * 16;` with `(maxLen <= 0 || len <= maxLen) ? 1 : (unsigned)(len / maxLen)`. Eliminates UB and division by 0; the normal case (integer `radius*16`) remains bit-identical. Regression test: `tests/simTests/SmallToolTest`.

### K-2 — `PyPtr` violates Rule-of-Three → double DECREF / use-after-free
**`src/python/PyPtr.h:26-45`** — CRITICAL

The class defines a destructor (`Py_DECREF`) and copy-assignment (with `Py_INCREF`), but **no copy constructor**. The implicitly generated one copies `ptr` without `Py_INCREF`; both objects call `Py_DECREF` in their destructor → reference-count underflow up to use-after-free. `PyPtr` is held as a member in `PyTask`/`Runner` and copied.

**Fix:** Add `PyPtr(const PyPtr &o) : ptr(o.ptr) { if (ptr) Py_INCREF(ptr); }` (consider a move ctor).

---

## 3. Findings by Module

### 3.1 G-code Engine (`src/gcode`, 14.8k LOC)

| ID | Severity | Location | Finding |
|----|-------------|-----|--------|
| G-1 | HIGH | `ControllerImpl.h:161`, `.cpp:740,1084` | `unsigned getCurrentTool() < 0` is **always false** → dead "no tool" guard check; G43/radius compensation continue running with an invalid tool number. Fix: return type `int`, sentinel `-1`. |
| G-2 | HIGH | `ControllerImpl.cpp:503,515` | `drill()` reads L as `unsigned` without validation; negative L → billions of iterations (DoS hang), L=0 → silent non-drilling. Fix: read as `int`, check `>= 1`. |
| G-3 | HIGH | `interp/Evaluator.cpp:57-61,66-111` | Division/modulo by 0 is only logged and returns **`0`** → incorrect positions/offsets flow in unnoticed. `SQRT(<0)`, `LN(≤0)`, `pow(neg)` produce silent NaN. Fix: throw instead of returning 0; check domain. |
| G-4 | MEDIUM | `ControllerImpl.cpp:71,981` | Block variables are not reset per block → unguarded `getVar('P'/'R'/'L'/'D'/'H')` returns the stale value of the previous block. Fix: reset `varValues` in `startBlock()`. |
| G-5 | MEDIUM | `plan/LineCommand.cpp:181-192` | `offset += s.offset;` instead of `offset = s.offset;` → incorrect time/feed distribution with merged speeds (offset can become > length). |
| G-6 | MEDIUM | `interp/OCodeInterpreter.cpp:74-78` | Recursion depth is only warned about (depth 101), not limited → stack overflow with deep/recursive subroutine. Fix: throw at maximum depth. |
| G-7 | MEDIUM | `interp/GCodeInterpreter.cpp:87` | Possible end-iterator dereference in `specialComment` (triggerable with comment `(probeopen)`). Fix: `it != end` before each `*it`. |
| G-8 | MEDIUM | `parse/Tokenizer.cpp:57-76,93` | `skipWhiteSpace` in the middle of `number()` turns "1 2 3" → "123"; parenthesized comments run past the end of line (against RS-274), a missing `)` is reported only at EOF. |
| G-9 | MEDIUM | `ControllerImpl.cpp:359-423` | `arc()`: radius format and full-circle logic on hard float thresholds; unstable for nearly collinear points / radius ≈ 0. Fix: catch degenerate cases, relative tolerances. |
| G-10 | MEDIUM | `plan/LinePlanner.cpp:1197-1210` | Junction velocity uses a 9D dot product including rotation/auxiliary axes (its own TODO) → incorrect corner speeds for A/B/C/U/V/W. |
| G-11 | MEDIUM | `plan/LinePlanner.cpp:81,381,388` | `1U << config.idBits` is UB for `idBits >= 32`; `idBits == 0` → `1U << -1`. Fix: `uint64_t` literals, validate range. |
| G-12 | LOW | `ControllerImpl.cpp:738-767` | Cutter radius compensation sets state (`cutterRadiusComp=true`), but is never applied to the path → silent, incorrect geometry instead of clear rejection. |
| G-13 | LOW | `plan/LinePlanner.cpp:330,449,562` | Memory leaks/`pop_back` on an empty list on error paths (`THROW` before `delete lc`). Fix: RAII/smart pointer, `empty()` guard. |
| G-14 | LOW | `interp/GCodeInterpreter.cpp:305-307` | `Codes::find(...)` without null check before `activeMotion->priority` (currently covered, fragile). |

### 3.2 Simulation, Contour & Rendering (`src/camotics/{sim,contour,render}`, 8.7k LOC)

| ID | Severity | Location | Finding |
|----|-------------|-----|--------|
| S-1 | **CRITICAL** | `sim/Sweep.cpp:33-35` | see **K-1** (material removal fails for small tools). |
| S-2 | HIGH | `sim/CutWorkpiece.cpp:34-43` | `isValid()` is **inverted** (`if (workpiece.isValid()) return false;`) — and is also dead code that is never called anywhere. Correct or remove. |
| S-3 | MEDIUM | `sim/Simulation.cpp:63-89`, `.h:50-53` | `read()` does not read `threads`; `threads`/`resolution`/`time` without in-class initializer → uninitialized after deserialization, flows into `Renderer`. |
| S-4 | MEDIUM | `render/Renderer.cpp:61,76` | `threads == 0`: `log(0) = -inf` → NaN/UB, and `while (jobs.size() < threads)` never starts a job → **infinite hang**. Fix: `threads = std::max(1u, threads);`. |
| S-5 | MEDIUM | `contour/CorrectedMC33.cpp:31-46` | `getCenter()`: `/count` without a `count>0` guard (NaN); 8-bit vertex case number misused as a 12-bit edge mask; `centerComputed` never set (cache ineffective). |
| S-6 | MEDIUM | `sim/ConicSweep.cpp:65,73`, `sim/SpheroidSweep.cpp:35,62` | Exact float comparisons (`epsilon == 0`, `2*radius != length`) → numerical instability for nearly vertical paths / almost-spherical tools. Fix: epsilon tolerances. |
| S-7 | MEDIUM | `contour/CorrectedMC33Cube.cpp:130,150-180` | Unguarded divisions and `sqrt(delta<0)` → NaN/inf flow into the MC33 disambiguation → incorrect topology. |
| S-8 | MEDIUM | `sim/ToolSweep.cpp:111-134` | `depth()` (hottest path) allocates a `vector` per voxel corner and `sort()`s it — dominates the runtime. Fix: pre-sorted/indexed moves, small buffer. |
| S-9 | LOW | `sim/OctTree.cpp` (entire file) | Dead code — `OctTree` is never instantiated anywhere (MoveLookup is `AABBTree` throughout). Remove. |
| S-10 | LOW | `sim/AABB.cpp:31-122` | Purely recursive tree construction/traversal → deep recursion with many moves; `intersects()`/`collisions()` not const. |
| S-11 | LOW | `sim/Workpiece.cpp:28-32` | Members `center`/`halfDim2` computed but never used (dead state). |
| S-12 | LOW | `render/Renderer.cpp:101` | Unsigned underflow in the progress value during transient job inconsistency. Fix: signed/clamp. |
| S-13 | HIGH | `camsim.cpp:134-135` | `bounds = getWorkpiece().getBounds()` is read **before** `update(*path)` → empty bounds with an automatic workpiece → "Empty workpiece, nothing to simulate". `camsim` is thereby unusable for pure G-code/TPL without explicit bounds. (Discovered subsequently while building the test infrastructure.) Fix: swap the order. |

> **Positive:** The thread partitioning (`tree.partition()` → disjoint `GridTree` subtrees, only read-only evaluation of the shared `CutWorkpiece`, clean join in `Renderer::render`) is correct and free of data races.

### 3.3 GUI: Qt, OpenGL View, Value System (`src/camotics/{qt,view,value,machine}`, 14.7k LOC)

| ID | Severity | Location | Finding |
|----|-------------|-----|--------|
| U-1 | **HIGH** | `qt/QtWin.cpp:1411,1242,1930` | `setModel(new QStringListModel(...))` without ownership transfer; via `resizeEvent → updateToolTables()` it **leaks a model on every window resize**. Fix: model with parent / persistent member model, delete the old one; do not rebuild in the resizeEvent. |
| U-2 | HIGH | `qt/BBCtrlAPI.cpp:43-45`, `.h:42-43` | Uninitialized members `lastMessage`, `useSystemProxy` → UB on the first `reconnect()`/upload. Fix: in the initializer list. |
| U-3 | HIGH | `qt/BBCtrlAPI.cpp:104,123` | `QByteArray::fromRawData` does not copy; the asynchronous PUT may later read a freed/overwritten `gcode` buffer (dangling). Fix: copying `QByteArray(data, length)`. |
| U-4 | HIGH | `value/VarValue.h:30`, `MemberFunctorObserver.h:30`, `qt/QtWin.h:111-114` | The value/observer system holds raw references/pointers to members without deregistration; `view` is destroyed before `valueSet` → `valueSet` references a destroyed object. Only "accidentally" safe due to destruction order. Fix: deregistration / weak_ptr. |
| U-5 | MEDIUM | `view/View.cpp:297-319`, `view/GLScene.cpp:45` | `glInit()` not idempotent — on context loss/reparenting, duplicate scene objects + leaked `GLProgram`/VBOs. |
| U-6 | MEDIUM | `view/GLProgram.cpp:41-45`, `view/VBO.cpp:27-32` | Destructors skip GL release without an active context → GPU resource leak on repeated project/model switching. |
| U-7 | MEDIUM | `qt/BBCtrlAPI.cpp:109,157-191,203` | Address unchecked via string concatenation into URLs (no escaping/TLS/auth); `line - 1` (uint32) underflow when `ln==0`; unchecked network JSON fields. |
| U-8 | MEDIUM | `qt/BBCtrlAPI.cpp:87-91,146-154` | Unbounded reconnect loop without backoff cap/abort; `.local` trim permanently alters the address. |
| U-9 | MEDIUM | `qt/QtWin.cpp` (2535 lines) | Oversized class; ~30 `update*` one-liners, 4 identical `on_action*Surface`, 6 spinbox handlers = copy-paste. Fix: data-driven tables. |
| U-10 | MEDIUM | `qt/QtWin.cpp:300,1409,1785…` | Pervasive deprecated `QString::sprintf` (removed in Qt6, not type-safe). Fix: `arg`/`number`/`asprintf`. |
| U-11 | LOW | `qt/QtWin.cpp:177,185,496,1661-1672` | `QMenu`/`QMovie` without parent + manual `delete` (fragile ownership). |
| U-12 | LOW | `view/GLProgram.cpp:119-128` | `getUniform` throws on an optimized-away uniform → can abort the entire drawing. Fix: tolerate missing uniforms. |
| U-13 | LOW | `qt/GLView.cpp:31,98` | Deprecated Qt APIs (`QGLFormat`, `event->delta()`). Fix: `QSurfaceFormat`, `angleDelta()`. |
| U-14 | LOW | `qt/QtWin.cpp:895-907` | `redraw()` throttling can swallow the final frame (implicit timer coupling). |

> **Positive:** Worker→GUI communication via `postEvent` is thread-safe; WebSocket slots run in the GUI thread. No GUI race conditions found.

### 3.4 Language Bindings & I/O (`src/{tplang,python,stl,dxf}`, `src/camotics/{project,probe,opt}`, ~6.7k LOC)

| ID | Severity | Location | Finding |
|----|-------------|-----|--------|
| L-1 | **CRITICAL** | `python/PyPtr.h:26-45` | see **K-2** (Rule-of-Three → double DECREF). |
| L-2 | HIGH | `python/PyJSON.cpp:47,63,76,80` | Several reference leaks: `PySequence_GetItem`/`PyObject_Str`/`PyObject_ASCII` return new references that are never released; scales with the amount of data. Fix: `Py_DECREF`/`PyPtr`. |
| L-3 | HIGH | `python/PySimulation.cpp:90-93,351,479` | `new Runner(...)` starts a thread in the constructor *before* `set_task()` checks "task active" → a running Runner is thrown away, never joined → thread leak. Fix: check before creation. |
| L-4 | MEDIUM | `dxf/Reader.cpp:92-111` | `addVertex`/`addControlPoint`/`addKnot` dereference `entity` without a null check → a manipulated DXF (VERTEX without POLYLINE) throws `referenceError`. Fix: null check with a clear message. |
| L-5 | MEDIUM | `stl/Reader.cpp:38-115` | Untrusted STL: `read()` without a `gcount()` check; attacker-controlled `count` without sanity check against file size; fragile ASCII/binary heuristic (`"solid "`); endianness ignored. |
| L-6 | MEDIUM | `opt/Opt.cpp:209`, `opt/AnnealState.cpp:75` | Degenerate path (0 cuts): `rand() % index.size()` (modulo 0) or `index.size()-1` (unsigned underflow) → crash/UB. Fix: `if (paths.size() < 2) return;`. |
| L-7 | MEDIUM | `project/Files.cpp:53-61` | `.camotics` file references allow absolute paths / `../` without a sandbox; loaded TPL executes arbitrary JS → a malicious project = code execution/file access outside the project folder. |
| L-8 | MEDIUM | `project/Project.cpp:109-119` | `resolution` unchecked (0/negative accepted) → division by 0 or excessive voxel allocation (DoS). Fix: `> 0` + upper bound. |
| L-9 | MEDIUM | `project/XMLHandler.cpp:34` | `i < filename.size() - 2` underflows (size_t) when `filename.size() < 2` → `substr`/`parseU8` throws. Fix: `i + 2 < size()`. |
| L-10 | MEDIUM | `project/Project.cpp:149` (cb::XML::Reader) | Possible **XXE** with untrusted `.camotics`/`.xml` — external entity/DTD resolution in the cbang XML reader not verified. Check/disable. |
| L-11 | LOW | `tplang/MatrixModule.cpp:106-112` | Negative matrix index not checked (`getInteger` returns `int`, only the upper bound is checked) → out-of-range access. |
| L-12 | LOW | `python/PyNameResolver.cpp:27-30` | `Py_INCREF` before `PyCallable_Check` → leak on throw; `PyTuple_SetItem` without NULL guard. |
| L-13 | LOW | `python/Catch.h:24-31` | `PyErr_SetString` overwrites a more precise existing Python exception. Fix: only when `!PyErr_Occurred()`. |
| L-14 | LOW | `tplang/ClipperModule.cpp:59,64,71` | Integer overflow at `coord * scale` (1e6) → faulty geometry with large JS coordinates. |
| L-15 | LOW | `project/XMLHandler.cpp:46,139` | `currentTool` is never set → `<tool>` descriptions from XML projects are never read in (functional defect). |

---

## 4. Test Coverage Analysis

### 4.1 What exists

There are **25 integration tests** (golden-file-based, cbang `testHarness`), spread across 4 suites. **Unit tests do not exist.** All tests are pure stdin→stdout/stderr/return comparisons.

| Suite | Tests | Driven binary | Tested functionality |
|-------|:-----:|--------------------|--------------------------|
| `tplTests` | 10 | `tplang` | TPL/JS: arc, cut, rapid, rotate, square(s), require, DXF loading |
| `offsetTests` | 8 | `gcodetool` | Coordinate systems & tool offsets (G10/G52/G53/G92) |
| `varRefTests` | 6 | `gcodetool` | G-code variable references (numeric/named, local/global) |
| `oCodeTests` | 1 | `gcodetool` | O-code control flow (else/if) |

### 4.2 Structural coverage — the gap

The tests drive only **2 of the 6 programs** (`gcodetool`, `tplang`). This results in the following module coverage:

| Module | LOC | Test coverage |
|-------|----:|---------------|
| `gcode/` (parse, interp, machine) | ~14.8k | 🟡 **partial** — only via `gcodetool`, ~5% of the code table (see below) |
| `tplang/` | ~1.7k | 🟡 **partial** — basic functions via `tplTests` |
| `dxf/`, `clipper/` | — | 🟡 **indirect** — only via `tplTests/DXFTest` or Clipper usage |
| **`camotics/sim/`** (simulation core) | **2.4k** | 🔴 **NONE** |
| **`camotics/contour/`** (Marching Cubes) | **6.0k** | 🔴 **NONE** |
| `camotics/render/` | 0.3k | 🔴 **NONE** |
| `camotics/opt/` (optimization) | 0.6k | 🔴 **NONE** |
| `camotics/probe/` | 0.5k | 🔴 **NONE** |
| `camotics/project/` (IO/serialization) | 1.0k | 🔴 **NONE** |
| `stl/` (STL parser) | 0.6k | 🔴 **NONE** |
| `python/` (bindings) | 1.9k | 🔴 **NONE** |
| `camotics/{qt,view,value,machine}/` (GUI) | ~14.7k | 🔴 **NONE** (acceptable for GUI) |
| `planner`, `camsim` (binaries) | — | 🔴 **NONE** |

**Estimate of the effectively tested own code base: < 20%.** The modules central to the core task "simulation", `sim/` and `contour/` (together 8.4k LOC), have **zero** automated coverage — and that is exactly where two of the most severe findings lie (K-1, S-4).

### 4.3 Functional coverage of the G-code table

The G/M-code table (`Codes.cpp`) contains **225 entries**. In all test inputs, however, only the following **12 codes** appear:

```
G0  G10  G21  G43  G52  G53  G55  G92  G92.1  G92.2  G92.3  M6
```

That is **~5%**. Entire functional classes are untested: arcs (G2/G3), drilling cycles (G81–G89), cutter compensation (G40–G42 — only partially implemented anyway, see G-12), planes (G17–G19), spindle/coolant (M3–M9), dwell, splines (G5), unit switching at runtime.

### 4.4 Real code coverage measurement

An instrumented gcov/lcov measurement was **not** performed (it requires recompiling CAMotics **and** cbang with `--coverage`). For this code base, however, the structural analysis is already meaningful: Since entire binaries and modules are not addressed by any test, a line-coverage measurement would inevitably show the 🔴 modules above as near 0%.

---

## 5. Recommendations (prioritized)

### Immediate (correctness/security)
1. Fix **K-1 / S-1** — `Sweep.cpp` unsigned truncation. Direct impact on simulation correctness.
2. Fix **K-2 / L-1** — `PyPtr` copy constructor. Memory safety of the Python bindings.
3. Fix **G-1, G-2, G-3** — dead tool guard check, `drill()` DoS, division-by-0 in the evaluator.
4. Fix **U-3, U-2** — BBCtrlAPI dangling data & uninitialized members.

### Short-term (robustness against inputs)
5. Harden input validation: **L-5** (STL), **L-4** (DXF), **L-8/L-9/L-10** (project/XML/XXE), **L-7** (path sandbox). CAMotics loads user-supplied files — these parsers are the primary attack surface.
6. **S-3/S-4** (renderer hang with `threads==0`), **U-1** (GUI resize leak).

### Test coverage (structurally most important measure)
7. Set up **golden-file tests for the simulation engine**: run `camsim` over small, deterministic G-code programs and check a mesh/volume metric (triangle count, volume, bounding-box hash) against reference values. This closes the largest gap (`sim/`, `contour/`) using the existing `testHarness` mechanism.
8. Add **`planner` tests** analogous to `gcodetool` (motion planning is untested but contains G-5/G-10/G-11).
9. Increase **G-code functional coverage**: targeted tests for arcs, drilling cycles, plane selection, dwell, and unit switching — the most common real-world G-codes.
10. **Derive regression tests from bugs:** for K-1 a test with a tiny tool; for L-6 a path with 0 cuts; for G-2 a `drill` with L=0 — so that each fix is permanently safeguarded.

### Medium-term (maintainability)
11. Remove dead code (`sim/OctTree.cpp`, `Workpiece` members, `CutWorkpiece::isValid`).
12. Migrate deprecated Qt APIs (`QString::sprintf`, `QGLFormat`, `event->delta()`) — a prerequisite for a later Qt6 port.
13. Untangle `QtWin` (data-driven observer/surface/spinbox handling instead of copy-paste).

---

*Note: The bundled third-party libraries `src/clipper`, `src/dxflib`, and `src/cairo` (~26k LOC) were not the subject of this review, as they are maintained as external dependencies.*
