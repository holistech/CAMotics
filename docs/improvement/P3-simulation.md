# P3 — Simulation / Contour / Render: Fixes + Tests

**Goal:** Fix the critical simulation bug (K-1) and the robustness/numerics defects in
`sim/`, `contour/`, `render/` — verified via the simulation test harness created in P1.

**Status:** ⬜ open · **Findings:** S-1…S-12 (details see `CODE_REVIEW.md` §3.2)
**Dependency:** P1 (sim harness must be in place).

---

## Fixes (prioritized)

| ID | Severity | File:Line | Fix Core |
|----|-------------|-------------|----------|
| S-1 (**K-1**) | **CRITICAL** | `sim/Sweep.cpp:33-35` | `double maxLen = radius * 16;`, ensure `radius > 0`, `steps = (maxLen <= 0 \|\| len <= maxLen) ? 1 : ceil(len/maxLen)`. |
| S-2 | HIGH | `sim/CutWorkpiece.cpp:34-43` | Correct `isValid()` logic or remove dead code. |
| S-3 | MEDIUM | `sim/Simulation.cpp:63-89`, `.h:50-53` | Read `threads` in `read()`; in-class initializers for `threads/resolution/time`. |
| S-4 | MEDIUM | `render/Renderer.cpp:61,76` | `threads = std::max(1u, threads);` at the start of the method. |
| S-5 | MEDIUM | `contour/CorrectedMC33.cpp:31-46` | `count>0` guard; correct active-edge mask; set `centerComputed`. |
| S-6 | MEDIUM | `sim/ConicSweep.cpp:65,73`, `sim/SpheroidSweep.cpp:35,62` | Epsilon tolerances instead of exact float comparisons. |
| S-7 | MEDIUM | `contour/CorrectedMC33Cube.cpp:130,150-180` | Check denominator/discriminant for ~0, defined fallback. |
| S-8 | MEDIUM | `sim/ToolSweep.cpp:111-134` | `depth()` hot path: avoid heap `vector`/`sort` per voxel corner (pre-sorted/small buffer). |
| S-9 | LOW | `sim/OctTree.cpp` | Remove dead code (→ possibly move to P6). |
| S-10 | LOW | `sim/AABB.cpp:31-122` | Limit recursion depth; methods `const`. |
| S-11 | LOW | `sim/Workpiece.cpp:28-32` | Remove unused members. |
| S-12 | LOW | `render/Renderer.cpp:101` | Avoid unsigned underflow in the progress (signed/clamp). |
| S-13 | HIGH | `camsim.cpp:134-135` | `bounds` is read BEFORE `update(*path)` → empty bounds for an automatic workpiece → "Empty workpiece, nothing to simulate". Makes `camsim` unusable for plain G-code/TPL without explicit bounds. **Discovered during P1.** Fix: swap the order (first `update`, then `getBounds`). |

> **S-13 / test simplification:** Once S-13 is fixed, the `simTests` can be switched to plain
> G-code inputs with an automatic workpiece (instead of `.camotics` projects
> with fixed bounds). Until then the tests use fixed bounds — see `tests/README.md`.

## Tests (interlocked)

- **S-1 / K-1:** Activate `SmallToolTest` from P1 — after the fix it must produce a correct,
  non-empty mesh (metrics > 0). Documented as faulty before the fix.
- **S-4:** Sim test with `--threads 0` → must not hang, must produce a correct result
  (secure the harness with a timeout).
- **S-2:** If `isValid()` is reactivated, a targeted unit-style test via `camsim`.
- **S-6:** Sim test with a nearly vertical tool path (conic/spheroid special case) →
  stable surface instead of NaN/artifact.
- **Regression protection:** The `BoxMill/Drill/ArcMill` metrics created in P1 may only
  change as expected due to the numerics fixes (golden possibly reset deliberately,
  justify the change in the status).

## Acceptance Criteria

- [ ] K-1 fixed and proven by `SmallToolTest` (green).
- [ ] No hang at `threads==0` (test with timeout green).
- [ ] All S findings fixed or explicitly moved to P6 (dead code).
- [ ] Build green; all sim and existing tests green.

## Risks

- S-5/S-7 (marching-cubes numerics) may alter the generated surface → check the metric
  goldens of the sim tests carefully; validate changes visually/numerically for plausibility.
- S-8 (hot-path rebuild) is a performance optimization with a correctness risk → merge only with
  metric equality before/after; otherwise defer.
