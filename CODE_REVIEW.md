# CAMotics — Code-Review & Testabdeckungs-Analyse

**Datum:** 2026-06-21
**Umfang:** Gesamter eigener Quellcode (`src/`, ~46.800 LOC ohne gebündelte Fremdbibliotheken clipper/dxflib/cairo)
**Methodik:** Modulweiser Review (G-code-Engine, Simulation/Rendering, GUI, Sprach-Bindings/IO) plus strukturelle Testabdeckungs-Analyse. Build und Testsuite wurden zuvor erfolgreich ausgeführt (25/25 Tests grün).

---

## 1. Management Summary

CAMotics ist eine ausgereifte, funktional reichhaltige CNC-Simulationssoftware. Die Architektur ist sauber geschichtet (G-code → Planung → Simulation → Rendering → GUI), die Nebenläufigkeit der Voxel-Berechnung ist solide entworfen, und das Worker→GUI-Threading-Muster ist korrekt umgesetzt.

Der Review fördert jedoch eine Reihe **konkreter Korrektheits- und Robustheitsdefekte** zutage, die teils zu stillen Fehlsimulationen, teils zu Abstürzen oder Hängern bei ungewöhnlichen Eingaben führen. Schwerpunkte:

- **Stille Fehlsimulation:** Ein unsigned-Truncation-Bug lässt den Materialabtrag für kleine Werkzeuge komplett ausfallen (`Sweep.cpp`); Division-durch-Null im G-code-Evaluator liefert stillschweigend `0` statt Fehler.
- **Robustheit gegenüber nicht vertrauenswürdigen Eingaben:** STL-/DXF-Parser und das `.camotics`-Projektformat validieren Eingaben unzureichend (DoS durch Riesen-Allokationen, Endlosschleifen, Pfad-Traversal, mögliches XXE).
- **Speicher-/Referenzfehler in den Python-Bindings:** mehrere Referenzlecks und eine Rule-of-Three-Verletzung (`PyPtr`) mit Potenzial für Use-after-free.
- **Ein benutzergetriebenes Speicherleck in der GUI** (Qt-Modell bei jedem Fenster-Resize).

**Die mit Abstand größte Schwäche ist die Testabdeckung** (siehe Abschnitt 4): Das Herzstück — die Simulations-Engine — wird von **keinem einzigen automatisierten Test** berührt. Die 25 vorhandenen Tests decken nur 2 der 6 Programme und ~5 % der G/M-Code-Tabelle ab.

### Befundübersicht nach Schweregrad

| Schweregrad | Anzahl | Kernrisiko |
|-------------|:------:|------------|
| KRITISCH    | 2      | Stille Fehlsimulation, Doppel-DECREF (Use-after-free) |
| HOCH        | 9      | Tote Schutzabfragen, DoS-Hänger, Referenzlecks, Dangling-Daten, GUI-Leak |
| MITTEL      | 21     | Numerische Robustheit, fehlende Validierung, Ressourcenlecks, XXE/Pfad-Traversal |
| NIEDRIG     | 14     | Toter Code, veraltete APIs, Wartbarkeit |

---

## 2. Kritische Befunde (sofort beheben)

### K-1 — Materialabtrag fällt für kleine Werkzeuge still aus
**`src/camotics/sim/Sweep.cpp:33-35`** — KRITISCH

```cpp
const unsigned maxLen = radius * 16;   // <-- Trunkierung auf unsigned
```
Für Werkzeuge mit Radius < 1/16 Einheit (häufig bei Zoll-Einheiten oder Graviersticheln) wird `maxLen == 0`. Dann ergibt `steps = len / maxLen` eine Division durch 0 → `inf`, dessen Cast nach `unsigned` UB ist (praktisch `steps = 0`). Die BBox-Schleife läuft nie → der **komplette Sweep dieses Moves wird stillschweigend verworfen**: fehlender Materialabtrag, ohne jede Fehlermeldung.

**Fix:** `double maxLen = radius * 16;`, `radius > 0` sicherstellen, `steps = (maxLen <= 0 || len <= maxLen) ? 1 : (unsigned)ceil(len / maxLen);`

