# P6 — Cleanup & finale Verifikation

**Ziel:** Toten Code entfernen, veraltete APIs abschließen, Dokumentation aktualisieren
und die erreichte Testabdeckung mit einer echten gcov/lcov-Messung belegen.

**Status:** ⬜ offen

---

## Aufgaben

1. **Toten Code entfernen** (sofern nicht schon in P3 erledigt):
   - `sim/OctTree.cpp` (S-9) — ungenutzt, falls bestätigt.
   - `sim/Workpiece.cpp` ungenutzte Member (S-11).
   - `sim/CutWorkpiece::isValid` (S-2), falls als toter Code eingestuft.
   - Weitere bei den Fixes entdeckte Leichen.

2. **Veraltete Qt-APIs** abschließen (Rest aus P5, Qt6-Vorbereitung):
   `QString::sprintf`, `QGLFormat`, `event->delta()` flächendeckend prüfen.

3. **Dokumentation aktualisieren:**
   - `CLAUDE.md`: Hinweis auf neue Test-Suiten (`simTests`, `plannerTests`, `stlTests`)
     und wie man sie ausführt/erweitert.
   - `CODE_REVIEW.md`: Befunde als behoben markieren (Querverweis auf Projekte).
   - `tests/README` o. ä.: Anleitung zum Hinzufügen von Sim-/Parser-Tests.

4. **Finale Coverage-Messung (gcov/lcov):**
   - CAMotics **und** cbang mit `--coverage` (`-fprofile-arcs -ftest-coverage`) bauen.
     In SConstruct über eine Build-Variable (z. B. `coverage=1`) zuschaltbar machen.
   - Komplette Testsuite laufen lassen, `lcov`/`genhtml`-Report erzeugen.
   - Zeilen-/Funktions-Coverage pro Modul im Status festhalten (Vorher/Nachher).

5. **Gesamt-Regressionslauf:** `scons -j$(nproc)` + komplette `testHarness`-Suite grün.

## Abnahmekriterien

- [ ] Kein bekannter toter Code mehr (oder bewusst dokumentiert belassen).
- [ ] Doku (CLAUDE.md, CODE_REVIEW.md, Test-README) aktuell.
- [ ] gcov/lcov-Report erzeugt; Coverage-Zahlen pro Modul im Status.
- [ ] Vollständiger Build + alle Tests grün.
- [ ] STATUS.md final: alle Projekte ✅, Befundbilanz vollständig.

## Risiken

- Coverage-Build erfordert instrumentiertes cbang → ggf. separater Build-Baum; falls zu
  aufwändig, mindestens CAMotics-eigene Objekte instrumentieren und die Einschränkung
  dokumentieren.
