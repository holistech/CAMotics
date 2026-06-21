# P1 — Test-Infrastruktur & Simulations-Harness

**Ziel:** Fundament schaffen, um die heute ungetesteten Binaries (`camsim`, `planner`)
automatisiert und deterministisch zu testen. Voraussetzung für die Verifikation der
Simulations-Fixes in P3.

**Status:** ⬜ offen

---

## Hintergrund

- `tests/testHarness` (cbang, Python) führt pro Test ein `command` aus und vergleicht
  `stdout`/`stderr`/`return` gegen Golden-Files in `expect/`. Eingabe via `data/stdin`.
- `camsim <input.gcode|tpl|camotics> <output.stl>` erzeugt eine STL-Datei. Optionen:
  `--binary 0` (ASCII-STL), `--threads N`, `--resolution low|medium|high|<dezimal>`,
  `--time`, `--reduce`, `--render-mode`.
- Direktes STL-Byte-Diffing ist **nicht** robust: Thread-Partitionierung kann die
  Facetten-Reihenfolge ändern; Floating-Point variiert minimal über Plattformen.
  → Stattdessen **stabile Kennzahlen** vergleichen.

## Umsetzungsschritte

1. **STL-Kennzahl-Extraktor** (`tests/simTests/stl-metrics.py`):
   liest eine (ASCII- oder Binär-)STL und gibt deterministische Kennzahlen nach stdout:
   - Facettenzahl
   - Bounding-Box (auf z. B. 3 Nachkommastellen gerundet)
   - Geschlossenes Volumen (Signed-Volume-Summe der Dreiecke, gerundet)
   - Oberfläche (gerundet)
   Rundung macht den Vergleich robust gegen FP-Rauschen.

2. **Test-Wrapper** (`tests/simTests/run-sim.sh` o. ä.): ruft
   `camsim --threads 1 --binary 0 --resolution <fix> <input> <tmp.stl>` auf, leitet
   `tmp.stl` durch `stl-metrics.py`, schreibt Kennzahlen nach stdout.
   `--threads 1` für Determinismus.

3. **Suite `tests/simTests/test.json`**: `command` = Wrapper. Pro Test ein Verzeichnis
   mit `data/` (G-code-Input) und `expect/{stdout,stderr,return}`.

4. **Initiale Simulations-Tests** (Golden via `testHarness init`):
   - `BoxMillTest` — einfacher rechteckiger Fräspfad, prüft Grund-Materialabtrag.
   - `DrillTest` — Bohrzyklus, prüft zylindrische Abtragung.
   - `ArcMillTest` — Bogenbewegung (G2/G3), prüft gekrümmte Oberfläche.
   - `SmallToolTest` — Werkzeug mit Radius < 1/16 Einheit → **Regressionstest für K-1**
     (dieser Test muss VOR dem Fix fehlschlagen/leeres Mesh zeigen, NACH dem Fix korrekt).

5. **`planner`-Harness** analog zu `gcodetool` (`tests/plannerTests/`): `planner` liest
   G-code von stdin und gibt geplante Moves aus → direkt golden-vergleichbar wie die
   bestehenden `gcodetool`-Suiten. Initiale Tests: einfache Linearbewegung, Vorschub-/
   Eilgang-Übergang, Bogen.

6. **Determinismus-Check:** Jeden neuen Test 3× laufen lassen, sicherstellen, dass die
   Kennzahlen stabil sind, bevor die Golden-Files committet werden.

## Abnahmekriterien

- [ ] `stl-metrics.py` liefert reproduzierbare Kennzahlen.
- [ ] `tests/simTests` mit ≥ 4 Tests, alle grün (außer `SmallToolTest`, der bis P3 als
      bekannter Fehlschlag markiert oder via `disable` geparkt wird).
- [ ] `tests/plannerTests` mit ≥ 3 Tests, alle grün.
- [ ] `./testHarness` aus `tests/` läuft die neuen Suiten mit.
- [ ] Doku in `tests/README` o. ä. wie man Sim-Tests hinzufügt.

## Hinweise

- Falls `testHarness` Positionsargumente/Datei-IO nicht direkt unterstützt, ist der
  Wrapper-Skript-Ansatz (Schritt 2) der robusteste Weg — `command` kapselt den
  camsim-Aufruf vollständig.
- Resolution bewusst grob wählen (wenige Voxel) → kleine STL, schnelle Tests.
