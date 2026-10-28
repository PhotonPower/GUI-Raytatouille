# Changelog

Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/); Versionen nach SemVer.

## [Unreleased]

Angepasst an Raytatouille 0.8.0 (Tag `v0.8.0`, Commit `451ab4c`); läuft weiter mit 0.7.0 und älter.

### Hinzugefügt
- Layout: **Bildausschnitt** wählen. Knöpfe „Gesamtes System“, „Auf Quelle zoomen“ (Fenster ± mm um
  den Startpunkt der Strahlen) und „Auf Bildebene zoomen“ (ersetzt den Haken und den Schieberegler)
  sowie ein frei wählbarer Bereich in z und y (bzw. x) in mm.
- Layout: Der Zoom auf die Bildebene bricht nicht mehr mit „Axis limits cannot be NaN or Inf“ ab, wenn
  kein Strahl die Bildebene erreicht (z. B. alle Strahlen an einer Blende verloren); der Knopf ist dann aus.
- Layout: **Alle Pfade zeichnen** bei Systemen mit mehreren Pfaden (Standard an), z. B. beide Arme des
  Michelson-Interferometers; Farbe oder Linienart je Pfad, Pfadnamen in der Legende (#6).
- Layout: Strahlen, die die letzte Fläche eines Pfads verlassen (Spiegel, Totalreflexion), laufen
  blass in ihrer Austrittsrichtung weiter; nicht hinter einem Detektor (#9).

### Behoben
- Layout: Ringblenden (Blende oder dünnes Element mit Innenradius) wurden als Linie über den offenen
  Ring gezeichnet, die gesperrte Mitte blieb leer. Jetzt sind Mitte und Backen dicke Balken und der
  offene Ring eine dünne graue Linie.
- Layout: Blenden und Detektoren werden an ihrer Position und mit ihrer Verkippung gezeichnet statt
  immer auf der Achse (#7).
- Freies Bündel: Radius und Startebene folgen einem Systemwechsel. Vorher startete das Bündel nach
  dem Michelson beim TIR-Prisma hinter der Eintrittsfläche, und alle Strahlen gingen verloren.

### Hinzugefügt (0.8.0)
- Ansicht **Beugung** (M6): Beugungs-PSF mit Strehlzahl und Schnitten, MTF tangential und sagittal,
  eingeschlossene Energie mit den Radien für 50, 80 und 90 % und die Strehlzahl durch den Fokus;
  monochromatisch oder polychromatisch, Pupillengitter wählbar, mit Fokusverschiebung.
- OPD / Wellenfront: Fokusverschiebung der Referenzkugel, σ um den besten Fokus, Strehlzahl und
  Zernike-Koeffizienten (Noll, mit Namen) aus dem Zernike-Fit der Bibliothek.
- Funktionsflags `wavefront` und `diffraction`.
- **Ideale Linse:** Modell zeigt Brennweite, Objektabstand und Zylinderachse; das Layout zeichnet ein
  Linsensymbol; im Baukasten der Zeilentyp „Ideallinse“ (Brennweite in der Radius-Spalte, als Variable
  optimierbar, Schema 0.5.0).
- Polarisation: **Jones-Pupille** der Bibliothek mit Diattenuation, physikalischer Retardance (auch für
  fokussierte Strahlen), Jones-Matrix am Hauptstrahl und Stokes-Karte für polarisierte Quellen; mit
  dem freien Bündel auch für gefaltete Systeme.
- Pfade & Ghosts: **Interferogramm** zweier Pfade mit Streifen, Intensität, Streifenzahl und Scherung.
- Strahlenbündel: Pupillenraster **Punktliste** (px, py je Zeile).
- Funktionsflags `ideal_lens`, `jones`, `interferogram` und `point_list`.

### Geändert (0.8.0)
- OPD / Wellenfront: Die Strehlzahl kommt aus der Bibliothek statt aus der eigenen Maréchal-Formel.

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
- **Optimieren im Baukasten:** Häkchen „R var“, „k var“, „d var“ in der Flächentabelle und eine
  Merit-Tabelle (EFL, BFL, Blendenzahl, Randstrahl im Fokus, RMS-Spot, RMS-Wellenfront); das Ergebnis
  lässt sich in die Tabelle zurückschreiben.
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
- Spot: Der Airy-Radius rechnete mit |EFL|/EPD und war für ein Objekt im Endlichen zu klein (bei
  `r2/ideal_lens` etwa um den Faktor 3); jetzt mit der paraxialen Arbeitsblende und der gewählten
  Wellenlänge.
- OPD / Wellenfront: Die Maréchal-Näherung für ältere Bibliotheken berücksichtigt jetzt λ_ref/λ; bei
  einer anderen Wellenlänge als der Referenz war die Strehlzahl falsch.
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