### K-2 — `PyPtr` verletzt Rule-of-Three → Doppel-DECREF / Use-after-free
**`src/python/PyPtr.h:26-45`** — KRITISCH

Die Klasse definiert Destruktor (`Py_DECREF`) und Copy-Assignment (mit `Py_INCREF`), aber **keinen Copy-Konstruktor**. Der implizit generierte kopiert `ptr` ohne `Py_INCREF`; beide Objekte rufen im Destruktor `Py_DECREF` → Referenzzähler-Unterlauf bis hin zu Use-after-free. `PyPtr` wird als Member in `PyTask`/`Runner` gehalten und kopiert.

**Fix:** `PyPtr(const PyPtr &o) : ptr(o.ptr) { if (ptr) Py_INCREF(ptr); }` ergänzen (Move-Ctor erwägen).

---

## 3. Befunde nach Modul

### 3.1 G-code-Engine (`src/gcode`, 14.8k LOC)

| ID | Schweregrad | Ort | Befund |
|----|-------------|-----|--------|
| G-1 | HOCH | `ControllerImpl.h:161`, `.cpp:740,1084` | `unsigned getCurrentTool() < 0` ist **immer false** → tote „kein Werkzeug"-Schutzabfrage; G43/Radiuskorrektur laufen mit ungültiger Werkzeugnummer weiter. Fix: Rückgabetyp `int`, Sentinel `-1`. |
| G-2 | HOCH | `ControllerImpl.cpp:503,515` | `drill()` liest L als `unsigned` ohne Validierung; negatives L → Milliarden-Iterationen (DoS-Hänger), L=0 → stilles Nicht-Bohren. Fix: als `int` lesen, `>= 1` prüfen. |
| G-3 | HOCH | `interp/Evaluator.cpp:57-61,66-111` | Division/Modulo durch 0 wird nur geloggt und liefert **`0`** → falsche Positionen/Offsets fließen unbemerkt ein. `SQRT(<0)`, `LN(≤0)`, `pow(neg)` erzeugen stilles NaN. Fix: werfen statt 0 zurückgeben; Domain prüfen. |
| G-4 | MITTEL | `ControllerImpl.cpp:71,981` | Block-Variablen werden nicht pro Block zurückgesetzt → ungeschützte `getVar('P'/'R'/'L'/'D'/'H')` liefern veralteten Wert des Vorblocks. Fix: `varValues` in `startBlock()` zurücksetzen. |
| G-5 | MITTEL | `plan/LineCommand.cpp:181-192` | `offset += s.offset;` statt `offset = s.offset;` → falsche Zeit-/Vorschubverteilung bei gemergten Speeds (offset kann > length werden). |
| G-6 | MITTEL | `interp/OCodeInterpreter.cpp:74-78` | Rekursionstiefe wird nur gewarnt (Tiefe 101), nicht begrenzt → Stack-Overflow bei tiefer/rekursiver Subroutine. Fix: bei Maximaltiefe werfen. |
| G-7 | MITTEL | `interp/GCodeInterpreter.cpp:87` | Mögliche End-Iterator-Dereferenzierung in `specialComment` (auslösbar mit Kommentar `(probeopen)`). Fix: `it != end` vor jedem `*it`. |
| G-8 | MITTEL | `parse/Tokenizer.cpp:57-76,93` | `skipWhiteSpace` mitten in `number()` macht aus „1 2 3" → „123"; Klammerkommentare laufen über Zeilenende hinaus (RS-274-widrig), fehlende `)` wird erst bei EOF gemeldet. |
| G-9 | MITTEL | `ControllerImpl.cpp:359-423` | `arc()`: Radius-Format und Vollkreis-Logik an harten Float-Schwellen; instabil bei nahezu kollinearen Punkten / Radius ≈ 0. Fix: degenerierte Fälle abfangen, relative Toleranzen. |
| G-10 | MITTEL | `plan/LinePlanner.cpp:1197-1210` | Junction-Velocity nutzt 9D-Dot-Produkt inkl. Rotations-/Hilfsachsen (eigenes TODO) → falsche Eckgeschwindigkeiten für A/B/C/U/V/W. |
| G-11 | MITTEL | `plan/LinePlanner.cpp:81,381,388` | `1U << config.idBits` ist UB bei `idBits >= 32`; `idBits == 0` → `1U << -1`. Fix: `uint64_t`-Literale, Bereich validieren. |
| G-12 | NIEDRIG | `ControllerImpl.cpp:738-767` | Schneidenradiuskorrektur setzt State (`cutterRadiusComp=true`), wird aber nie auf die Bahn angewandt → stille, falsche Geometrie statt klarer Ablehnung. |
| G-13 | NIEDRIG | `plan/LinePlanner.cpp:330,449,562` | Speicherlecks/`pop_back` auf leerer Liste auf Fehlerpfaden (`THROW` vor `delete lc`). Fix: RAII/SmartPointer, `empty()`-Schutz. |
| G-14 | NIEDRIG | `interp/GCodeInterpreter.cpp:305-307` | `Codes::find(...)` ohne Null-Prüfung vor `activeMotion->priority` (aktuell gedeckt, fragil). |

