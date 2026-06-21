# P3 — Simulation / Contour / Render: Fixes + Tests

**Ziel:** Den kritischen Simulations-Bug (K-1) und die Robustheits-/Numerikdefekte in
`sim/`, `contour/`, `render/` beheben — verifiziert über den in P1 geschaffenen
Sim-Test-Harness.

**Status:** ⬜ offen · **Befunde:** S-1…S-12 (Details siehe `CODE_REVIEW.md` §3.2)
**Abhängigkeit:** P1 (Sim-Harness muss stehen).

---

## Fixes (priorisiert)

| ID | Schweregrad | Datei:Zeile | Fix-Kern |
|----|-------------|-------------|----------|
| S-1 (**K-1**) | **KRITISCH** | `sim/Sweep.cpp:33-35` | `double maxLen = radius * 16;`, `radius > 0` sicherstellen, `steps = (maxLen <= 0 \|\| len <= maxLen) ? 1 : ceil(len/maxLen)`. |
| S-2 | HOCH | `sim/CutWorkpiece.cpp:34-43` | `isValid()`-Logik korrigieren oder toten Code entfernen. |
| S-3 | MITTEL | `sim/Simulation.cpp:63-89`, `.h:50-53` | `threads` in `read()` lesen; In-Class-Initializer für `threads/resolution/time`. |
| S-4 | MITTEL | `render/Renderer.cpp:61,76` | `threads = std::max(1u, threads);` am Methodenanfang. |
| S-5 | MITTEL | `contour/CorrectedMC33.cpp:31-46` | `count>0`-Schutz; korrekte Aktiv-Kanten-Maske; `centerComputed` setzen. |
| S-6 | MITTEL | `sim/ConicSweep.cpp:65,73`, `sim/SpheroidSweep.cpp:35,62` | Epsilon-Toleranzen statt exakter Float-Vergleiche. |
| S-7 | MITTEL | `contour/CorrectedMC33Cube.cpp:130,150-180` | Nenner/Diskriminante auf ~0 prüfen, definierter Fallback. |
| S-8 | MITTEL | `sim/ToolSweep.cpp:111-134` | `depth()`-Hot-Path: Heap-`vector`/`sort` pro Voxel-Ecke vermeiden (vorsortiert/Small-Buffer). |
| S-9 | NIEDRIG | `sim/OctTree.cpp` | Toten Code entfernen (→ ggf. nach P6 verschieben). |
| S-10 | NIEDRIG | `sim/AABB.cpp:31-122` | Rekursionstiefe begrenzen; Methoden `const`. |
| S-11 | NIEDRIG | `sim/Workpiece.cpp:28-32` | Ungenutzte Member entfernen. |
| S-12 | NIEDRIG | `render/Renderer.cpp:101` | Unsigned-Underflow im Fortschritt vermeiden (signed/clamp). |
| S-13 | HOCH | `camsim.cpp:134-135` | `bounds` wird VOR `update(*path)` gelesen → bei automatischem Workpiece leere Bounds → „Empty workpiece, nothing to simulate". Macht `camsim` für reinen G-code/TPL ohne explizite Bounds unbrauchbar. **Während P1 entdeckt.** Fix: Reihenfolge tauschen (erst `update`, dann `getBounds`). |

> **S-13 / Test-Vereinfachung:** Sobald S-13 behoben ist, können die `simTests` auf reine
> G-code-Inputs mit automatischem Workpiece umgestellt werden (statt `.camotics`-Projekten
> mit festen Bounds). Bis dahin nutzen die Tests feste Bounds — siehe `tests/README.md`.

## Tests (verzahnt)

- **S-1 / K-1:** `SmallToolTest` aus P1 aktivieren — muss nach dem Fix korrektes,
  nicht-leeres Mesh liefern (Kennzahlen > 0). Vor dem Fix dokumentiert fehlerhaft.
- **S-4:** Sim-Test mit `--threads 0` → darf nicht hängen, muss korrektes Ergebnis
  liefern (Harness mit Timeout absichern).
- **S-2:** Falls `isValid()` reaktiviert wird, gezielter Unit-artiger Test über `camsim`.
- **S-6:** Sim-Test mit nahezu vertikaler Werkzeugbahn (Conic/Spheroid-Sonderfall) →
  stabile Oberfläche statt NaN/Artefakt.
- **Regressionsschutz:** Die in P1 angelegten `BoxMill/Drill/ArcMill`-Kennzahlen dürfen
  sich durch die Numerik-Fixes nur erwartungsgemäß ändern (Golden ggf. bewusst neu setzen,
  Änderung im Status begründen).

## Abnahmekriterien

- [ ] K-1 behoben und durch `SmallToolTest` belegt (grün).
- [ ] Kein Hänger bei `threads==0` (Test mit Timeout grün).
- [ ] Alle S-Befunde behoben oder explizit nach P6 verschoben (toter Code).
- [ ] Build grün; alle Sim- und Bestandstests grün.

## Risiken

- S-5/S-7 (Marching-Cubes-Numerik) können die erzeugte Oberfläche verändern → Kennzahl-
  Goldens der Sim-Tests genau prüfen; Änderungen visuell/numerisch plausibilisieren.
- S-8 (Hot-Path-Umbau) ist eine Performance-Optimierung mit Korrektheitsrisiko → nur mit
  Kennzahl-Gleichheit vorher/nachher mergen; sonst zurückstellen.
