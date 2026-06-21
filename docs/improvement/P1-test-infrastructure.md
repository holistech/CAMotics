# P1 — Test Infrastructure & Simulation Harness

**Goal:** Establish a foundation for testing the currently untested binaries (`camsim`, `planner`)
automatically and deterministically. Prerequisite for verifying the
simulation fixes in P3.

**Status:** ⬜ open

---

## Background

- `tests/testHarness` (cbang, Python) runs a `command` per test and compares
  `stdout`/`stderr`/`return` against golden files in `expect/`. Input via `data/stdin`.
- `camsim <input.gcode|tpl|camotics> <output.stl>` produces an STL file. Options:
  `--binary 0` (ASCII STL), `--threads N`, `--resolution low|medium|high|<decimal>`,
  `--time`, `--reduce`, `--render-mode`.
- Direct STL byte diffing is **not** robust: thread partitioning can change the
  facet ordering; floating point varies minimally across platforms.
  → Instead, compare **stable metrics**.

## Implementation Steps

1. **STL metric extractor** (`tests/simTests/stl-metrics.py`):
   reads an (ASCII or binary) STL and outputs deterministic metrics to stdout:
   - Facet count
   - Bounding box (rounded to e.g. 3 decimal places)
   - Closed volume (signed-volume sum of the triangles, rounded)
   - Surface area (rounded)
   Rounding makes the comparison robust against FP noise.

2. **Test wrapper** (`tests/simTests/run-sim.sh` or similar): invokes
   `camsim --threads 1 --binary 0 --resolution <fixed> <input> <tmp.stl>`, pipes
   `tmp.stl` through `stl-metrics.py`, writes metrics to stdout.
   `--threads 1` for determinism.

3. **Suite `tests/simTests/test.json`**: `command` = wrapper. Per test one directory
   with `data/` (G-code input) and `expect/{stdout,stderr,return}`.

4. **Initial simulation tests** (golden via `testHarness init`):
   - `BoxMillTest` — simple rectangular milling path, checks basic material removal.
   - `DrillTest` — drilling cycle, checks cylindrical removal.
   - `ArcMillTest` — arc movement (G2/G3), checks curved surface.
   - `SmallToolTest` — tool with radius < 1/16 unit → **regression test for K-1**
     (this test must fail / show an empty mesh BEFORE the fix, and be correct AFTER the fix).

5. **`planner` harness** analogous to `gcodetool` (`tests/plannerTests/`): `planner` reads
   G-code from stdin and outputs planned moves → directly golden-comparable like the
   existing `gcodetool` suites. Initial tests: simple linear movement, feed/
   rapid transition, arc.

6. **Determinism check:** Run each new test 3× and make sure that the
   metrics are stable before the golden files are committed.

## Acceptance Criteria

- [ ] `stl-metrics.py` produces reproducible metrics.
- [ ] `tests/simTests` with ≥ 4 tests, all green (except `SmallToolTest`, which until P3 is
      marked as a known failure or parked via `disable`).
- [ ] `tests/plannerTests` with ≥ 3 tests, all green.
- [ ] `./testHarness` from `tests/` also runs the new suites.
- [ ] Documentation in `tests/README` or similar on how to add sim tests.

## Notes

- If `testHarness` does not directly support positional arguments / file I/O, the
  wrapper-script approach (step 2) is the most robust path — `command` fully encapsulates the
  camsim invocation.
- Deliberately choose a coarse resolution (few voxels) → small STL, fast tests.
