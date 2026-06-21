# P2 — G-code Engine: Fixes + Tests

**Goal:** Fix correctness and robustness defects in `src/gcode` and significantly increase the
functional coverage of the G-code engine (today ~5 % of the code table).

**Status:** ⬜ open · **Findings:** G-1…G-14 (details see `CODE_REVIEW.md` §3.1)

---

## Fixes (prioritized)

| ID | Severity | File:Line | Fix Core |
|----|-------------|-------------|----------|
| G-1 | HIGH | `ControllerImpl.h:161` | `getCurrentTool()` → `int`, sentinel `-1`; adjust callers `:740,1084`. |
| G-2 | HIGH | `ControllerImpl.cpp:503,515` | Read `drill()` L as `int`, validate `>= 1`, otherwise throw. |
| G-3 | HIGH | `interp/Evaluator.cpp:57-61,66-111` | Division/modulo by 0 → throw; check `SQRT/LN/pow` domain. |
| G-4 | MEDIUM | `ControllerImpl.cpp:71,981` | Reset `varValues` in `startBlock()`; guard auxiliary-parameter reads against the `vars` mask. |
| G-5 | MEDIUM | `plan/LineCommand.cpp:181-192` | `offset += s.offset` → `offset = s.offset`. |
| G-6 | MEDIUM | `interp/OCodeInterpreter.cpp:74-78` | Throw instead of merely warning when exceeding the maximum depth. |
| G-7 | MEDIUM | `interp/GCodeInterpreter.cpp:87` | `it != end` before every `*it` in `specialComment`. |
| G-8 | MEDIUM | `parse/Tokenizer.cpp:57-76,93` | Limit parenthesis comment to the end of line; prevent/document whitespace swallowing in `number()`. |
| G-9 | MEDIUM | `ControllerImpl.cpp:359-423` | `arc()`: catch degenerate cases (radius/distance ≈ 0), relative tolerances. |
| G-10 | MEDIUM | `plan/LinePlanner.cpp:1197-1210` | Restrict junction velocity to translational axes. |
| G-11 | MEDIUM | `plan/LinePlanner.cpp:81,381,388` | `uint64_t` shift literals; validate `idBits` range. |
| G-12 | LOW | `ControllerImpl.cpp:738-767` | Cutter radius comp: either reject clearly (throw/warning + do not set state) instead of silently producing a wrong path. |
| G-13 | LOW | `plan/LinePlanner.cpp:330,449,562` | RAII/smart pointer for `lc`; guard `pop_back` loops against `empty()`. |
| G-14 | LOW | `interp/GCodeInterpreter.cpp:305-307` | Null check before `activeMotion->priority`. |

## Tests (interlocked)

**Regression tests** (one targeted `gcodetool` test per fix, where triggerable via stdin):
- G-2: `drill` with `L0` and with negative L → expected error/return ≠ 0.
- G-3: Expression with division by 0 and `SQRT[-1]` → expected error.
- G-4: Block with P/R from preceding block → correctly isolated.
- G-7: Comment `(probeopen)` without crash.
- G-8: `(multi-line\ncomment` and `X1 Y2` whitespace cases.
- G-1: Movement with tool comp/G43 without a set tool → clean rejection.

**Coverage extension** (new `gcodetool` tests for untested codes):
- Arcs: G2/G3 in IJK and R format, full circle, all three planes (G17/G18/G19).
- Drilling cycles: G81/G82/G83/G73/G85/G89, incl. R/Q/L parameters and G98/G99 retract.
- Modal/units: G20↔G21 at runtime, G90/G91, G93/G94.
- Spindle/coolant/M-codes: M3/M4/M5, M7/M8/M9 (state output).
- Dwell G4; tool change M6 with T.

## Acceptance Criteria

- [ ] All 14 findings fixed or explicitly noted as "won't fix with rationale" in the status.
- [ ] Build green; existing 25 tests still green.
- [ ] ≥ 15 new `gcodetool` tests, all green.
- [ ] Functional G/M-code coverage documented as increased (record target figure in the status).

## Risks

- G-9 (`arc`) and G-10 (junction) touch numerically sensitive paths — watch the golden files of the
  existing offset/varRef tests for whether outputs change unintentionally.
- G-3 (throw instead of 0) may break legitimate, previously tolerated G-code programs →
  decide deliberately and document in the status.
