# P5 — GUI: Fixes

**Ziel:** Speicher-/Ownership- und Robustheitsdefekte in der Qt-/OpenGL-GUI beheben.
GUI-Code ist nur eingeschränkt automatisiert testbar — Fokus auf Korrektheit durch
Review + manuelle Verifikation; der testbare `value/`-Teil bekommt einen Test.

**Status:** ⬜ offen · **Befunde:** U-1…U-14 (Details siehe `CODE_REVIEW.md` §3.3)

---

## Fixes (priorisiert)

| ID | Schweregrad | Datei:Zeile | Fix-Kern |
|----|-------------|-------------|----------|
| U-1 | HOCH | `qt/QtWin.cpp:1411,1242,1930` | Persistentes Member-`QStringListModel` mit Parent; nur `setStringList()`; nicht im `resizeEvent` neu bauen. |
| U-2 | HOCH | `qt/BBCtrlAPI.cpp:43-45`, `.h:42-43` | `lastMessage(0)`, `useSystemProxy(false)` initialisieren. |
| U-3 | HOCH | `qt/BBCtrlAPI.cpp:104,123` | Kopierendes `QByteArray(data, length)` statt `fromRawData`. |
| U-4 | HOCH | `value/VarValue.h:30`, `MemberFunctorObserver.h:30`, `qt/QtWin.h:111-114` | Deregistrierung im Value/Observer-System; mind. Zerstörungsreihenfolge `valueSet` zuletzt + Kommentar. |
| U-5 | MITTEL | `view/View.cpp:297-319`, `view/GLScene.cpp:45` | `glInit()` idempotent (Szene vorher leeren / nur Erst-Init). |
| U-6 | MITTEL | `view/GLProgram.cpp:41-45`, `view/VBO.cpp:27-32` | GL-Freigabe an `makeCurrent()`/Widget-Lebenszyklus koppeln. |
| U-7 | MITTEL | `qt/BBCtrlAPI.cpp:109,157-191,203` | Adresse via `QUrl` validieren; `line ? line-1 : 0`; JSON-Felder prüfen. |
| U-8 | MITTEL | `qt/BBCtrlAPI.cpp:87-91,146-154` | Reconnect-Zähler + Abbruch/Statusmeldung; Originaladresse beibehalten. |
| U-9 | MITTEL | `qt/QtWin.cpp` | `update*`/`on_action*Surface`/Spinbox-Handler datengetrieben entflechten. |
| U-10 | MITTEL | `qt/QtWin.cpp:300,1409,1785…` | `QString::sprintf` → `arg`/`number`/`asprintf`. |
| U-11 | NIEDRIG | `qt/QtWin.cpp:177,185,496,1661-1672` | `QMenu`/`QMovie` mit Parent; manuelle `delete` vermeiden. |
| U-12 | NIEDRIG | `view/GLProgram.cpp:119-128` | Fehlende Uniforms tolerieren (cachen, no-op, einmalige Warnung). |
| U-13 | NIEDRIG | `qt/GLView.cpp:31,98` | `QSurfaceFormat` / `QWheelEvent::angleDelta()`. |
| U-14 | NIEDRIG | `qt/QtWin.cpp:895-907` | Verworfenen Sofort-Redraw via `singleShot` nachziehen. |

## Tests / Verifikation

- **`value/`-Observer (testbar):** Kleiner Unit-artiger Test über das Python-Modul oder
  einen Mini-Treiber, der `ValueSet`/`VarValue`-Lebenszeit und Deregistrierung (U-4) prüft.
- **Manuelle Verifikation** (dokumentiert im Status): `camotics` starten, Projekt laden,
  Fenster mehrfach resizen (U-1 Leak via Speicherbeobachtung), Dock un-/andocken (U-5/U-6),
  BBCtrl-Verbindung gegen nicht erreichbaren Host (U-2/U-7/U-8).
- **Build-Verifikation:** GUI baut weiterhin (`scons` mit `with_gui=1`).

## Abnahmekriterien

- [ ] Alle HOCH-Befunde (U-1…U-4) behoben.
- [ ] Build mit GUI grün; keine neuen Warnungen.
- [ ] `value/`-Test grün (falls Treiber realisierbar) oder Begründung im Status.
- [ ] Manuelle Verifikationsschritte durchgeführt und im Status protokolliert.

## Risiken

- U-4 (Observer-Lebenszeit) ist strukturell — minimal-invasive Lösung (Zerstörungs-
  reihenfolge + Doku) bevorzugen, größere Umbauten nur falls nötig.
- U-10 (`sprintf`-Migration) ist breit gestreut → mechanisch, aber sorgfältig auf
  Format-Semantik achten.
