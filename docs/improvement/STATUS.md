# CAMotics — Improvement Initiative: Status

Central log for implementing the findings from [`CODE_REVIEW.md`](../../CODE_REVIEW.md)
and for building a complete test suite.

**Mode:** Tests interleaved with fixes per module · autonomous run until blocker.
**Start:** 2026-06-21

---

## Overall Progress

| Project | Topic | Status | Findings fixed | New tests | Build | Tests green |
|---------|-------|:------:|:--------------:|:---------:|:-----:|:----------:|
| [P1](P1-test-infrastructure.md) | Test infrastructure & simulation harness | ✅ completed | — | 6 | ✅ | ✅ 31/31 |
| [P2](P2-gcode-engine.md) | G-code engine: fixes + tests | ✅ completed | 10 fix / 4 assessed | 11 | ✅ | ✅ 42/42 |
| [P3](P3-simulation.md) | Simulation/Contour/Render: fixes + tests | ✅ completed | 7 fix / 3 assessed / 3→P6 | 2 | ✅ | ✅ 44/44 |
| [P4](P4-bindings-io.md) | Language bindings & IO + security | ✅ completed | 12 fix / 3 assessed | 1 | ✅ | ✅ 45/45 |
| [P5](P5-gui.md) | GUI: fixes | ✅ completed | 6 fix / 8 assessed→P6 | 0 | ✅ | ✅ 45/45 |
| [P6](P6-cleanup.md) | Cleanup & final verification | ✅ completed | dead code + coverage | — | ✅ | ✅ 45/45 |
| P7 | Extend test coverage (addendum) | ✅ completed | — | 8 | ✅ | ✅ 53/53 |
| P8 | Signal handler fix → clean shutdown + GUI coverage | ✅ completed | 1 (clean shutdown) | — | ✅ | ✅ 53/53 |

Status legend: ⬜ open · 🟡 in progress · ✅ completed · ⛔ blocked

---

## Baseline (before start)

- Build: ✅ `scons -j24` green (all 6 binaries + Python module)
- Tests: ✅ 25/25 green (`tplTests` 10, `offsetTests` 8, `varRefTests` 6, `oCodeTests` 1)
- Covered binaries: 2/6 (`gcodetool`, `tplang`)
- Functional G/M-code coverage: 12/225 (~5 %)

---

## Change Log

