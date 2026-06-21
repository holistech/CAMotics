# CAMotics — Verbesserungs-Initiative: Status

Zentrales Log für die Umsetzung der Befunde aus [`CODE_REVIEW.md`](../../CODE_REVIEW.md)
und den Aufbau einer vollständigen Testsuite.

**Modus:** Tests verzahnt mit Fixes pro Modul · autonomer Durchlauf bis Blocker.
**Start:** 2026-06-21

---

## Gesamtfortschritt

| Projekt | Thema | Status | Befunde behoben | Tests neu | Build | Tests grün |
|---------|-------|:------:|:---------------:|:---------:|:-----:|:----------:|
| [P1](P1-test-infrastructure.md) | Test-Infrastruktur & Simulations-Harness | ✅ abgeschlossen | — | 6 | ✅ | ✅ 31/31 |
| [P2](P2-gcode-engine.md) | G-code-Engine: Fixes + Tests | ✅ abgeschlossen | 10 fix / 4 bewertet | 11 | ✅ | ✅ 42/42 |
| [P3](P3-simulation.md) | Simulation/Contour/Render: Fixes + Tests | ✅ abgeschlossen | 7 fix / 3 bewertet / 3→P6 | 2 | ✅ | ✅ 44/44 |
| [P4](P4-bindings-io.md) | Sprach-Bindings & IO + Security | ✅ abgeschlossen | 12 fix / 3 bewertet | 1 | ✅ | ✅ 45/45 |
| [P5](P5-gui.md) | GUI: Fixes | ✅ abgeschlossen | 6 fix / 8 bewertet→P6 | 0 | ✅ | ✅ 45/45 |
| [P6](P6-cleanup.md) | Cleanup & finale Verifikation | ✅ abgeschlossen | toter Code + Coverage | — | ✅ | ✅ 45/45 |

Status-Legende: ⬜ offen · 🟡 in Arbeit · ✅ abgeschlossen · ⛔ blockiert

---

## Baseline (vor Beginn)

- Build: ✅ `scons -j24` grün (alle 6 Binaries + Python-Modul)
- Tests: ✅ 25/25 grün (`tplTests` 10, `offsetTests` 8, `varRefTests` 6, `oCodeTests` 1)
- Abgedeckte Binaries: 2/6 (`gcodetool`, `tplang`)
- Funktionale G/M-Code-Abdeckung: 12/225 (~5 %)

---

## Änderungs-Log