### 3.2 Simulation, Contour & Rendering (`src/camotics/{sim,contour,render}`, 8.7k LOC)

| ID | Schweregrad | Ort | Befund |
|----|-------------|-----|--------|
| S-1 | **KRITISCH** | `sim/Sweep.cpp:33-35` | siehe **K-1** (Materialabtrag fällt für kleine Werkzeuge aus). |
| S-2 | HOCH | `sim/CutWorkpiece.cpp:34-43` | `isValid()` ist **invertiert** (`if (workpiece.isValid()) return false;`) — zudem toter, nirgends aufgerufener Code. Korrigieren oder entfernen. |
| S-3 | MITTEL | `sim/Simulation.cpp:63-89`, `.h:50-53` | `read()` liest `threads` nicht; `threads`/`resolution`/`time` ohne In-Class-Initializer → nach Deserialisierung uninitialisiert, fließt in `Renderer`. |
| S-4 | MITTEL | `render/Renderer.cpp:61,76` | `threads == 0`: `log(0) = -inf` → NaN/UB, und `while (jobs.size() < threads)` startet nie einen Job → **Endlos-Hänger**. Fix: `threads = std::max(1u, threads);`. |
| S-5 | MITTEL | `contour/CorrectedMC33.cpp:31-46` | `getCenter()`: `/count` ohne `count>0`-Schutz (NaN); 8-Bit-Vertex-Fallnummer als 12-Bit-Kantenmaske missbraucht; `centerComputed` nie gesetzt (Cache wirkungslos). |
| S-6 | MITTEL | `sim/ConicSweep.cpp:65,73`, `sim/SpheroidSweep.cpp:35,62` | Exakte Float-Vergleiche (`epsilon == 0`, `2*radius != length`) → numerische Instabilität bei nahezu vertikalen Bahnen / fast-kugelförmigen Werkzeugen. Fix: Epsilon-Toleranzen. |
| S-7 | MITTEL | `contour/CorrectedMC33Cube.cpp:130,150-180` | Ungeschützte Divisionen und `sqrt(delta<0)` → NaN/inf fließen in MC33-Disambiguierung → falsche Topologie. |
| S-8 | MITTEL | `sim/ToolSweep.cpp:111-134` | `depth()` (heißester Pfad) allokiert pro Voxel-Ecke einen `vector` und `sort()`et — dominiert die Laufzeit. Fix: vorsortierte/indizierte Moves, Small-Buffer. |
| S-9 | NIEDRIG | `sim/OctTree.cpp` (ganze Datei) | Toter Code — `OctTree` wird nirgends instanziiert (MoveLookup ist durchgängig `AABBTree`). Entfernen. |
| S-10 | NIEDRIG | `sim/AABB.cpp:31-122` | Rein rekursiver Baumaufbau/-traversierung → tiefe Rekursion bei vielen Moves; `intersects()`/`collisions()` nicht const. |
| S-11 | NIEDRIG | `sim/Workpiece.cpp:28-32` | Member `center`/`halfDim2` berechnet, aber nie verwendet (toter Zustand). |
| S-12 | NIEDRIG | `render/Renderer.cpp:101` | Unsigned-Underflow im Fortschrittswert bei transienter Job-Inkonsistenz. Fix: vorzeichenbehaftet/clamp. |
| S-13 | HOCH | `camsim.cpp:134-135` | `bounds = getWorkpiece().getBounds()` wird **vor** `update(*path)` gelesen → bei automatischem Workpiece leere Bounds → „Empty workpiece, nothing to simulate". `camsim` ist damit für reinen G-code/TPL ohne explizite Bounds unbrauchbar. (Nachträglich beim Aufbau der Testinfrastruktur entdeckt.) Fix: Reihenfolge tauschen. |