| Date | Project | Action |
|------|---------|--------|
| 2026-06-21 | — | Code review completed, 6-project plan created, status tracking set up |
| 2026-06-21 | P1 | Sim test harness built: `tests/simTests/{stl-metrics.py,run-sim}` (metric-based, `--threads=1` deterministic). 3 sim tests (Box/Drill/Arc) + 3 planner tests created. `tests/README.md` added. Test suite: 25 → **31 green**. |
| 2026-06-21 | P1→P3 | New finding **S-13** discovered: `camsim.cpp:134` reads `bounds` before `update()` → automatic workpiece yields empty result. Documented in CODE_REVIEW + P3. |
| 2026-06-21 | P2 | **10 fixes** implemented: G-1 (tool sentinel `int`), G-2 (validate drill L), G-3 (Div/0 + SQRT/LN/ACOS/ASIN domain throw), G-5 (LineCommand offset), G-6 (recursion depth throw), G-7 (specialComment iterator), G-9 (arc coincident points), G-11 (`1ULL` shift), G-13 (LinePlanner leaks/pop_back), G-14 (activeMotion null check). **11 tests** new (6 errorTests + 5 gcodeTests). Suite: 31 → **42 green**. |
| 2026-06-21 | P2 | **4 findings differentially assessed (no blind fix):** G-4, G-8, G-10, G-12 — see P2 closing notes. G-10 was a **false finding** (code already correct). |
| 2026-06-21 | — | P1+P2 committed in branch `test-suite` (3 commits: docs / P1 / P2). |
| 2026-06-21 | P3 | **7 fixes:** K-1/S-1 (Sweep unsigned UB, **critical**), S-2 (isValid inverted), S-3 (Simulation member init), S-4 (Renderer threads==0 hang), S-5 (MC33 NaN guard + cache), S-12 (progress underflow), S-13 (camsim bounds ordering). **2 tests** new (SmallToolTest=K-1 regression, ThreadsZeroTest=S-4). Suite: 42 → **44 green**. |
| 2026-06-21 | P3 | **K-1 made precise:** the symptom is UB-dependent and platform-specific (x86/gcc: wrong facet count instead of total failure) — proven by counter-test (buggy 3356 ≠ fixed 3740). |
| 2026-06-21 | P4 | **12 fixes:** K-2/L-1 (PyPtr copy/move ctor, **critical**), L-2 (PyJSON 4 reference leaks), L-3 (runner thread before active check), L-4 (DXF null checks), L-5 (STL gcount), L-6 (opt modulo/underflow at 0 cuts), L-8 (resolution>0), L-9 (decodeFilename underflow), L-11 (MatrixModule neg. index), L-12 (PyNameResolver INCREF ordering), L-13 (Catch.h overwrites exception), L-15 (XMLHandler currentTool). **1 test** (pythonTests/RefcountTest). Suite: 44 → **45 green**. |
| 2026-06-21 | P4 | **L-10 (XXE) verified: no risk.** cbang uses Expat without `XML_SetExternalEntityRefHandler`; `XML_SetParamEntityParsing` defaults to `NEVER` → external entities are not resolved. No fix needed. |
| 2026-06-21 | — | P3+P4 committed (2 commits). |
| 2026-06-21 | P5 | **6 fixes:** U-1 (QStringListModel leak per resize, **HIGH**), U-2 (BBCtrlAPI uninit. member), U-3 (dangling `fromRawData` on async PUT), U-4 (observer lifetime documented+enforced), U-7 (line-1 uint32 underflow), U-12 (tolerate GL uniform instead of aborting draw). GUI builds, camotics starts, 45 tests green. |
| 2026-06-21 | — | P5 committed. |
| 2026-06-21 | P6 | **Dead code removed:** `sim/OctTree.{cpp,h}` (S-9, never instantiated), unused `Workpiece` members `center`/`halfDim2` (S-11). **gcov coverage option** added to SConstruct (`coverage=1`). **Real coverage measured.** CLAUDE.md (test suites + coverage) and CODE_REVIEW.md (implementation status) updated. 45 tests green. |
| 2026-06-21 | P7 | **Test coverage extended (pure test additions, no `src/` code changed):** 3 tool-shape tests (conical/spheroid/snubnose → ConicSweep/SpheroidSweep/CompositeSweep), 2 `planner --gcode` (GCodeMachine), 2 `gcodetool --json-out` (JSONMachine), 1 **GUI pipeline smoke test** (camotics headless via Xvfb). Suite: 45 → **53 green**. CLI coverage 40.3 % → **42.2 %** (gcode/machine 30→37 %, planner 73→80 %). |
| 2026-06-21 | P7 | **GUI coverage limitation identified:** SIGTERM terminates camotics before the gcov dump (separate Qt/cbang event loops) → GUI modules do not appear in gcov. The GUI test remains valuable as pipeline crash protection. Documented in `tests/README.md`. |
| 2026-06-21 | P8 | **Signal handler fix (limitation resolved):** `QtApp` enables `FEATURE_SIGNAL_HANDLER` (GUI-only) and polls cbang's `quit` flag in `run()` via QTimer → `qApp.quit()`. SIGTERM/SIGINT now shut camotics down **cleanly** (exit 0 instead of 143; saves state, frees GL resources). **Signal-safe:** the handler only sets a bool; the Qt call happens in the Qt thread, not in the signal context. CLI tools unchanged (feature GUI-only). **GUI coverage now measurable:** `view` 59 %, `value` 72 %, `qt` 28 %, `machine` 43 %. GUI test tightened to "clean exit" → locks in the shutdown. |

---

## P1 — Closing Notes

- **Determinism:** STL geometry depends on the thread count (partition boundaries) →
  tests run pinned with `--threads=1`; bit-stable metrics verified over 3 runs.