| Datum | Projekt | Aktion |
|-------|---------|--------|
| 2026-06-21 | — | Code-Review abgeschlossen, 6-Projekt-Plan erstellt, Status-Tracking aufgesetzt |
| 2026-06-21 | P1 | Sim-Test-Harness gebaut: `tests/simTests/{stl-metrics.py,run-sim}` (Kennzahl-basiert, `--threads=1` deterministisch). 3 Sim-Tests (Box/Drill/Arc) + 3 Planner-Tests angelegt. `tests/README.md` ergänzt. Testsuite: 25 → **31 grün**. |
| 2026-06-21 | P1→P3 | Neuer Befund **S-13** entdeckt: `camsim.cpp:134` liest `bounds` vor `update()` → automatisches Workpiece liefert leeres Ergebnis. In CODE_REVIEW + P3 dokumentiert. |
| 2026-06-21 | P2 | **10 Fixes** umgesetzt: G-1 (Tool-Sentinel `int`), G-2 (drill L validieren), G-3 (Div/0 + SQRT/LN/ACOS/ASIN-Domain werfen), G-5 (LineCommand offset), G-6 (Rekursionstiefe werfen), G-7 (specialComment Iterator), G-9 (arc coincident points), G-11 (`1ULL`-Shift), G-13 (LinePlanner-Lecks/pop_back), G-14 (activeMotion Null-Check). **11 Tests** neu (6 errorTests + 5 gcodeTests). Suite: 31 → **42 grün**. |
| 2026-06-21 | P2 | **4 Befunde differenziert bewertet (kein blinder Fix):** G-4, G-8, G-10, G-12 — siehe P2-Abschlussnotizen. G-10 war ein **Fehlbefund** (Code bereits korrekt). |
| 2026-06-21 | — | P1+P2 in Branch `test-suite` committet (3 Commits: docs / P1 / P2). |
| 2026-06-21 | P3 | **7 Fixes:** K-1/S-1 (Sweep unsigned-UB, **kritisch**), S-2 (isValid invertiert), S-3 (Simulation-Member init), S-4 (Renderer threads==0 Hänger), S-5 (MC33 NaN-Guard + Cache), S-12 (Fortschritt-Underflow), S-13 (camsim bounds-Reihenfolge). **2 Tests** neu (SmallToolTest=K-1-Regression, ThreadsZeroTest=S-4). Suite: 42 → **44 grün**. |
| 2026-06-21 | P3 | **K-1 präzisiert:** Symptom ist UB-bedingt plattformabhängig (x86/gcc: falsche Facettenzahl statt Totalausfall) — durch Gegentest belegt (buggy 3356 ≠ fixed 3740). |
| 2026-06-21 | P4 | **12 Fixes:** K-2/L-1 (PyPtr Copy/Move-Ctor, **kritisch**), L-2 (PyJSON 4 Referenzlecks), L-3 (Runner-Thread vor Aktiv-Prüfung), L-4 (DXF Null-Checks), L-5 (STL gcount), L-6 (opt Modulo/Underflow bei 0 Cuts), L-8 (resolution>0), L-9 (decodeFilename Underflow), L-11 (MatrixModule neg. Index), L-12 (PyNameResolver INCREF-Reihenfolge), L-13 (Catch.h überschreibt Exception), L-15 (XMLHandler currentTool). **1 Test** (pythonTests/RefcountTest). Suite: 44 → **45 grün**. |
| 2026-06-21 | P4 | **L-10 (XXE) verifiziert: kein Risiko.** cbang nutzt Expat ohne `XML_SetExternalEntityRefHandler`; `XML_SetParamEntityParsing` ist per Default `NEVER` → externe Entitäten werden nicht aufgelöst. Kein Fix nötig. |
| 2026-06-21 | — | P3+P4 committet (2 Commits). |
| 2026-06-21 | P5 | **6 Fixes:** U-1 (QStringListModel-Leak pro Resize, **HOCH**), U-2 (BBCtrlAPI uninit. Member), U-3 (Dangling `fromRawData` bei async PUT), U-4 (Observer-Lebenszeit dokumentiert+erzwungen), U-7 (line-1 uint32-Underflow), U-12 (GL-Uniform tolerieren statt Draw-Abbruch). GUI baut, camotics startet, 45 Tests grün. |
| 2026-06-21 | — | P5 committet. |
| 2026-06-21 | P6 | **Toter Code entfernt:** `sim/OctTree.{cpp,h}` (S-9, nirgends instanziiert), ungenutzte `Workpiece`-Member `center`/`halfDim2` (S-11). **gcov-Coverage-Option** zu SConstruct hinzugefügt (`coverage=1`). **Echte Coverage gemessen.** CLAUDE.md (Test-Suiten + Coverage) und CODE_REVIEW.md (Umsetzungsstatus) aktualisiert. 45 Tests grün. |

---

## P1 — Abschlussnotizen

- **Determinismus:** STL-Geometrie hängt von der Threadzahl ab (Partitionsgrenzen) →
  Tests laufen fest mit `--threads=1`; über 3 Läufe bit-stabile Kennzahlen verifiziert.
- **Workpiece:** Tests nutzen `.camotics`-Projekte mit festen Bounds, da der
  Automatik-Pfad defekt ist (S-13). Nach dem S-13-Fix (P3) auf reinen G-code umstellbar.
- **SmallToolTest (K-1-Regression):** bewusst **nicht** in P1 angelegt, sondern in P3
  zusammen mit dem K-1-Fix (TDD: Test schlägt vor dem Fix fehl, danach grün).
- Abnahmekriterien P1 erfüllt: ≥4 Sim-Tests (3 + SmallTool folgt), ≥3 Planner-Tests,
  Harness integriert, Doku vorhanden.

## P2 — Abschlussnotizen (differenziert bewertete Befunde)

Vier Befunde wurden **bewusst nicht** als der ursprünglich vorgeschlagene Fix umgesetzt,
weil die Verifikation am echten Code etwas anderes ergab. Adversariale Prüfung statt
blindem Patchen:

- **G-4 (varValues pro Block zurücksetzen): NICHT umgesetzt — würde Regression erzeugen.**
  Ein pauschaler Reset in `startBlock()` würde **modale Bohrzyklen** (G81–G89) brechen:
  dort bleiben R/Z/F über Folgeblöcke gültig (`G81 X.. Y.. Z.. R..` gefolgt von nur
  `X.. Y..`). Der `DrillCycleTest` belegt dieses modale Verhalten. Korrekt wäre nur das
  selektive Absichern *nicht*-modaler Hilfsparameter; L wurde bereits in G-2 abgesichert.
