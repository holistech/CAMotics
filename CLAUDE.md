# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

CAMotics is Open-Source software for simulating 3-axis NC (CNC) machining. It parses
G-code (and an optional JavaScript-based tool path language, TPL), plans/interprets the
tool path, simulates material removal against a workpiece, and renders the cut surface.
It builds a Qt GUI application plus several command-line tools. License: GPL v2+.

## Build

The build system is **SCons** (not CMake/Make — the top-level `Makefile` just shells out).
It depends on **C! (cbang)**, a sibling library that must be built first.

In this checkout cbang already lives (built) at `../cbang` (`/home/soeren/src/cbang`) and
`CBANG_HOME` is set to it. To rebuild it after changes:

```bash
# Build cbang (requires V8/libnode installed first); CBANG_HOME must point at it
scons -C ../cbang
export CBANG_HOME=$(realpath ../cbang)   # if unset, SConstruct defaults to ./cbang

# Build CAMotics
scons                                # builds all default targets
scons -j$(nproc)                     # parallel build
scons strict=0                       # don't treat build warnings as errors
scons package                        # build the .deb / platform package
scons -c                             # clean (removes build/, config.log, dist.txt, package.txt)
```

Useful SCons variables (pass as `name=value` on the command line):
- `with_gui=0` — build without Qt GUI (CLI tools only; `camotics` is not built).
- `with_tpl=0` — disable the TPL JavaScript engine (drops the V8/Chakra requirement).
- `cxxstd=c++17` — C++ standard (`c++14`/`c++17`/`c++20`).
- `install_prefix=/usr/local/` — install location for `scons install`.

System prerequisites on Debian/Ubuntu:
```bash
sudo apt-get install scons build-essential libqt5websockets5-dev libqt5opengl5-dev \
  qttools5-dev-tools libnode-dev libglu1-mesa-dev pkgconf git
```

Object files are compiled into `build/` via a SCons `VariantDir` (source stays in `src/`).
Do not edit anything under `build/` — it is generated.

## Executables produced

| Binary      | Source            | Purpose |
|-------------|-------------------|---------|
| `camotics`  | `src/camotics.cpp`| Qt GUI application (only built with `with_gui=1`). |
| `gcodetool` | `src/gcodetool.cpp`| CLI G-code parser/transformer; used as the test driver. |
| `planner`   | `src/planner.cpp` | CLI motion planner (outputs planned moves). |
| `camsim`    | `src/camsim.cpp`  | CLI simulation runner. |
| `tplang`    | `src/tplang.cpp`  | CLI TPL (JavaScript) interpreter (only with `with_tpl=1`). |
| `camotics.so` | `src/python.cpp`| Python module (built when Python is detected). |

The CLI tools (`gcodetool`, `planner`, `tplang`) derive from
`CAMotics::CommandLineApp`; `camsim` and `camotics` derive from `CAMotics::Application`.
All use cbang's `doApplication<>()` entry-point pattern.

## Tests

Tests use cbang's **`testHarness`** Python runner (`tests/testHarness`). Each test is a
directory with `data/stdin` (input) and an `expect/` folder containing the golden
`stdout`, `stderr`, and `return` (exit code). A suite's `test.json` defines the `command`
to run (e.g. `gcodetool` for the G-code suites).

```bash
cd tests
./testHarness                 # run all tests (requires the binaries already built)
./testHarness run offsetTests/CSTest   # run one specific test
./testHarness diff <target>   # diff actual vs. expected output
./testHarness init <target>   # create a new test
./testHarness reset <target>  # delete a test's expect/ files (regenerate goldens)
```

Test suites (driver in parentheses):
- `oCodeTests` (`gcodetool`) — O-code control flow
- `offsetTests` (`gcodetool`) — coordinate-system & tool offsets
- `varRefTests` (`gcodetool`) — G-code variable references
- `gcodeTests` (`gcodetool`) — units/plane/drill-cycle/incremental coverage
- `errorTests` (`gcodetool`) — error-path regressions (divide-by-zero, bad drill L, recursion …)
- `tplTests` (`tplang`) — TPL/JavaScript
- `plannerTests` (`planner`) — motion planning (JSON plan output)
- `simTests` (`camsim`) — end-to-end simulation via stable STL metrics (see `tests/README.md`)
- `pythonTests` (`camotics.so`) — Python-binding refcount regression

