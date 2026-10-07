# Changelog

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/); Versionen nach SemVer.

## [Unreleased]

## [0.1.0] – Erste Veröffentlichung

### Hinzugefügt
- Paket `rtt_explorer` mit Befehl `rtt-explorer` und `streamlit_app.py`; aus dem Prototyp
  `rtt_explorer.py` in Module zerlegt (ADR 0003), Verhalten unverändert.
- Ansichten: Layout, Spot, Ray Fans, OPD / Wellenfront, Verzeichnung & Feldkrümmung, Farbfehler,
  Seidel, Strahlenbündel, Polarisation, Materialien, System-Datei.
- Systemquellen: Referenzsysteme, Upload, Baukasten mit Flächentabelle und Vorlagen.
- Funktionserkennung für optionale Funktionen der Bibliothek (ADR 0005).
- Tests: Unit-Tests der reinen Logik und App-Rauchtests mit `AppTest`.
- CI mit Lint, Unit-Tests (Python 3.10 und 3.12) und Bibliothekstest mit gebauter Raytatouille.
- Dokumentation unter `docs/` und Architekturentscheidungen.
