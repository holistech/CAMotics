# CAMotics Tests

The tests use the cbang `testHarness` (Python). Each test runs a `command`
and compares `stdout`/`stderr`/`return` against golden files under `<test>/expect/`.
Inputs come from `<test>/data/` (via `stdin` or as an argument).

## Running

```bash
cd tests
./testHarness                       # all suites
./testHarness run simTests          # a single suite
./testHarness run simTests/BoxMillTest   # a single test
./testHarness diff simTests/BoxMillTest  # diff actual vs. expected
```

Prerequisite: The binaries (`gcodetool`, `planner`, `camsim`, `tplang`) must be built
(`scons` in the project root directory).

## Suites

| Suite | Driver | Content |
|-------|---------|--------|
| `oCodeTests` | `gcodetool` | O-code control flow |
| `offsetTests` | `gcodetool` | Coordinate systems & tool offsets |
| `varRefTests` | `gcodetool` | G-code variable references |
| `tplTests` | `tplang` | TPL/JavaScript tool path language |
| `plannerTests` | `planner` | Motion planning (JSON plan output) |
| `simTests` | `camsim` | End-to-end simulation (STL metrics; all tool shapes) |
| `pythonTests` | `camotics.so` | Python binding refcount regression |
| `guiTests` | `camotics` | GUI pipeline smoke test (headless via Xvfb) |

## Simulation tests (`simTests`)

Since the raw STL output is not byte-stable (facet ordering depends on the
thread partitioning), the sim tests compare **derived metrics**
(facet count, bounding box, volume, surface area) instead of the file itself.

- `run-sim <project.camotics>` — invokes `camsim --threads=1 --binary=false` and prints
  the metrics from `stl-metrics.py` to stdout. **`--threads=1` is mandatory**: with
  multiple threads, slightly different facets arise at the partition boundaries.
- `stl-metrics.py <file.stl>` — extracts the deterministic metrics (rounds
  against FP noise).

### Adding a new simulation test

1. Create the directory `simTests/<Name>/data/` with:
   - `project.camotics` — project with **fixed** bounds (`"automatic": false`), a defined
     tool and a fixed `resolution`. Fixed bounds are necessary as long as the
     automatic workpiece path in `camsim` is broken (see `CODE_REVIEW.md`, S-13).
   - the referenced G-code/TPL file (relative path in `files`).
2. Generate the golden:
   ```bash
   mkdir -p simTests/<Name>/expect
   ./simTests/run-sim simTests/<Name>/data/project.camotics > simTests/<Name>/expect/stdout
   : > simTests/<Name>/expect/stderr
   echo -n 0 > simTests/<Name>/expect/return
   ```
3. Before committing, run the test 3 times and check for stable metrics.

## Planner tests (`plannerTests`)

`planner --json-out` reads G-code from stdin and outputs the planned motion sequence as
JSON (deterministic, including simulated machining time on stderr). New tests are written
analogously to the `gcodetool` suites: `data/stdin` + `expect/{stdout,stderr,return}`. Some
tests override the `command` via the test's `test.json` to `--gcode` (which hits the
`GCodeMachine` output sink instead of `JSONMachine`).

## GUI tests (`guiTests`)

`run-gui <project.camotics>` starts `camotics` headless under **Xvfb** (no window on
the real display), has it load the project, compute the surface and render it via OpenGL,
and then terminates it via SIGTERM. Success = a **clean** exit (code 0): camotics
catches SIGTERM (`FEATURE_SIGNAL_HANDLER`), the poll timer in `QtApp::run` ends the
Qt event loop, and the app shuts down normally (save state, release GL resources).
The test thereby also locks in the clean shutdown. Requires `xvfb-run`.

Because camotics now shuts down cleanly, the gcov atexit handlers run — the GUI test
therefore provides **real line coverage** for the GUI modules (measured, among others, `view` ~59 %,
`value` ~72 %, `qt` ~28 %). Cf. the coverage guide in `CLAUDE.md`.

## Code coverage

See `CLAUDE.md` → "Code coverage". In short: `scons coverage=1`, run the tests,
evaluate `gcov --json-format --stdout build/<path>.gcda`, then rebuild normally and
delete `build/**/*.gcda`,`*.gcno`.