Binaries must be built (`scons`) before running tests, since the harness invokes them by
relative path. `simTests` and `pythonTests` use small wrapper scripts (`run-sim`, `run-py`);
see `tests/README.md` for how to add simulation tests. **Always `--threads=1` for `camsim`
tests** — multi-threaded marching-cubes output is not bit-stable.

### Code coverage

```bash
scons coverage=1 with_gui=0 gcodetool planner camsim tplang   # instrumented build
cd tests && ./testHarness                                     # generate *.gcda
gcov --json-format --stdout build/gcode/interp/Evaluator.gcda # evaluate per file
```

Disable instrumentation again with a normal `scons` rebuild (and delete `build/**/*.gcda`,
`*.gcno`). Coverage instruments only CAMotics objects, not the cbang dependency.

## Architecture

The codebase is layered: G-code/TPL front-end → planning/interpretation → simulation →
rendering → GUI. Libraries are built separately and linked with `--start-group/--end-group`
to resolve circular dependencies.

### Core libraries (`src/`)
- **`gcode/`** → `libGCode`. The G-code engine: lexing/parsing (`parse/`), AST (`ast/`),
  interpretation (`interp/`), machine state (`machine/`), and motion planning
  (`plan/`, with Buildbotics controller support in `plan/bbctrl/`). Key types:
  `Codes`, `Controller`/`ControllerImpl`, `ToolPath`, `ToolTable`, `Move`, `Axes`.
- **`stl/`** → `libSTL`, **`dxf/`** → `libDXF`: mesh/CAD file I/O. `dxflib/` and
  `cairo/` are bundled third-party fallbacks built only if the system libs aren't found.
- **`clipper/`**: bundled polygon-clipping library (built when TPL is enabled).

### Application core (`src/camotics/`) → `libCAMotics`
- **`sim/`**: the simulation engine — voxel/octree material removal. `CutSim`,
  `Simulation`, `Workpiece`/`CutWorkpiece`, `OctTree`, `AABBTree`, and tool `Sweep`
  shapes (`ConicSweep`, `SpheroidSweep`, `CompositeSweep`). Work is split into
  `Task`s run by `ConcurrentTaskManager` (see `Task.h`, `TaskObserver.h`).
- **`contour/`**: surface extraction from the simulated volume (Marching Cubes variants,
  e.g. `CorrectedMC33`).
- **`render/`**: turns surfaces into renderable geometry (`Renderer`, `RenderJob`).
- **`project/`**: the `.camotics` project model (`Project`, `Files`, `Tool` settings).
- **`probe/`**, **`opt/`**: probing grids and tool-path optimization (simulated annealing).

### GUI (`src/camotics/`, built only with `with_gui=1`) → `libCAMoticsGUI`
- **`qt/`**: Qt widgets, dialogs, and the `BBCtrlAPI` WebSocket bridge to Buildbotics
  controllers. `.ui` files live in `qt/` and are compiled by `uic` into `build/ui_*.h`.
- **`view/`**: OpenGL scene/view objects. **`value/`**: an observer/value-binding system
  (`Value`, `ValueSet`, `Observer`) linking model state to the UI. **`machine/`**:
  3D machine-model visualization.

### TPL (`src/tplang/`)
A JavaScript-scriptable tool-path language running on V8 (or Chakra). `Interpreter`
exposes modules (`GCodeModule`, `ClipperModule`, `DXFModule`, `MatrixModule`) to scripts.
Standard-library TPL scripts ship in `tpl_lib/`.

### Resources & i18n
GUI resources (`src/resources/`) are compiled into `build/resources.cpp` by cbang's
`Resources` tool. Qt `.qrc` resources and `languages/*.ts` translations are compiled
into the binary at build time.

## Conventions

- C++17 by default; the `CBANG_*` macros and cbang utilities are used throughout
  (`USING_CBANG` is defined). Prefer cbang's `SmartPointer`, `Exception`, etc., matching
  surrounding code.
- The default build is strict (warnings → errors). Use `scons strict=0` only to work
  around third-party warnings, not to silence warnings in this project's own code.
- Version is single-sourced from `package.json` (`version` field) into the build.
