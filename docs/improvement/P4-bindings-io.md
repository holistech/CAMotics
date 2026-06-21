# P4 — Sprach-Bindings & IO + Security-Härtung

**Ziel:** Speicher-/Referenzfehler in den Python-Bindings beheben (inkl. kritischem K-2)
und die Parser für nicht vertrauenswürdige Eingaben (STL, DXF, `.camotics`) härten.

**Status:** ⬜ offen · **Befunde:** L-1…L-15 (Details siehe `CODE_REVIEW.md` §3.4)

---

## Fixes (priorisiert)

| ID | Schweregrad | Datei:Zeile | Fix-Kern |
|----|-------------|-------------|----------|
| L-1 (**K-2**) | **KRITISCH** | `python/PyPtr.h:26-45` | Copy-Konstruktor mit `Py_INCREF` ergänzen (Move-Ctor erwägen). |
| L-2 | HOCH | `python/PyJSON.cpp:47,63,76,80` | Neue Referenzen (`PySequence_GetItem`, `PyObject_Str/ASCII`) freigeben; `PyPtr` nutzen; Fehler prüfen. |
| L-3 | HOCH | `python/PySimulation.cpp:90-93,351,479` | „Task aktiv"-Prüfung VOR `new Runner(...)`; sonst Runner joinen/freigeben. |
| L-4 | MITTEL | `dxf/Reader.cpp:92-111` | Null-Prüfung für `entity` in `addVertex/addControlPoint/addKnot` mit klarer Meldung. |
| L-5 | MITTEL | `stl/Reader.cpp:38-115` | `gcount()` nach jedem `read` prüfen; `count` gegen Restdateigröße plausibilisieren; robustere ASCII/Binär-Heuristik. |
| L-6 | MITTEL | `opt/Opt.cpp:209`, `opt/AnnealState.cpp:75` | `if (paths.size() < 2) return;`; `if (index.empty()) return 0;`. |
| L-7 | MITTEL | `project/Files.cpp:53-61` | Pfade gegen Projektverzeichnis validieren (Traversal/absolut ablehnen oder bestätigen); TPL-Vertrauensgrenze dokumentieren. |
| L-8 | MITTEL | `project/Project.cpp:109-119` | `resolution > 0` + sinnvolle Obergrenze validieren. |
| L-9 | MITTEL | `project/XMLHandler.cpp:34` | `i + 2 < filename.size()` ohne size_t-Subtraktion. |
| L-10 | MITTEL | `project/Project.cpp:149` | XXE prüfen: externe Entity-/DTD-Auflösung im cbang-XML-Reader deaktivieren/verifizieren. |
| L-11 | NIEDRIG | `tplang/MatrixModule.cpp:106-112` | `if (matrix < 0 \|\| AXES_COUNT <= matrix) THROW(...)`. |
| L-12 | NIEDRIG | `python/PyNameResolver.cpp:27-30` | `PyCallable_Check` vor `Py_INCREF`; `PyTuple_SetItem`-NULL-Schutz. |
| L-13 | NIEDRIG | `python/Catch.h:24-31` | `PyErr_SetString` nur bei `!PyErr_Occurred()`. |
| L-14 | NIEDRIG | `tplang/ClipperModule.cpp:59,64,71` | Koordinaten/Produkt gegen Integer-Bereich plausibilisieren. |
| L-15 | NIEDRIG | `project/XMLHandler.cpp:46,139` | `currentTool` in `startElement("tool")` setzen. |

## Tests (verzahnt)

- **L-5 (STL):** Malformed-STL-Korpus unter `tests/stlTests/` — abgeschnittene Datei,
  übergroßes `count`, `"solid\n"`-ASCII, Binär mit zufälligem `"solid "`-Header → sauberer
  Fehler statt Crash/Hänger. Treiber: kleines Test-Programm oder `camsim`/`tplang` mit
  STL-Last (TPL kann STL nicht laden — ggf. dedizierter Mini-Treiber nötig).
- **L-4 (DXF):** Malformed-DXF (VERTEX ohne POLYLINE) via `tplang` DXF-Modul → klarer Fehler.
- **L-6 (opt):** G-code-Pfad mit 0 Cuts durch `planner`/`camsim` mit Optimierung → kein Crash.
- **L-8 (resolution):** `camsim --resolution 0` bzw. Projekt mit `resolution=0` → Ablehnung.
- **L-9 (decodeFilename):** `.camotics` mit Dateiname `"%"` → kein Wurf/Underflow.
- **L-1/L-2/L-3 (Python):** Falls eine Python-Testmöglichkeit besteht (Modul `camotics.so`),
  ein `pytest`/Skript-Test, der wiederholte `toJSON`-Konvertierung und doppelten Task
  ausführt (Refcount-Stabilität, kein Crash). Sonst als manuell verifiziert dokumentieren.
- **L-7 (Pfad-Sandbox):** `.camotics` mit `../`-Referenz → Ablehnung/Bestätigung.

## Abnahmekriterien

- [ ] K-2 + alle HOCH-Python-Befunde behoben.
- [ ] STL- und DXF-Parser überstehen Malformed-Input ohne Crash/Hänger (Tests grün).
- [ ] Pfad-Traversal und `resolution<=0` werden abgelehnt.
- [ ] XXE-Status geklärt und dokumentiert.
- [ ] Build grün; alle Tests grün.

## Risiken

- L-7 (Pfad-Sandbox) kann legitime Projekte mit absoluten Pfaden brechen → Verhalten
  bewusst wählen (harte Ablehnung vs. Warnung) und im Status dokumentieren.
- Python-Tests erfordern ggf. eine Test-Harness-Erweiterung; falls zu aufwändig, Refcount-
  Fixes per Code-Review + manuellem Smoke-Test absichern und das im Status vermerken.
