# P6 — Cleanup & Final Verification

**Goal:** Remove dead code, finalize deprecated APIs, update the documentation
and back the achieved test coverage with a real gcov/lcov measurement.

**Status:** ⬜ open

---

## Tasks

1. **Remove dead code** (unless already done in P3):
   - `sim/OctTree.cpp` (S-9) — unused, if confirmed.
   - `sim/Workpiece.cpp` unused members (S-11).
   - `sim/CutWorkpiece::isValid` (S-2), if classified as dead code.
   - Further corpses discovered during the fixes.

2. **Finalize deprecated Qt APIs** (remainder from P5, Qt6 preparation):
   Check `QString::sprintf`, `QGLFormat`, `event->delta()` comprehensively.

3. **Update documentation:**
   - `CLAUDE.md`: Note about the new test suites (`simTests`, `plannerTests`, `stlTests`)
     and how to run/extend them.
   - `CODE_REVIEW.md`: Mark findings as fixed (cross-reference to the projects).
   - `tests/README` or similar: Instructions for adding sim/parser tests.

4. **Final coverage measurement (gcov/lcov):**
   - Build CAMotics **and** cbang with `--coverage` (`-fprofile-arcs -ftest-coverage`).
     Make it switchable in SConstruct via a build variable (e.g. `coverage=1`).
   - Run the complete test suite, generate an `lcov`/`genhtml` report.
   - Record line/function coverage per module in the status (before/after).

5. **Overall regression run:** `scons -j$(nproc)` + complete `testHarness` suite green.

## Acceptance Criteria

- [ ] No more known dead code (or deliberately left in and documented).
- [ ] Docs (CLAUDE.md, CODE_REVIEW.md, test README) up to date.
- [ ] gcov/lcov report generated; coverage numbers per module in the status.
- [ ] Complete build + all tests green.
- [ ] STATUS.md final: all projects ✅, finding tally complete.

## Risks

- The coverage build requires an instrumented cbang → possibly a separate build tree; if too
  costly, instrument at least CAMotics' own objects and document the limitation.
