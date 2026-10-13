# Bedienung

Einheiten: Längen in mm, Wellenlängen in µm, Felder in Grad. Die optische Achse ist +z.

## Seitenleiste

- **Projekt:** Pfad zum Raytatouille-Repo und die Quelle des Systems.
- **Umgebung:** Temperatur und Luftdruck überschreiben. Wirkt auf die Luft (Ciddor) und, falls der
  Katalog dn/dT enthält, auf die Gläser.
- **Funktionen dieser Bibliotheksversion:** zeigt mit ✅/❌, was die installierte Version kann.
- **Kataloge:** eigene AGF-Glaskataloge und Coating-Kataloge (`.json`) hochladen. Welche Katalogdatei
  aktiv ist, wählt die App anhand der Glas- und Coating-Referenzen im System vor; gleichnamige
  Dateien (zwei `schott.agf`) werden mit Alias geladen (`SCHOTT`, `SCHOTT_2`), sofern die
  Bibliothek das kann.
- **Pfad:** erscheint nur bei Systemen mit mehreren optischen Pfaden.
- **Konfiguration:** erscheint nur bei Systemen mit Konfigurationen (Parametertabelle, z. B.
  `m5/zoom`). Kompiliert wird die gewählte Spalte; die Kopfzeile nennt sie. Alle Ansichten rechnen mit
  ihr, die Optimierung dagegen mit allen Konfigurationen, die ihre Merit-Funktion nennt.

## Systemquellen

**Beispielsystem:** Dateien aus `tests/reference` der Bibliothek, Vorgabe ist `m2/cooke_triplet`.

**Datei hochladen:** eine `.rtt.json`-Datei.

**System bauen:** Vorlage wählen und die Flächentabelle bearbeiten.

| Spalte | Bedeutung |
| --- | --- |
| Typ | `Fläche`, `Blende`, `Ideallinse` (ab Raytatouille 0.8) oder `Bild` |
| Radius | Scheitelradius in mm, 0 = plan. Positiv, wenn der Krümmungsmittelpunkt bei +z liegt. Bei einer Ideallinse die Brennweite f |
| Konik | Konstante k |
| Dicke | Abstand bis zur nächsten Zeile (> 0); die z-Position ergibt sich aus der Summe |
| Material danach | `AIR`, `CONST:1.5168` oder `KATALOG:GLAS` (z. B. `SCHOTT:N-BK7`) |
| Halbdurchm. | Halber freier Durchmesser, 0 = frei |
| Coating | optional `KATALOG:NAME`, z. B. `DEMO:AR_MGF2` |

Regeln: Genau eine Blende (in Luft) und genau eine Bildzeile am Ende. Das Glas steht in der Zeile der
ersten Linsenfläche; die Fläche, die wieder in Luft führt, schließt die Linse ab. Aufeinanderfolgende
Gläser ergeben ein verkittetes Element. Zusätzlich gibt es Tabellen für Wellenlängen (genau eine
Referenz) und Feldpunkte. Fehler erscheinen auf Deutsch mit Zeilennummer.

Eine Zeile vom Typ **Ideallinse** ist eine dünne ideale Linse in Luft (Material davor und danach
`AIR`): Brennweite in der Radius-Spalte (f > 0 sammelnd, f < 0 zerstreuend), Halbdurchmesser
optional, keine Konik und kein Coating. Sie bildet für ein unendlich fernes Objekt fehlerfrei ab;
„R var“ macht die Brennweite zur Optimierungsvariablen. Mit einer Ideallinse hat die Datei Schema
0.5.0.

Hilfen: „Glas aus einem aktiven Katalog eintragen“ und der Knopf **Bildebene auf paraxialen Fokus
setzen**, der die letzte Dicke anpasst.

**Optimieren im Baukasten** (ab Raytatouille 0.7):
- Die Häkchen **R var**, **k var** und **d var** machen Radius, Konik und Dicke einer Zeile zu
  Optimierungsvariablen. Eine plane Fläche (Radius 0) kann nicht variabel sein; dann einen großen
  Startradius eintragen. Variable Dicken bleiben ≥ 0,01 mm, haben aber keine Obergrenze.