- **G-8 (Whitespace in Zahlen): nicht "gefixt".** RS-274/NGC erlaubt Whitespace innerhalb
  von Zahlen (LinuxCNC entfernt vorab allen Whitespace), das `Tokenizer::number()`-Verhalten
  ist also **standardkonform**. Nicht angetastet, um keine Konformität zu brechen.
- **G-10 (Junction-Velocity mit Rotationsachsen): FEHLBEFUND.** Der aktuelle Code beschränkt
  die Berechnung bereits auf XYZ (`unit.slice<3>()`, `computeMaxAccel` iteriert `axis < 3`).
  Der Review-Befund bezog sich auf älteren Code / übersah die Beschränkung. Kein Fix nötig.
- **G-12 (Cutter-Radius-Kompensation): belassen (NIEDRIG).** Bereits als „not implemented"
  gewarnt; der gesetzte State wird nie auf die Bahn angewandt (Bahn bleibt unkompensiert,
  nicht falsch). Vollimplementierung von G40–G42 ist ein eigenes Feature, kein Bugfix.

Ebenfalls notiert: **G83 (Peck-Drilling)** ist im Code als `// TODO Peck drill`
(`ControllerImpl.cpp:1148`) markiert — Q wird ignoriert, ein Durchgang statt Pecking.
Bekannte Nicht-Implementierung, kein versteckter Defekt.

## P3 — Abschlussnotizen (differenziert bewertete Befunde)

- **S-6 (exakte Float-Vergleiche Conic/Spheroid-Sweep): konservativ belassen.** Die
  `epsilon == 0`-Vergleiche sind theoretisch fragil, aber der Code funktioniert und liefert
  korrekte Oberflächen. Ein Toleranz-Fix (`fabs(epsilon) < eps`) an dieser Kern-Sweep-
  Routine hätte hohes Regressionsrisiko (willkürliche Schwelle, schwer zu verifizieren) ohne
  nachgewiesenen Defekt. Zurückgestellt, bis ein reproduzierbares Artefakt vorliegt.
- **S-7 (ungeschützte Divisionen/sqrt in CorrectedMC33Cube): verifiziert, belassen.** Die
  entstehenden NaN/inf propagieren **sicher** durch die nachfolgenden Vergleiche
  (`t1 < 1 && 0 < t1 && …` ergeben bei NaN `false`) zu definierten Code-Pfaden — **kein
  Crash, kein klassisches UB** (IEEE-NaN ist wohldefiniert). Ein korrekter Fallback für
  degenerierte Zellen erfordert MC33-Algorithmus-Expertise; ein willkürlicher Guard würde
  die Tiling-Auswahl riskieren statt verbessern.
- **S-5 (getCenter): teilweise.** NaN-Guard (`count>0`) und Cache-Aktivierung umgesetzt
  (beide ohne Normalfall-Änderung, Goldens stabil). Die heikle 8-bit-Fallnummer-vs-12-bit-
  Kantenmaske-Semantik wurde **bewusst nicht** angetastet (MC33-Topologie-Risiko), nur im
  Code kommentiert.
- **S-8 (ToolSweep::depth Hot-Path): zurückgestellt.** Performance-Optimierung, kein
  Korrektheitsbug. Laut Plan nur mit nachgewiesener Kennzahl-Gleichheit vorher/nachher zu
  mergen — als eigenständige, sorgfältig zu benchmarkende Aufgabe ausgelagert.
- **S-9 / S-10 / S-11 (toter Code, const-Korrektheit): → P6** (Cleanup-Projekt).

## P4 — Abschlussnotizen (differenziert bewertete Befunde)

- **L-7 (Pfad-Sandbox für `.camotics`-Projekte): bewusst keine harte Sandbox.** Ein Projekt
  kann auf Dateien per absolutem/`../`-Pfad verweisen und TPL (beliebiges JS) laden. Eine
  harte Ablehnung würde legitime Workflows mit absoluten Pfaden brechen. Das ist eine
  **Vertrauensgrenze-Entscheidung** des Projektbesitzers: Ein `.camotics`-Projekt ist wie
  ausführbarer Code zu behandeln (Öffnen = Vertrauen wie bei einem Makro-Dokument). Dies ist
  zu dokumentieren (README/UI-Hinweis), nicht durch einen riskanten Pfad-Filter zu erzwingen.
