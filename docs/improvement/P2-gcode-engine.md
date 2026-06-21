# P2 — G-code-Engine: Fixes + Tests

**Ziel:** Korrektheits- und Robustheitsdefekte in `src/gcode` beheben und die
funktionale Abdeckung der G-code-Engine (heute ~5 % der Code-Tabelle) deutlich erhöhen.

**Status:** ⬜ offen · **Befunde:** G-1…G-14 (Details siehe `CODE_REVIEW.md` §3.1)

---

## Fixes (priorisiert)

| ID | Schweregrad | Datei:Zeile | Fix-Kern |
|----|-------------|-------------|----------|
| G-1 | HOCH | `ControllerImpl.h:161` | `getCurrentTool()` → `int`, Sentinel `-1`; Aufrufer `:740,1084` anpassen. |
| G-2 | HOCH | `ControllerImpl.cpp:503,515` | `drill()` L als `int` lesen, `>= 1` validieren, sonst werfen. |
| G-3 | HOCH | `interp/Evaluator.cpp:57-61,66-111` | Division/Modulo durch 0 → werfen; `SQRT/LN/pow`-Domain prüfen. |
| G-4 | MITTEL | `ControllerImpl.cpp:71,981` | `varValues` in `startBlock()` zurücksetzen; Hilfsparameter-Lesezugriffe gegen `vars`-Maske absichern. |
| G-5 | MITTEL | `plan/LineCommand.cpp:181-192` | `offset += s.offset` → `offset = s.offset`. |
| G-6 | MITTEL | `interp/OCodeInterpreter.cpp:74-78` | Bei Überschreiten der Maximaltiefe werfen statt nur warnen. |
| G-7 | MITTEL | `interp/GCodeInterpreter.cpp:87` | `it != end` vor jedem `*it` in `specialComment`. |
| G-8 | MITTEL | `parse/Tokenizer.cpp:57-76,93` | Klammerkommentar auf Zeilenende begrenzen; Whitespace-Schlucken in `number()` unterbinden/dokumentieren. |
| G-9 | MITTEL | `ControllerImpl.cpp:359-423` | `arc()`: degenerierte Fälle (Radius/Distanz ≈ 0) abfangen, relative Toleranzen. |
| G-10 | MITTEL | `plan/LinePlanner.cpp:1197-1210` | Junction-Velocity auf translatorische Achsen beschränken. |
| G-11 | MITTEL | `plan/LinePlanner.cpp:81,381,388` | `uint64_t`-Shift-Literale; `idBits`-Bereich validieren. |
| G-12 | NIEDRIG | `ControllerImpl.cpp:738-767` | Cutter-Radius-Comp: entweder klar ablehnen (werfen/Warnung + State nicht setzen) statt still falsche Bahn. |
| G-13 | NIEDRIG | `plan/LinePlanner.cpp:330,449,562` | RAII/SmartPointer für `lc`; `pop_back`-Schleifen gegen `empty()` absichern. |
| G-14 | NIEDRIG | `interp/GCodeInterpreter.cpp:305-307` | Null-Prüfung vor `activeMotion->priority`. |

## Tests (verzahnt)

**Regressionstests** (je ein gezielter `gcodetool`-Test pro Fix, wo via stdin auslösbar):
- G-2: `drill` mit `L0` und mit negativem L → erwarteter Fehler/return ≠ 0.
- G-3: Ausdruck mit Division durch 0 und `SQRT[-1]` → erwarteter Fehler.
- G-4: Block mit P/R aus Vorblock → korrekt isoliert.
- G-7: Kommentar `(probeopen)` ohne Crash.
- G-8: `(mehrzeiliger\nKommentar` und `X1 Y2` Whitespace-Fälle.
- G-1: Bewegung mit Tool-Comp/G43 ohne gesetztes Werkzeug → saubere Ablehnung.

**Abdeckungs-Erweiterung** (neue `gcodetool`-Tests für ungetestete Codes):
- Bögen: G2/G3 in IJK- und R-Format, Vollkreis, alle drei Ebenen (G17/G18/G19).
- Bohrzyklen: G81/G82/G83/G73/G85/G89, inkl. R/Q/L-Parameter und G98/G99-Rückzug.
- Modal/Einheiten: G20↔G21 im Lauf, G90/G91, G93/G94.
- Spindel/Kühlung/M-Codes: M3/M4/M5, M7/M8/M9 (Zustandsausgabe).
- Dwell G4; Tool-Wechsel M6 mit T.

## Abnahmekriterien

- [ ] Alle 14 Befunde behoben oder explizit als „won't fix mit Begründung" im Status notiert.
- [ ] Build grün; bestehende 25 Tests weiterhin grün.
- [ ] ≥ 15 neue `gcodetool`-Tests, alle grün.
- [ ] Funktionale G/M-Code-Abdeckung dokumentiert erhöht (Zielmarke im Status festhalten).

## Risiken

- G-9 (`arc`) und G-10 (Junction) berühren numerisch sensible Pfade — Golden-Files der
  bestehenden offset-/varRef-Tests beobachten, ob sich Ausgaben unbeabsichtigt ändern.
- G-3 (werfen statt 0) kann legitime, bisher tolerierte G-code-Programme brechen →
  bewusst entscheiden und im Status dokumentieren.