> **Positiv:** Die Thread-Partitionierung (`tree.partition()` → disjunkte `GridTree`-Teilbäume, nur lesende Auswertung der geteilten `CutWorkpiece`, sauberer Join in `Renderer::render`) ist korrekt und frei von Datenrennen.

### 3.3 GUI: Qt, OpenGL-View, Value-System (`src/camotics/{qt,view,value,machine}`, 14.7k LOC)

| ID | Schweregrad | Ort | Befund |
|----|-------------|-----|--------|
| U-1 | **HOCH** | `qt/QtWin.cpp:1411,1242,1930` | `setModel(new QStringListModel(...))` ohne Ownership-Übergabe; per `resizeEvent → updateToolTables()` **leakt bei jedem Fenster-Resize** ein Modell. Fix: Modell mit Parent / persistentes Member-Modell, altes löschen; nicht im resizeEvent neu bauen. |
| U-2 | HOCH | `qt/BBCtrlAPI.cpp:43-45`, `.h:42-43` | Uninitialisierte Member `lastMessage`, `useSystemProxy` → UB beim ersten `reconnect()`/Upload. Fix: in Initialisierungsliste. |
| U-3 | HOCH | `qt/BBCtrlAPI.cpp:104,123` | `QByteArray::fromRawData` kopiert nicht; asynchroner PUT liest später ggf. freigegebenen/überschriebenen `gcode`-Puffer (Dangling). Fix: kopierendes `QByteArray(data, length)`. |
| U-4 | HOCH | `value/VarValue.h:30`, `MemberFunctorObserver.h:30`, `qt/QtWin.h:111-114` | Value/Observer-System hält rohe Referenzen/Zeiger auf Member ohne Deregistrierung; `view` wird vor `valueSet` zerstört → `valueSet` referenziert zerstörtes Objekt. Nur durch Zerstörungsreihenfolge „zufällig" sicher. Fix: Deregistrierung / weak_ptr. |
| U-5 | MITTEL | `view/View.cpp:297-319`, `view/GLScene.cpp:45` | `glInit()` nicht idempotent — bei Kontextverlust/Reparenting doppelte Szenenobjekte + geleaktes `GLProgram`/VBOs. |
| U-6 | MITTEL | `view/GLProgram.cpp:41-45`, `view/VBO.cpp:27-32` | Destruktoren überspringen GL-Freigabe ohne aktiven Kontext → GPU-Ressourcenleck bei wiederholtem Projekt-/Modellwechsel. |
| U-7 | MITTEL | `qt/BBCtrlAPI.cpp:109,157-191,203` | Adresse ungeprüft per String-Konkatenation in URLs (kein Escaping/TLS/Auth); `line - 1` (uint32) Underflow bei `ln==0`; ungeprüfte Netzwerk-JSON-Felder. |
| U-8 | MITTEL | `qt/BBCtrlAPI.cpp:87-91,146-154` | Unbegrenzte Reconnect-Schleife ohne Backoff-Obergrenze/Abbruch; `.local`-Trim verändert Adresse dauerhaft. |
| U-9 | MITTEL | `qt/QtWin.cpp` (2535 Z.) | Übergroße Klasse; ~30 `update*`-Einzeiler, 4 identische `on_action*Surface`, 6 Spinbox-Handler = Copy-Paste. Fix: datengetriebene Tabellen. |
| U-10 | MITTEL | `qt/QtWin.cpp:300,1409,1785…` | Flächendeckend veraltetes `QString::sprintf` (in Qt6 entfernt, nicht typsicher). Fix: `arg`/`number`/`asprintf`. |
| U-11 | NIEDRIG | `qt/QtWin.cpp:177,185,496,1661-1672` | `QMenu`/`QMovie` ohne Parent + manuelles `delete` (fragile Ownership). |
| U-12 | NIEDRIG | `view/GLProgram.cpp:119-128` | `getUniform` wirft bei wegoptimiertem Uniform → kann gesamtes Zeichnen abbrechen. Fix: fehlende Uniforms tolerieren. |
| U-13 | NIEDRIG | `qt/GLView.cpp:31,98` | Veraltete Qt-APIs (`QGLFormat`, `event->delta()`). Fix: `QSurfaceFormat`, `angleDelta()`. |
| U-14 | NIEDRIG | `qt/QtWin.cpp:895-907` | `redraw()`-Drosselung kann finalen Frame verschlucken (implizite Timer-Kopplung). |

