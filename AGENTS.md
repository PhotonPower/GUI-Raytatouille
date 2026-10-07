# Regeln für Programmieragenten

Diese Datei liest jeder Agent zu Beginn jeder Sitzung. Sie gilt zusammen mit
`docs/architektur.md` und `docs/adr/`.

## Projekt in einem Satz

Der Raytatouille Explorer ist eine Streamlit-Oberfläche auf der öffentlichen Python-API der
Bibliothek [Raytatouille](https://github.com/PhotonPower/Raytatouille); er ist ein
Erkundungswerkzeug, nicht die M10-GUI (ADR 0001).

## Bauen und testen

```bash
pip install -e ".[dev]"                   # plus raytatouille, siehe docs/installation.md
export RTT_REPO=/pfad/zu/Raytatouille
ruff check .
pytest -m "not library"                   # reine Logik
pytest                                    # alles, inklusive App-Rauchtests
streamlit run streamlit_app.py
```

## Arbeitsregeln

1. **Ein Auftrag = ein Ziel.** Nichts darüber hinaus bauen.
2. **Erst Test, dann Code.** Neue Logik bekommt einen Test, der vorher fehlschlägt. Bestehende Tests
   nur mit Freigabe des Maintainers ändern; einen Test anzupassen, damit er grün wird, ist verboten.
3. **Reine Logik gehört in reine Module** (ohne `streamlit`, ohne `raytatouille`). Streamlit-Aufrufe
   nur in `ui/` und `views/`.
4. **Nur öffentliche API von raytatouille** (ADR 0002). Fehlt etwas, Issue in der Bibliothek
   beschreiben statt umgehen. Die Bibliothek wird von hier aus nicht geändert.
5. **Optionale Funktionen über `compat.Features`** abfragen und fehlende erklären, nie abstürzen.
6. **Fehler der Bibliothek als Meldung zeigen**, nicht als Traceback (`ui.common.run`).
7. **Physik mit Quelle:** Die Berechnung liegt in der Bibliothek. Zeigt der Explorer eine eigene
   Anzeigegröße (Strehl, Airy-Radius), muss sie als Näherung gekennzeichnet sein und die Formel im
   Kommentar stehen.
8. **Determinismus:** Zufall nur mit festem Seed.
9. **Unklarheit = Frage, nicht Annahme.** Bei widersprüchlichen Vorgaben oder offenen
   Konventionen ein Issue stellen und auf Antwort warten.
10. **Widget-Schlüssel und `session_state`-Namen nicht umbenennen**, ohne `docs/architektur.md` und
    die Rauchtests anzupassen.

## Sprache und Stil

- Code, Kommentare, Commit-Messages und Bezeichner auf Englisch; Oberfläche und Projektdokumentation
  auf Deutsch.
- Stil: `ruff` (Konfiguration in `pyproject.toml`, 120 Spalten).
- Commits im Imperativ, ein Thema pro Commit, z. B. `views: add footprint view`.

## Definition of Done (PR-Checkliste)

- [ ] CI grün
- [ ] Test für neue Logik; Rauchtest für neue oder geänderte Ansicht
- [ ] Optionale Bibliotheksfunktionen über `Features` abgefangen
- [ ] `docs/bedienung.md` angepasst, wenn sich die Bedienung ändert
- [ ] `CHANGELOG.md` ergänzt
- [ ] Bei neuer Architekturentscheidung: ADR