- Rechts die **Merit-Funktion**: je Zeile ein Operand mit Ziel und Gewicht (leer = 1).
  | Operand | Bedeutung |
  | --- | --- |
  | EFL, BFL | Brenn- bzw. Schnittweite in mm, Ziel nötig |
  | Blendenzahl bildseitig | paraxiale Blendenzahl, Ziel nötig |
  | Randstrahl im Fokus | Höhe des Randstrahls (Pupille py = 1) in der Bildebene, Ziel 0 |
  | RMS-Spot, RMS-Wellenfront | Abbildungsgüte über alle Felder und Wellenlängen (Gauß-Abtastung) |
- Intern wird jede Variable eine Zeile der Parametertabelle, benannt nach Größe und Tabellenzeile
  (`R2`, `K2`, `D3`); die Datei hat dann Schema 0.4.0.
- In der Ansicht **Optimierung** „Optimieren“ drücken; **Ergebnis in die Flächentabelle übernehmen**
  schreibt die neuen Werte in die Tabelle zurück.

## Kopfzeile

Brennweite EFL, Schnittweite BFL, f/#, Eintrittspupille und paraxiale Bildebene. Darunter ein
Aufklapper mit Wellenlängen, Feldern, Pfaden und Flächen-IDs.

## Ansichten

**Layout:** Schnittebene yz oder xz, Strahlen als Fächer oder hexapolar, Real- oder Paraxial-Aiming,
Felder und Wellenlängen wählbar, verlorene Strahlen als rotes ×. Die Strahlquelle ist entweder die
Pupille mit Feldern (braucht eine Blende) oder ein **freies kollimiertes Bündel** (Radius,
Startebene, Neigung), das auch Systeme ohne Blende zeigt. Der Zoom auf die Bildebene schneidet den
Bereich davor aus. Ideale Linsen erscheinen als violettes Linsensymbol (Pfeile nach außen: sammelnd,
nach innen: zerstreuend); eine Zylinderlinse ohne Brechkraft in der Schnittebene gestrichelt.
Hat das System mehrere Pfade (z. B. die beiden Arme eines Michelson-Interferometers), zeichnet
„Alle Pfade zeichnen“ jeden Pfad einzeln: Die Bibliothek verfolgt immer einen Pfad, ein Strahlteiler
teilt die Strahlen nicht. In Referenzfarben bekommt jeder Pfad eine Farbe, in Spektralfarben eine
Linienart; die Legende nennt die Pfadnamen. Ausgeschaltet zeigt das Layout nur den Pfad aus der
Seitenleiste. Blenden und Detektoren stehen an ihrer Position und mit ihrer Verkippung (z. B. der
Detektor des Michelson bei y = −50). Endet ein Pfad mit einer Reflexion oder Totalreflexion, zeigt
ein blasses Stück, wohin die Strahlen danach laufen; seine Länge dient nur der Orientierung. Hinter
einem Detektor gibt es kein solches Stück. Radius und Startebene des freien Bündels werden beim
Wechsel auf ein anderes System auf dessen Vorgaben zurückgesetzt, die Neigungen bleiben.

**Spot:** RMS um Schwerpunkt und Hauptstrahl, GEO-Radius, angekommene Strahlen. Der Airy-Radius
1,22·λ·N_w ist ein Vergleichswert (Näherung); N_w ist die paraxiale Arbeitsblende 1/(2|n′u′|) der
Bibliothek und gilt auch für ein Objekt im Endlichen (ohne Prescription, vor 0.6: |EFL|/EPD).

**OPD / Wellenfront:** RMS und PV in Wellen. Ab Raytatouille 0.8 verschiebt **Fokusverschiebung (mm)**
die Referenzkugel entlang des Hauptstrahls; dazu kommen σ um den besten Fokus (ohne Z1 bis Z4) und
die Strehlzahl nach Maréchal aus dem Zernike-Fit der Bibliothek, exp(−(2π·σ_bf·λ_ref/λ)²), gut bis
etwa 0,1. Der Aufklapper **Zernike-Koeffizienten (Noll)** listet 15, 37 oder 66 Terme mit Namen, als
CSV und JSON. Ältere Bibliotheken zeigen die Näherung exp(−(2π·RMS·λ_ref/λ)²) der Oberfläche.