> **Positiv:** Worker→GUI-Kommunikation über `postEvent` ist thread-sicher; WebSocket-Slots laufen im GUI-Thread. Keine GUI-Race-Conditions gefunden.

### 3.4 Sprach-Bindings & I/O (`src/{tplang,python,stl,dxf}`, `src/camotics/{project,probe,opt}`, ~6.7k LOC)

| ID | Schweregrad | Ort | Befund |
|----|-------------|-----|--------|
| L-1 | **KRITISCH** | `python/PyPtr.h:26-45` | siehe **K-2** (Rule-of-Three → Doppel-DECREF). |
| L-2 | HOCH | `python/PyJSON.cpp:47,63,76,80` | Mehrere Referenzlecks: `PySequence_GetItem`/`PyObject_Str`/`PyObject_ASCII` liefern neue Referenzen, die nie freigegeben werden; skaliert mit Datenmenge. Fix: `Py_DECREF`/`PyPtr`. |
| L-3 | HOCH | `python/PySimulation.cpp:90-93,351,479` | `new Runner(...)` startet Thread im Konstruktor, *bevor* `set_task()` „Task aktiv" prüft → laufender Runner wird geworfen, nie gejoint → Thread-Leak. Fix: Prüfung vor Erzeugung. |
| L-4 | MITTEL | `dxf/Reader.cpp:92-111` | `addVertex`/`addControlPoint`/`addKnot` dereferenzieren `entity` ohne Null-Prüfung → manipulierte DXF (VERTEX ohne POLYLINE) wirft `referenceError`. Fix: Null-Prüfung mit klarer Meldung. |
| L-5 | MITTEL | `stl/Reader.cpp:38-115` | Untrusted STL: `read()` ohne `gcount()`-Prüfung; angreiferkontrolliertes `count` ohne Plausibilisierung gegen Dateigröße; fragile ASCII/Binär-Heuristik (`"solid "`); Endianness ignoriert. |
| L-6 | MITTEL | `opt/Opt.cpp:209`, `opt/AnnealState.cpp:75` | Entarteter Pfad (0 Cuts): `rand() % index.size()` (Modulo 0) bzw. `index.size()-1` (unsigned Underflow) → Crash/UB. Fix: `if (paths.size() < 2) return;`. |
| L-7 | MITTEL | `project/Files.cpp:53-61` | `.camotics`-Datei-Referenzen erlauben absolute Pfade / `../` ohne Sandbox; geladene TPL führt beliebiges JS aus → bösartiges Projekt = Code-Ausführung/Dateizugriff außerhalb Projektordner. |
| L-8 | MITTEL | `project/Project.cpp:109-119` | `resolution` ungeprüft (0/negativ akzeptiert) → Division durch 0 bzw. exzessive Voxel-Allokation (DoS). Fix: `> 0` + Obergrenze. |
| L-9 | MITTEL | `project/XMLHandler.cpp:34` | `i < filename.size() - 2` unterläuft (size_t) bei `filename.size() < 2` → `substr`/`parseU8` wirft. Fix: `i + 2 < size()`. |
| L-10 | MITTEL | `project/Project.cpp:149` (cb::XML::Reader) | Mögliches **XXE** bei untrusted `.camotics`/`.xml` — externe Entity-/DTD-Auflösung im cbang-XML-Reader nicht verifiziert. Prüfen/deaktivieren. |
| L-11 | NIEDRIG | `tplang/MatrixModule.cpp:106-112` | Negativer Matrix-Index nicht geprüft (`getInteger` liefert `int`, nur Obergrenze geprüft) → Out-of-Range-Zugriff. |
| L-12 | NIEDRIG | `python/PyNameResolver.cpp:27-30` | `Py_INCREF` vor `PyCallable_Check` → Leck bei Wurf; `PyTuple_SetItem` ohne NULL-Schutz. |
| L-13 | NIEDRIG | `python/Catch.h:24-31` | `PyErr_SetString` überschreibt präzisere bestehende Python-Exception. Fix: nur bei `!PyErr_Occurred()`. |
| L-14 | NIEDRIG | `tplang/ClipperModule.cpp:59,64,71` | Integer-Überlauf bei `coord * scale` (1e6) → fehlerhafte Geometrie bei großen JS-Koordinaten. |
| L-15 | NIEDRIG | `project/XMLHandler.cpp:46,139` | `currentTool` wird nie gesetzt → `<tool>`-Beschreibungen aus XML-Projekten werden nie eingelesen (Funktionsdefekt). |

