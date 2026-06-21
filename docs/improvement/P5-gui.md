# P5 — GUI: Fixes

**Goal:** Fix memory/ownership and robustness defects in the Qt/OpenGL GUI.
GUI code is only partly automatable for testing — focus on correctness through
review + manual verification; the testable `value/` part gets a test.

**Status:** ⬜ open · **Findings:** U-1…U-14 (details see `CODE_REVIEW.md` §3.3)

---

## Fixes (prioritized)

| ID | Severity | File:Line | Fix Core |
|----|-------------|-------------|----------|
| U-1 | HIGH | `qt/QtWin.cpp:1411,1242,1930` | Persistent member `QStringListModel` with a parent; only `setStringList()`; do not rebuild it in `resizeEvent`. |
| U-2 | HIGH | `qt/BBCtrlAPI.cpp:43-45`, `.h:42-43` | Initialize `lastMessage(0)`, `useSystemProxy(false)`. |
| U-3 | HIGH | `qt/BBCtrlAPI.cpp:104,123` | Copying `QByteArray(data, length)` instead of `fromRawData`. |
| U-4 | HIGH | `value/VarValue.h:30`, `MemberFunctorObserver.h:30`, `qt/QtWin.h:111-114` | Deregistration in the Value/Observer system; at minimum destruction order with `valueSet` last + comment. |
| U-5 | MEDIUM | `view/View.cpp:297-319`, `view/GLScene.cpp:45` | Make `glInit()` idempotent (clear the scene beforehand / first-init only). |
| U-6 | MEDIUM | `view/GLProgram.cpp:41-45`, `view/VBO.cpp:27-32` | Couple GL release to `makeCurrent()`/the widget lifecycle. |
| U-7 | MEDIUM | `qt/BBCtrlAPI.cpp:109,157-191,203` | Validate the address via `QUrl`; `line ? line-1 : 0`; check JSON fields. |
| U-8 | MEDIUM | `qt/BBCtrlAPI.cpp:87-91,146-154` | Reconnect counter + abort/status message; keep the original address. |
| U-9 | MEDIUM | `qt/QtWin.cpp` | Disentangle `update*`/`on_action*Surface`/spinbox handlers in a data-driven way. |
| U-10 | MEDIUM | `qt/QtWin.cpp:300,1409,1785…` | `QString::sprintf` → `arg`/`number`/`asprintf`. |
| U-11 | LOW | `qt/QtWin.cpp:177,185,496,1661-1672` | `QMenu`/`QMovie` with a parent; avoid manual `delete`. |
| U-12 | LOW | `view/GLProgram.cpp:119-128` | Tolerate missing uniforms (cache, no-op, one-time warning). |
| U-13 | LOW | `qt/GLView.cpp:31,98` | `QSurfaceFormat` / `QWheelEvent::angleDelta()`. |
| U-14 | LOW | `qt/QtWin.cpp:895-907` | Reissue the discarded immediate redraw via `singleShot`. |

## Tests / Verification

- **`value/` observer (testable):** Small unit-style test via the Python module or
  a mini driver that checks `ValueSet`/`VarValue` lifetime and deregistration (U-4).
- **Manual verification** (documented in the status): Start `camotics`, load a project,
  resize the window multiple times (U-1 leak via memory observation), un-/redock the dock (U-5/U-6),
  BBCtrl connection against an unreachable host (U-2/U-7/U-8).
- **Build verification:** The GUI still builds (`scons` with `with_gui=1`).

## Acceptance Criteria

- [ ] All HIGH findings (U-1…U-4) fixed.
- [ ] Build with GUI green; no new warnings.
- [ ] `value/` test green (if a driver is feasible) or justification in the status.
- [ ] Manual verification steps performed and recorded in the status.

## Risks

- U-4 (observer lifetime) is structural — prefer a minimally invasive solution (destruction
  order + docs), larger rework only if necessary.
- U-10 (`sprintf` migration) is widely scattered → mechanical, but pay careful attention to
  format semantics.