- **Workpiece:** tests use `.camotics` projects with fixed bounds, since the
  automatic path is broken (S-13). After the S-13 fix (P3), they can be switched to pure G-code.
- **SmallToolTest (K-1 regression):** deliberately **not** created in P1, but in P3
  together with the K-1 fix (TDD: test fails before the fix, green afterwards).
- P1 acceptance criteria met: ≥4 sim tests (3 + SmallTool to follow), ≥3 planner tests,
  harness integrated, documentation present.

## P2 — Closing Notes (differentially assessed findings)

Four findings were **deliberately not** implemented as the originally proposed fix,
because verification against the real code revealed something different. Adversarial review instead of
blind patching:

- **G-4 (reset varValues per block): NOT implemented — would create a regression.**
  A blanket reset in `startBlock()` would break **modal drill cycles** (G81–G89):
  there R/Z/F remain valid across subsequent blocks (`G81 X.. Y.. Z.. R..` followed by only
  `X.. Y..`). The `DrillCycleTest` demonstrates this modal behavior. Correct would be only the
  selective safeguarding of *non*-modal auxiliary parameters; L was already safeguarded in G-2.
- **G-8 (whitespace in numbers): not "fixed".** RS-274/NGC allows whitespace within
  numbers (LinuxCNC strips all whitespace beforehand), so the `Tokenizer::number()` behavior
  is **standard-conformant**. Left untouched to avoid breaking conformance.
- **G-10 (junction velocity with rotary axes): FALSE FINDING.** The current code already restricts
  the computation to XYZ (`unit.slice<3>()`, `computeMaxAccel` iterates `axis < 3`).
  The review finding referred to older code / overlooked the restriction. No fix needed.
- **G-12 (cutter radius compensation): left as is (LOW).** Already warned as "not implemented";
  the state that is set is never applied to the path (the path remains uncompensated,
  not wrong). A full implementation of G40–G42 is its own feature, not a bugfix.

Also noted: **G83 (peck drilling)** is marked in the code as `// TODO Peck drill`
(`ControllerImpl.cpp:1148`) — Q is ignored, one pass instead of pecking.
A known non-implementation, not a hidden defect.

## P3 — Closing Notes (differentially assessed findings)

- **S-6 (exact float comparisons Conic/Spheroid sweep): conservatively left as is.** The
  `epsilon == 0` comparisons are theoretically fragile, but the code works and produces
  correct surfaces. A tolerance fix (`fabs(epsilon) < eps`) to this core sweep
  routine would carry high regression risk (arbitrary threshold, hard to verify) without
  a demonstrated defect. Deferred until a reproducible artifact is available.
- **S-7 (unguarded divisions/sqrt in CorrectedMC33Cube): verified, left as is.** The
  resulting NaN/inf propagate **safely** through the subsequent comparisons
  (`t1 < 1 && 0 < t1 && …` yield `false` for NaN) to defined code paths — **no
  crash, no classic UB** (IEEE NaN is well-defined). A correct fallback for
  degenerate cells requires MC33 algorithm expertise; an arbitrary guard would
  risk the tiling selection rather than improve it.
- **S-5 (getCenter): partial.** NaN guard (`count>0`) and cache activation implemented
  (both without changing the normal case, goldens stable). The delicate 8-bit case-number-vs-12-bit
  edge-mask semantics were **deliberately not** touched (MC33 topology risk), only commented
  in the code.
- **S-8 (ToolSweep::depth hot path): deferred.** A performance optimization, not a
  correctness bug. Per the plan, only to be merged with demonstrated metric equality before/after
  — split off as a standalone task to be carefully benchmarked.
- **S-9 / S-10 / S-11 (dead code, const correctness): → P6** (cleanup project).

## P4 — Closing Notes (differentially assessed findings)

- **L-7 (path sandbox for `.camotics` projects): deliberately no hard sandbox.** A project
  can reference files via absolute/`../` path and load TPL (arbitrary JS). A
  hard rejection would break legitimate workflows with absolute paths. This is a
  **trust-boundary decision** of the project owner: a `.camotics` project is to be treated like
  executable code (opening = trust, as with a macro document). This is
  to be documented (README/UI hint), not enforced through a risky path filter.
