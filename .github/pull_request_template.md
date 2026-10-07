## Was und warum

Closes #

## Checkliste (AGENTS.md, Definition of Done)

- [ ] CI grün (Lint, Unit-Tests, Bibliothekstest)
- [ ] Neue Logik liegt in einem reinen Modul (ohne Streamlit-Aufrufe) und hat einen Test
- [ ] Neue oder geänderte Ansicht: Rauchtest in `tests/test_app.py`
- [ ] Nur öffentliche API von `raytatouille` verwendet; fehlende Funktionen über `Features` abgefangen
- [ ] Bedienung geändert: `docs/bedienung.md` angepasst
- [ ] `CHANGELOG.md` ergänzt
- [ ] Bei neuer Architekturentscheidung: ADR unter `docs/adr/`