**Beugung** (ab 0.8): Beugungsrechnung der Bibliothek aus der Pupillenfunktion für ein Feld, eine
Wellenlänge oder polychromatisch (Gewichte aus dem System), mit Pupillengitter 32, 64 oder 128 und
Fokusverschiebung. Auswertungen:
- **PSF:** Bild linear oder logarithmisch mit Ausschnitt in Airy-Radien, Schnitte entlang x und y,
  Strehlzahl am Referenzpunkt C′.
- **MTF:** tangential und sagittal über der Ortsfrequenz in Linienpaaren pro mm, als CSV.
- **Eingeschlossene Energie:** Kurve bis zum größten Radius, den die Bibliothek zulässt, mit den
  Radien für 50, 80 und 90 %; Mittelpunkt C′ oder der Punkt der linearen Phase (folgt einer Kippung).
- **Through-Focus:** Strehlzahl über der Fokusverschiebung, monochromatisch; der Bereich in
  Vielfachen der Rayleigh-Tiefe 2·λ·N_w² (Näherung, grau hinterlegt).

Feine Gitter rechnen etwa (π/4)·N² Strahlen je Wellenlänge; Systeme mit afokalem Bildraum liefern
keine PSF und keine MTF.

**Seidel:** Summen S_I bis S_V, C_L, C_T und Beiträge je Fläche; W040 = S_I/8 in Wellen.

Spot, Ray Fans, OPD und Beugung zeigen Warnungen der Bibliothek mit Fläche und Diagnosecode (z. B.
`rays.lost`, `stop.clips_beam`), einen Aufklapper mit den verlorenen Strahlen je Status und der Fläche
mit den meisten Verlusten sowie den Knopf **Ergebnis als JSON** (Format `raytatouille-result`, lesbar
mit `rt.results.load_json`).

**Prescription:** paraxialer Randstrahl (y, u, i) und Hauptstrahl (ȳ, ū, ī) je Flächenereignis mit
z-Position, Brechzahl danach und Lagrange-Invariante; darüber Baulänge, Objektabstand, paraxiale
Arbeitsblende 1/(2|n′u′|) und Bild-NA |n′u′|. Ein Diagramm zeigt die Strahlhöhen über z. Nur für
rotationssymmetrische Pfade; ohne Blende bleiben die Strahlspalten leer.

**Strahlenbündel:** Pupillenraster hexapolar, Gitter, Zufall (fester Seed) oder Gauß-Quadratur
(Ringe × 6 Arme; die Gewichte der Bibliothek stehen in der CSV), Statustabelle,
Auftreffpunkte und CSV-Export. Ab Raytatouille 0.8 auch eine **Punktliste**: eine Zeile je Punkt
`px, py` (normiert, Dezimalpunkt; Punkte außerhalb des Einheitskreises erlaubt, `#` für Kommentare).

**Pfade & Ghosts:** Strahlquelle wie im Layout (Pupille oder freies Bündel).
- *Transmission je Pfad:* mittlerer, kleinster und größter Leistungsanteil; verlorene Strahlen zählen 0.
  Für Systeme mit Strahlteilern, Gittern (eine Zeile je Beugungsordnung) oder Kristallen (o- und
  e-Strahl) das freie Bündel nehmen.
- *Optische Wegdifferenz:* OPL_b − OPL_a zweier Pfade, die auf derselben Fläche enden, in mm und in
  Wellen der gewählten Wellenlänge, als Karte über Pupille oder Bündel.
- *Interferogramm* (ab 0.8): Streifen 1 + cos φ und Intensität der beiden Pfade auf der Bildfläche,
  mit eigener Ringzahl; dazu die Zahl der Streifen über die Fläche, die mittlere Wegdifferenz in
  Wellen und die größte Scherung der Auftreffpunkte. Skalare Zweistrahl-Interferenz mit gleicher
  Polarisation; Phasen von Metallspiegeln oder Coatings fehlen. Für Michelson-Aufbauten
  (`m0/michelson`, `m4/michelson_offset`) das freie Bündel nehmen.
- *Ghosts:* nach Ankreuzen von „Ghost-Ranking berechnen“ alle Zwei-Reflexions-Ghosts des gewählten
  Pfads, sortiert nach relativer Bestrahlungsstärke im Bild. Der Auflösungsradius r₀ ist eine
  Modellwahl (Detektor). Braucht eine Blende.