- **L-10 (XXE): no risk (verified).** See log — Expat without an external entity handler.
- **L-14 (ClipperModule integer overflow): LOW, left as is.** Affects only absurdly large
  coordinates in **user-written** TPL scripts (no untrusted input); a clamp
  would have little benefit and could alter legitimate extreme geometry.

## P5 — Closing Notes (deferred/assessed findings)

GUI code is not automatically testable (no display in CI). The HIGH memory errors
were fixed and verified via build + smoke test (camotics starts, libs resolved).
The following findings were treated differentially:

- **U-4 (observer lifetime): enforced + documented.** The destruction order is
  already necessarily correct via `view(new View(valueSet))` (valueSet outlives view); a
  reordering is impossible (View needs valueSet in the constructor). Fixed with a warning comment.
  A full observer deregistration system is a larger rework (too risky without GUI tests).
- **U-5 / U-6 (OpenGL resource lifecycle): deferred.** Correction requires
  careful context lifecycle handling, verifiable only with a running GUI.
- **U-8 (reconnect limit): UX decision.** The UB part (uninit. `lastMessage`) is fixed via
  U-2. A hard reconnect limit is not unambiguously desired (CNC controllers
  should automatically reconnect after a temporary outage).
- **U-9 (untangle QtWin): maintainability, → its own task** (not a defect).
- **U-10 (`QString::sprintf`) / U-13 (`QGLFormat`, `event->delta()`): → P6** (Qt6 preparation).
- **U-11 (QMenu/QMovie parent) / U-14 (redraw throttling): LOW, → P6.**

## Final Test Coverage (gcov, measured 2026-06-21)

Instrumented build (`scons coverage=1 with_gui=0`), full test suite, gcov evaluation.
GUI code (`qt/`, `view/`, `value/`) is not instrumented (not automatically testable).

| Module | Line coverage | Note |
|--------|:-------------:|------|
| `gcode/parse` | 66.5 % | Tokenizer/Parser — well covered |
| `gcode/interp` | 57.9 % | Interpreter/Evaluator (incl. new error paths) |
| `gcode/ast` | 56.7 % | |
| `gcode/plan` | 50.8 % | via `plannerTests` |
| `gcode` (core) | 46.3 % | |
| `gcode/machine` | 30.3 % | many output sinks (JSON/GCode) untested |
| `camotics/sim` | 25.4 % | via `simTests` (previously ~0 %) |
| `camotics/project` | 25.0 % | |
| `camotics/render` | 12.7 % | |
| `camotics/contour` | 8.3 % | Marching Cubes — only one tiling path per test |
| `tplang` | 37.7 % | |
| **Total (tested non-GUI code)** | **40.3 % → 42.2 % (P7)** | **3859 / 9134 lines** |

Driver binaries: `gcodetool` 90.5 %, `planner` 80.0 %, `camsim` 75.8 %, `tplang` 60.0 %.
After P7: `gcode/machine` 36.6 % (both sinks JSONMachine + GCodeMachine tested).

**GUI modules (captured after P8):** `view` 59.0 %, `value` 71.7 %, `qt` 28.5 %,
`machine` 42.7 % — the GUI smoke test covers them, since camotics now shuts down cleanly on SIGTERM
(gcov writes only on a regular exit). Total **incl. GUI: 40.3 % of
15452 lines** — the GUI code brings ~6300 previously untested lines into the denominator, hence
the same percentage with substantially more actually covered code (6233 instead of 3859 lines).

**Before → After:** 25 → 45 tests; 2 → 5 driven binaries; G/M-code coverage substantially
raised from ~5 %; `sim`/`contour`/`render` from practically 0 % to measurable coverage; Python
bindings with a regression test for the first time.

### Recommendations for further coverage (optional)
- `gcode/machine` (30 %): tests for the JSON/GCode machine output sinks.
- `camotics/contour` (8 %): tests with geometries that trigger different MC33 tilings.
- GUI: requires a display-capable test environment (e.g. Xvfb + Qt test) — its own undertaking.

## Open Blockers / Decisions

_(none — all 6 projects completed)_