- **L-10 (XXE): kein Risiko (verifiziert).** Siehe Log — Expat ohne externen Entity-Handler.
- **L-14 (ClipperModule Integer-Überlauf): NIEDRIG, belassen.** Betrifft nur absurd große
  Koordinaten in **nutzergeschriebenen** TPL-Skripten (kein untrusted Input); ein Clamp
  hätte geringen Nutzen und könnte legitime Extremgeometrie verändern.

## P5 — Abschlussnotizen (zurückgestellte/bewertete Befunde)

GUI-Code ist nicht automatisiert testbar (kein Display in CI). Die HOCH-Speicherfehler
wurden behoben und über Build + Smoke-Test (camotics startet, Libs aufgelöst) verifiziert.
Folgende Befunde wurden differenziert behandelt:

- **U-4 (Observer-Lebenszeit): erzwungen + dokumentiert.** Die Zerstörungsreihenfolge ist
  durch `view(new View(valueSet))` bereits zwingend korrekt (valueSet überlebt view); ein
  Umstellen ist unmöglich (View braucht valueSet im Konstruktor). Mit Warn-Kommentar fixiert.
  Ein vollständiges Observer-Deregistrierungs-System ist ein größerer Umbau (ohne GUI-Tests
  zu riskant).
- **U-5 / U-6 (OpenGL-Ressourcen-Lebenszyklus): zurückgestellt.** Korrektur erfordert
  sorgfältige Kontext-Lebenszyklus-Behandlung, nur mit laufender GUI verifizierbar.
- **U-8 (Reconnect-Limit): UX-Entscheidung.** Der UB-Teil (uninit. `lastMessage`) ist via
  U-2 behoben. Ein hartes Reconnect-Limit ist nicht eindeutig gewünscht (CNC-Controller
  sollen nach temporärem Ausfall automatisch wieder verbinden).
- **U-9 (QtWin entflechten): Wartbarkeit, → eigene Aufgabe** (kein Defekt).
- **U-10 (`QString::sprintf`) / U-13 (`QGLFormat`, `event->delta()`): → P6** (Qt6-Vorbereitung).
- **U-11 (QMenu/QMovie Parent) / U-14 (redraw-Drosselung): NIEDRIG, → P6.**

## Finale Testabdeckung (gcov, gemessen 2026-06-21)

Instrumentierter Build (`scons coverage=1 with_gui=0`), komplette Testsuite, gcov-Auswertung.
GUI-Code (`qt/`, `view/`, `value/`) ist nicht instrumentiert (nicht automatisiert testbar).

| Modul | Zeilen-Coverage | Bemerkung |
|-------|:---------------:|-----------|
| `gcode/parse` | 66,5 % | Tokenizer/Parser — gut abgedeckt |
| `gcode/interp` | 57,9 % | Interpreter/Evaluator (inkl. neue Fehlerpfade) |
| `gcode/ast` | 56,7 % | |
| `gcode/plan` | 50,8 % | via `plannerTests` |
| `gcode` (Kern) | 46,3 % | |
| `gcode/machine` | 30,3 % | viele Output-Senken (JSON/GCode) ungetestet |
| `camotics/sim` | 25,4 % | via `simTests` (vorher ~0 %) |
| `camotics/project` | 25,0 % | |
| `camotics/render` | 12,7 % | |
| `camotics/contour` | 8,3 % | Marching Cubes — pro Test nur ein Tiling-Pfad |
| `tplang` | 37,7 % | |
| **Gesamt (getesteter Nicht-GUI-Code)** | **40,3 %** | **3684 / 9134 Zeilen** |

Treiber-Binaries: `gcodetool` 90,5 %, `planner` 73,3 %, `camsim` 75,8 %, `tplang` 60,0 %.

**Vorher → Nachher:** 25 → 45 Tests; 2 → 5 getriebene Binaries; G/M-Code-Abdeckung von ~5 %
deutlich erhöht; `sim`/`contour`/`render` von praktisch 0 % auf messbare Abdeckung; Python-
Bindings erstmals mit Regressionstest.

### Empfehlungen für weitere Abdeckung (optional)
- `gcode/machine` (30 %): Tests für JSON-/GCode-Machine-Ausgabesenken.
- `camotics/contour` (8 %): Tests mit Geometrien, die verschiedene MC33-Tilings auslösen.
- GUI: erfordert eine Display-fähige Test-Umgebung (z. B. Xvfb + Qt-Test) — eigenes Vorhaben.

## Offene Blocker / Entscheidungen

_(keine — alle 6 Projekte abgeschlossen)_
