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
| [P3](P3-simulation.md) | Simulation/Contour/Render: Fixes + Tests | ⬜ offen | 0/13 | 0 | — | — |
| [P4](P4-bindings-io.md) | Sprach-Bindings & IO + Security | ⬜ offen | 0/15 | 0 | — | — |
| [P5](P5-gui.md) | GUI: Fixes | ⬜ offen | 0/14 | 0 | — | — |
| [P6](P6-cleanup.md) | Cleanup & finale Verifikation | ⬜ offen | — | — | — | — |

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

## Offene Blocker / Entscheidungen

_(keine)_