---

## 4. Testabdeckungs-Analyse

### 4.1 Was vorhanden ist

Es existieren **25 Integrationstests** (Golden-File-basiert, cbang-`testHarness`), verteilt auf 4 Suiten. **Unit-Tests existieren nicht.** Alle Tests sind reine stdin→stdout/stderr/return-Vergleiche.

| Suite | Tests | Getriebenes Binary | Getestete Funktionalität |
|-------|:-----:|--------------------|--------------------------|
| `tplTests` | 10 | `tplang` | TPL/JS: arc, cut, rapid, rotate, square(s), require, DXF-Laden |
| `offsetTests` | 8 | `gcodetool` | Koordinatensysteme & Werkzeug-Offsets (G10/G52/G53/G92) |
| `varRefTests` | 6 | `gcodetool` | G-code-Variablenreferenzen (numerisch/benannt, lokal/global) |
| `oCodeTests` | 1 | `gcodetool` | O-code-Kontrollfluss (else/if) |

### 4.2 Strukturelle Abdeckung — die Lücke

Die Tests treiben nur **2 der 6 Programme** (`gcodetool`, `tplang`). Damit ergibt sich folgende Modulabdeckung:

| Modul | LOC | Testabdeckung |
|-------|----:|---------------|
| `gcode/` (parse, interp, machine) | ~14.8k | 🟡 **teilweise** — nur über `gcodetool`, ~5 % der Code-Tabelle (s. u.) |
| `tplang/` | ~1.7k | 🟡 **teilweise** — Grundfunktionen über `tplTests` |
| `dxf/`, `clipper/` | — | 🟡 **indirekt** — nur über `tplTests/DXFTest` bzw. Clipper-Nutzung |
| **`camotics/sim/`** (Simulations-Kern) | **2.4k** | 🔴 **KEINE** |
| **`camotics/contour/`** (Marching Cubes) | **6.0k** | 🔴 **KEINE** |
| `camotics/render/` | 0.3k | 🔴 **KEINE** |
| `camotics/opt/` (Optimierung) | 0.6k | 🔴 **KEINE** |
| `camotics/probe/` | 0.5k | 🔴 **KEINE** |
| `camotics/project/` (IO/Serialisierung) | 1.0k | 🔴 **KEINE** |
| `stl/` (STL-Parser) | 0.6k | 🔴 **KEINE** |
| `python/` (Bindings) | 1.9k | 🔴 **KEINE** |
| `camotics/{qt,view,value,machine}/` (GUI) | ~14.7k | 🔴 **KEINE** (bei GUI vertretbar) |
| `planner`, `camsim` (Binaries) | — | 🔴 **KEINE** |

**Schätzung der effektiv getesteten eigenen Code-Basis: < 20 %.** Die für die Kernaufgabe „Simulation" zentralen Module `sim/` und `contour/` (zusammen 8,4k LOC) haben **null** automatisierte Abdeckung — genau dort liegen auch zwei der schwersten Befunde (K-1, S-4).

### 4.3 Funktionale Abdeckung der G-code-Tabelle

