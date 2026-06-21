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
| `simTests` | `camsim` | End-to-End-Simulation (STL-Kennzahlen) |

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
analog zu den `gcodetool`-Suiten: `data/stdin` + `expect/{stdout,stderr,return}`.
