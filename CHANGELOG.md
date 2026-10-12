# Changelog

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/); Versionen nach SemVer.

## [Unreleased]

Angepasst an Raytatouille 0.7.0 (Tag `v0.7.0`, Commit `41fff00`).

### Hinzugefügt (0.7.0)
- **Konfigurationen:** Auswahl in der Seitenleiste für Systeme mit Parametertabelle (z. B. `m5/zoom`);
  kompiliert die gewählte Spalte, auch für die Ghost-Analyse. Die Ansicht System-Datei speichert die
  Konfiguration mit festen Werten (`System.resolved`).
- Ansicht **Optimierung** (M5): Merit-Funktion mit Startwerten, Variablen mit Grenzen, Optionen des
  Levenberg-Marquardt-Optimierers, Lauf mit Status, Verlauf, Variablen vorher/nachher und Beiträgen;
  Ergebnis übernehmen (alle Ansichten zeigen dann das optimierte System), als `.rtt.json`, JSON Patch
  oder Ergebnis-JSON speichern.
- Ansicht **Reports**: Abmessungen (Mitten- und Randdicke, Durchmesser), Systemdaten und Raytrace mit
  lokalen Koordinaten, jeweils als CSV und JSON.
- Strahlenbündel: Pupillenraster „Gauß-Quadratur“ mit den Quadraturgewichten in der CSV.
- Funktionsflags `configs`, `optim`, `reports` und `gauss`.

### Hinzugefügt (0.6.0)
- Ansicht **Prescription** (G5): paraxialer Rand- und Hauptstrahl je Fläche, Baulänge, Arbeitsblende,
  Bild-NA und Lagrange-Invariante; Export als CSV und JSON.
- Ansicht **Pfade & Ghosts**: Transmission je Pfad, optische Wegdifferenz zweier Pfade (z. B.
  Michelson) und Ghost-Ranking der Zwei-Reflexions-Ghosts. Systeme ohne Blende laufen mit dem freien
  kollimierten Bündel.
- Ansicht **Modell** (G3, nur lesen): Flächentabelle aus dem Modellbaum mit Baugruppen, Material,
  Form, Apertur, Wechselwirkung und Phase, dazu Pfade, Parametertabelle und Konfigurationen.
- Warnungen der Bibliothek erscheinen mit Diagnosecode und Flächenname (G10): beim Laden der
  Kataloge, beim Kompilieren und bei Spot, Ray Fans und OPD. Diese Ansichten zeigen außerdem die
  verlorenen Strahlen je Status mit der Fläche der meisten Verluste und bieten das Ergebnis als
  JSON an (Format `raytatouille-result`).
- Funktionsflags `diagnostics`, `prescription`, `model`, `path_eval`, `ghosts` und `results`.
- Windows-Bauanleitung der Bibliothek in `docs/installation.md`.

### Behoben
- Unter Windows startete die App mit `m0/feature_tour` statt mit dem Cooke-Triplet, weil die
  Beispielsystem-Labels dort Backslashes enthalten.

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
