# Entwicklung

## Einrichten

```bash
python -m venv .venv && source .venv/bin/activate
pip install "./pfad/zu/Raytatouille[plot]"     # siehe installation.md
pip install -e ".[dev]"
export RTT_REPO=/pfad/zu/Raytatouille           # Beispielsysteme und Kataloge
```

## Prüfen

```bash
ruff check .                  # Lint und Importreihenfolge
pytest -m "not library"       # reine Logik, in Sekunden, ohne Bibliothek
pytest                        # zusätzlich die App-Rauchtests (brauchen Bibliothek und RTT_REPO)
```

Tests mit der Markierung `library` werden automatisch übersprungen, wenn `raytatouille` oder das
Repo fehlt (`tests/conftest.py`). Die Rauchtests starten die ganze App mit
`streamlit.testing.v1.AppTest` und prüfen, dass keine Exception und keine Fehlermeldung auftritt und
dass Kennwerte stimmen (z. B. f/# und EFL des Cooke-Triplets, EFL des Plankonvex-Singlets).

`AppTest` sieht keine Grafiken. Änderungen an Zeichnungen deshalb einmal von Hand ansehen oder
`scripts/render_example_figures.py` ausführen (braucht eine Bibliothek mit `layout`).

## Regeln

- Code, Kommentare, Commits und Bezeichner auf Englisch; Oberfläche und Projektdokumentation auf
  Deutsch.
- Reine Logik in reine Module, Streamlit-Aufrufe nur in `ui/` und `views/`.
- Fehler der Bibliothek (`rt.RaytatouilleError`, `ValueError`) als lesbare Meldung zeigen, nie als
  Traceback (Hilfsfunktion `ui.common.run`).
- Zufall nur mit festem Seed, damit Ansichten reproduzierbar bleiben.
- Commits im Imperativ, ein Thema pro Commit, z. B. `views: add through-focus spot`.

## Release

1. `__version__` in `src/rtt_explorer/__init__.py` erhöhen (SemVer).
2. `CHANGELOG.md`: Abschnitt `[Unreleased]` in die neue Version umbenennen.
3. Tag `vX.Y.Z` setzen und pushen.