Die G/M-Code-Tabelle (`Codes.cpp`) enthält **225 Einträge**. In sämtlichen Test-Inputs kommen jedoch nur folgende **12 Codes** vor:

```
G0  G10  G21  G43  G52  G53  G55  G92  G92.1  G92.2  G92.3  M6
```

Das sind **~5 %**. Ganze Funktionsklassen sind ungetestet: Bögen (G2/G3), Bohrzyklen (G81–G89), Cutter-Compensation (G40–G42 — ohnehin nur teilimplementiert, s. G-12), Ebenen (G17–G19), Spindel/Kühlung (M3–M9), Dwell, Splines (G5), Einheiten-Umschaltung im Lauf.

### 4.4 Echte Code-Coverage-Messung

Eine instrumentierte gcov/lcov-Messung wurde **nicht** durchgeführt (erfordert Neukompilierung von CAMotics **und** cbang mit `--coverage`). Für diese Codebasis ist die strukturelle Analyse aber bereits aussagekräftig: Da ganze Binaries und Module von keinem Test angesprochen werden, würde eine Zeilen-Coverage-Messung die obigen 🔴-Module zwangsläufig nahe 0 % ausweisen.

---

## 5. Empfehlungen (priorisiert)

### Sofort (Korrektheit/Sicherheit)
1. **K-1 / S-1** fixen — `Sweep.cpp` unsigned-Truncation. Direkter Einfluss auf Simulationskorrektheit.
2. **K-2 / L-1** fixen — `PyPtr` Copy-Konstruktor. Speichersicherheit der Python-Bindings.
3. **G-1, G-2, G-3** fixen — tote Werkzeug-Schutzabfrage, `drill()`-DoS, Division-durch-0-im-Evaluator.
4. **U-3, U-2** fixen — BBCtrlAPI Dangling-Daten & uninitialisierte Member.

### Kurzfristig (Robustheit gegen Eingaben)
5. Eingabevalidierung härten: **L-5** (STL), **L-4** (DXF), **L-8/L-9/L-10** (Projekt/XML/XXE), **L-7** (Pfad-Sandbox). CAMotics lädt nutzergelieferte Dateien — diese Parser sind die primäre Angriffsfläche.
6. **S-3/S-4** (Renderer-Hänger bei `threads==0`), **U-1** (GUI-Resize-Leak).

### Testabdeckung (strukturell wichtigste Maßnahme)
7. **Golden-File-Tests für die Simulations-Engine** aufsetzen: `camsim` über kleine, deterministische G-code-Programme laufen lassen und ein Mesh-/Volumen-Maß (Dreieckszahl, Volumen, Bounding-Box-Hash) gegen Referenzwerte prüfen. Das schließt die größte Lücke (`sim/`, `contour/`) mit dem vorhandenen `testHarness`-Mechanismus.
8. **`planner`-Tests** analog zu `gcodetool` ergänzen (Motion-Planning ist ungetestet, enthält aber G-5/G-10/G-11).
9. **G-code-Funktionsabdeckung** erhöhen: gezielt Tests für Bögen, Bohrzyklen, Ebenenwahl, Dwell und Einheiten-Umschaltung — die häufigsten realen G-codes.
10. **Regressionstests aus Bugs ableiten:** Für K-1 ein Test mit Kleinst-Werkzeug; für L-6 ein Pfad mit 0 Cuts; für G-2 ein `drill` mit L=0 — so wird jeder Fix dauerhaft abgesichert.

### Mittelfristig (Wartbarkeit)
11. Toten Code entfernen (`sim/OctTree.cpp`, `Workpiece`-Member, `CutWorkpiece::isValid`).
12. Veraltete Qt-APIs migrieren (`QString::sprintf`, `QGLFormat`, `event->delta()`) — Voraussetzung für eine spätere Qt6-Portierung.
13. `QtWin` entflechten (datengetriebene Observer-/Surface-/Spinbox-Behandlung statt Copy-Paste).

---

*Hinweis: Die gebündelten Fremdbibliotheken `src/clipper`, `src/dxflib` und `src/cairo` (~26k LOC) waren nicht Gegenstand dieses Reviews, da sie als externe Abhängigkeiten gepflegt werden.*
