# P4 — Language Bindings & IO + Security Hardening

**Goal:** Fix memory/reference errors in the Python bindings (including the critical K-2)
and harden the parsers for untrusted inputs (STL, DXF, `.camotics`).

**Status:** ⬜ open · **Findings:** L-1…L-15 (details see `CODE_REVIEW.md` §3.4)

---

## Fixes (prioritized)

| ID | Severity | File:Line | Fix Core |
|----|-------------|-------------|----------|
| L-1 (**K-2**) | **CRITICAL** | `python/PyPtr.h:26-45` | Add a copy constructor with `Py_INCREF` (consider a move constructor). |
| L-2 | HIGH | `python/PyJSON.cpp:47,63,76,80` | Release new references (`PySequence_GetItem`, `PyObject_Str/ASCII`); use `PyPtr`; check for errors. |
| L-3 | HIGH | `python/PySimulation.cpp:90-93,351,479` | Perform the "task active" check BEFORE `new Runner(...)`; otherwise join/release the Runner. |
| L-4 | MEDIUM | `dxf/Reader.cpp:92-111` | Null check for `entity` in `addVertex/addControlPoint/addKnot` with a clear message. |
| L-5 | MEDIUM | `stl/Reader.cpp:38-115` | Check `gcount()` after each `read`; validate `count` against the remaining file size; more robust ASCII/binary heuristic. |
| L-6 | MEDIUM | `opt/Opt.cpp:209`, `opt/AnnealState.cpp:75` | `if (paths.size() < 2) return;`; `if (index.empty()) return 0;`. |
| L-7 | MEDIUM | `project/Files.cpp:53-61` | Validate paths against the project directory (reject or confirm traversal/absolute); document the TPL trust boundary. |
| L-8 | MEDIUM | `project/Project.cpp:109-119` | Validate `resolution > 0` plus a sensible upper bound. |
| L-9 | MEDIUM | `project/XMLHandler.cpp:34` | `i + 2 < filename.size()` without size_t subtraction. |
| L-10 | MEDIUM | `project/Project.cpp:149` | Check XXE: disable/verify external entity/DTD resolution in the cbang XML reader. |
| L-11 | LOW | `tplang/MatrixModule.cpp:106-112` | `if (matrix < 0 \|\| AXES_COUNT <= matrix) THROW(...)`. |
| L-12 | LOW | `python/PyNameResolver.cpp:27-30` | `PyCallable_Check` before `Py_INCREF`; `PyTuple_SetItem` NULL protection. |
| L-13 | LOW | `python/Catch.h:24-31` | `PyErr_SetString` only when `!PyErr_Occurred()`. |
| L-14 | LOW | `tplang/ClipperModule.cpp:59,64,71` | Validate coordinates/product against the integer range. |
| L-15 | LOW | `project/XMLHandler.cpp:46,139` | Set `currentTool` in `startElement("tool")`. |

## Tests (interlinked)

- **L-5 (STL):** Malformed STL corpus under `tests/stlTests/` — truncated file,
  oversized `count`, `"solid\n"` ASCII, binary with a random `"solid "` header → clean
  error instead of crash/hang. Driver: small test program or `camsim`/`tplang` with an
  STL load (TPL cannot load STL — a dedicated mini driver may be needed).
- **L-4 (DXF):** Malformed DXF (VERTEX without POLYLINE) via the `tplang` DXF module → clear error.
- **L-6 (opt):** G-code path with 0 cuts through `planner`/`camsim` with optimization → no crash.
- **L-8 (resolution):** `camsim --resolution 0` or a project with `resolution=0` → rejection.
- **L-9 (decodeFilename):** `.camotics` with file name `"%"` → no throw/underflow.
- **L-1/L-2/L-3 (Python):** If a Python testing option exists (module `camotics.so`),
  a `pytest`/script test that runs repeated `toJSON` conversion and a duplicate task
  (refcount stability, no crash). Otherwise document as manually verified.
- **L-7 (path sandbox):** `.camotics` with a `../` reference → rejection/confirmation.

## Acceptance Criteria

- [ ] K-2 plus all HIGH Python findings fixed.
- [ ] STL and DXF parsers survive malformed input without crash/hang (tests green).
- [ ] Path traversal and `resolution<=0` are rejected.
- [ ] XXE status clarified and documented.
- [ ] Build green; all tests green.

## Risks

- L-7 (path sandbox) may break legitimate projects with absolute paths → choose the
  behavior deliberately (hard rejection vs. warning) and document it in the status.
- Python tests may require a test harness extension; if too costly, secure the refcount
  fixes via code review + manual smoke test and note this in the status.
