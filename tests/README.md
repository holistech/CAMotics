# CAMotics Tests

Die Tests nutzen den cbang-`testHarness` (Python). Jeder Test führt ein `command` aus
und vergleicht `stdout`/`stderr`/`return` gegen Golden-Files unter `<test>/expect/`.
Eingaben kommen aus `<test>/data/` (per `stdin` oder als Argument).

## Ausführen

```bash
cd tests
./testHarness                       # alle Suiten
./testHarness run simTests          # eine Suite
./testHarness run simTests/BoxMillTest   # ein Test
./testHarness diff simTests/BoxMillTest  # Diff actual vs. expected
```

Voraussetzung: Die Binaries (`gcodetool`, `planner`, `camsim`, `tplang`) müssen gebaut
sein (`scons` im Projektwurzelverzeichnis).

## Suiten

| Suite | Treiber | Inhalt |
|-------|---------|--------|
| `oCodeTests` | `gcodetool` | O-code-Kontrollfluss |
| `offsetTests` | `gcodetool` | Koordinatensysteme & Werkzeug-Offsets |
| `varRefTests` | `gcodetool` | G-code-Variablenreferenzen |
| `tplTests` | `tplang` | TPL/JavaScript-Tool-Path-Language |
| `plannerTests` | `planner` | Motion-Planning (JSON-Plan-Ausgabe) |
| `simTests` | `camsim` | End-to-End-Simulation (STL-Kennzahlen; alle Werkzeugformen) |
| `pythonTests` | `camotics.so` | Python-Binding-Refcount-Regression |
| `guiTests` | `camotics` | GUI-Pipeline-Smoke-Test (headless via Xvfb) |

## Simulationstests (`simTests`)

Da die rohe STL-Ausgabe nicht byte-stabil ist (Facetten-Reihenfolge hängt von der
Thread-Partitionierung ab), vergleichen die Sim-Tests **abgeleitete Kennzahlen**
(Facettenzahl, Bounding-Box, Volumen, Oberfläche) statt der Datei selbst.

- `run-sim <projekt.camotics>` — ruft `camsim --threads=1 --binary=false` auf und gibt
  die Kennzahlen aus `stl-metrics.py` nach stdout. **`--threads=1` ist Pflicht**: bei
  mehreren Threads entstehen an den Partitionsgrenzen leicht andere Facetten.
- `stl-metrics.py <datei.stl>` — extrahiert die deterministischen Kennzahlen (rundet
  gegen FP-Rauschen).

### Neuen Simulationstest hinzufügen

1. Verzeichnis `simTests/<Name>/data/` anlegen mit:
   - `project.camotics` — Projekt mit **festen** Bounds (`"automatic": false`), definiertem
     Werkzeug und fester `resolution`. Feste Bounds sind nötig, solange der
     Automatik-Workpiece-Pfad in `camsim` defekt ist (siehe `CODE_REVIEW.md`, S-13).
   - die referenzierte G-code-/TPL-Datei (relativer Pfad in `files`).
2. Golden erzeugen:
   ```bash
   mkdir -p simTests/<Name>/expect
   ./simTests/run-sim simTests/<Name>/data/project.camotics > simTests/<Name>/expect/stdout
   : > simTests/<Name>/expect/stderr
   echo -n 0 > simTests/<Name>/expect/return
   ```
3. Vor dem Commit den Test 3× laufen lassen und auf stabile Kennzahlen prüfen.

## Planner-Tests (`plannerTests`)

`planner --json-out` liest G-code von stdin und gibt den geplanten Bewegungsablauf als
JSON aus (deterministisch, inkl. simulierter Bearbeitungszeit auf stderr). Neue Tests
analog zu den `gcodetool`-Suiten: `data/stdin` + `expect/{stdout,stderr,return}`. Einige
Tests überschreiben das `command` per Test-`test.json` auf `--gcode` (trifft die
`GCodeMachine`-Ausgabesenke statt `JSONMachine`).

## GUI-Tests (`guiTests`)

`run-gui <projekt.camotics>` startet `camotics` headless unter **Xvfb** (kein Fenster auf
dem echten Display), lässt es das Projekt laden, die Oberfläche berechnen und per OpenGL
rendern, und beendet es dann per SIGTERM. Erfolg = **sauberer** Exit (Code 0): camotics
fängt SIGTERM ab (`FEATURE_SIGNAL_HANDLER`), der Poll-Timer in `QtApp::run` beendet die
Qt-Event-Loop, und die App fährt regulär herunter (State speichern, GL-Ressourcen
freigeben). Der Test verriegelt damit zugleich den sauberen Shutdown. Benötigt `xvfb-run`.

Weil camotics nun sauber herunterfährt, laufen die gcov-atexit-Handler — der GUI-Test
liefert daher **echte Zeilen-Coverage** für die GUI-Module (gemessen u. a. `view` ~59 %,
`value` ~72 %, `qt` ~28 %). Vgl. Coverage-Anleitung in `CLAUDE.md`.

## Code coverage

Siehe `CLAUDE.md` → „Code coverage". Kurzform: `scons coverage=1`, Tests laufen lassen,
`gcov --json-format --stdout build/<pfad>.gcda` auswerten, danach normal neu bauen und
`build/**/*.gcda`,`*.gcno` löschen.