**Polarisation:** Quelle unpolarisiert, linear (Winkel) oder zirkular. Karten über Pupille oder Bündel
für Transmission, Diattenuation, Retardance und Zirkularität, mittlerer Stokes-Vektor und
Transmission je Wellenlänge. Retardance ist nur für Strahlen definiert, die in ihrer
Einfallsrichtung austreten (Platten, Wellenplatten, ideale Elemente). Konventionen stehen in
`docs/architecture.md` der Bibliothek (ADR 0021).

Ab Raytatouille 0.8 folgt die **Jones-Pupille** der Bibliothek (ADR 0034): Diattenuation und
physikalische Retardance je Pupillenpunkt, auch für fokussierte Strahlen, mit Raster n × n und
Ausgangsbasis (Doppelpol oder Dipol), dazu die Jones-Matrix am Hauptstrahl als Betrag und Phase. Bei
polarisierter Quelle kommen Zirkularität S₃/S₀ und Orientierung der Ellipse am Ausgang dazu. Mit der
Pupille geht das nur für rotationssymmetrische Pfade; gefaltete Systeme (z. B. `m6/fold45_metal`) mit
dem freien Bündel, dessen Mittelstrahl dann der Hauptstrahl ist.

**Optimierung:** für Systeme mit Variablen (`"variable": true`) und einem Abschnitt
`optimization` (z. B. `m5/singlet_solve`, `m5/two_lens_gap`).
- Oben die Merit-Funktion: Operanden mit Ziel, Gewicht und Startwert, Generatoren (RMS-Spot oder
  RMS-Wellenfront mit Gauß-Abtastung) mit Start-RMS, darunter die Variablen mit Grenzen.
- „Optimieren“ startet den Levenberg-Marquardt-Optimierer der Bibliothek auf einer Kopie; die Optionen
  (Iterationen, ftol, xtol) stehen im Aufklapper. Danach: Status, Verlauf der normierten
  Merit-Funktion φ, Variablen vorher/nachher (an der Grenze markiert), Beiträge der Operanden und
  Generatoren.
- „Ergebnis übernehmen“ macht das optimierte System in allen Ansichten aktiv, bis „Verwerfen“ gedrückt
  oder die Quelle gewechselt wird. Speichern als `.rtt.json`, als JSON Patch oder als Ergebnis-JSON.
- Große Strafgewichte auf Gleichheitsbedingungen (z. B. EFL mit Gewicht 10⁴ in `m5/singlet_optim`)
  lassen den Optimierer früh stehen bleiben; besser die Bedingung über die Parametertabelle halten.

**Reports:** drei Reiter mit Tabellen der Bibliothek, jeweils als CSV und JSON.
- *Abmessungen:* je Glassegment Mittendicke, Halbdurchmesser und Apertur beider Flächen, Randdicke und
  Durchmesser.
- *Systemdaten:* Wellenlängen, Blende, Flächen und paraxiale Daten des Pfads als Schlüssel und Wert.
- *Raytrace:* ein y-Fächer (Strahlquelle wie im Layout) mit globalen und lokalen Koordinaten, Weg,
  Gewicht und Status je Ereignis.

**Materialien:** Katalogtabelle mit Suche und Filtern, Glaskarte (n_d über ν_d), Details und innere
Transmission, Dispersionskurven und Abbe-Zahl. Absolute Brechzahlen beziehen sich auf Systemtemperatur
und -druck; der Katalogwert n_d bezieht sich meist auf Luft und weicht daher leicht ab.

**Modell:** liest das geladene System aus dem Modellbaum der Bibliothek: Systemapertur, Objekt,
Feldart, eine Flächentabelle (Baugruppe, Element, Art, Material, z-Lage des Elements, Form, Radius, Konik, Apertur,
Wechselwirkung, Phase), die Pfade mit ihren Ereignissen sowie Parametertabelle und
Konfigurationen. `V` markiert Variablen, `→ NAME` an eine Parameterzeile gebundene Werte. Ideale
Linsen stehen mit Brennweite, Objektabstand und bei Zylinderlinsen mit Achse in der Spalte
Wechselwirkung. Nur lesen.

**System-Datei:** zeigt das System als JSON und speichert es als `.rtt.json`; bei Konfigurationen
auch die gewählte Konfiguration mit festen Werten.
