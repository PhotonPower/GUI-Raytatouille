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

## Systemquellen

**Beispielsystem:** Dateien aus `tests/reference` der Bibliothek, Vorgabe ist `m2/cooke_triplet`.

**Datei hochladen:** eine `.rtt.json`-Datei.

**System bauen:** Vorlage wählen und die Flächentabelle bearbeiten.

| Spalte | Bedeutung |
| --- | --- |
| Typ | `Fläche`, `Blende` oder `Bild` |
| Radius | Scheitelradius in mm, 0 = plan. Positiv, wenn der Krümmungsmittelpunkt bei +z liegt |
| Konik | Konstante k |
| Dicke | Abstand bis zur nächsten Zeile (> 0); die z-Position ergibt sich aus der Summe |
| Material danach | `AIR`, `CONST:1.5168` oder `KATALOG:GLAS` (z. B. `SCHOTT:N-BK7`) |
| Halbdurchm. | Halber freier Durchmesser, 0 = frei |
| Coating | optional `KATALOG:NAME`, z. B. `DEMO:AR_MGF2` |

Regeln: Genau eine Blende (in Luft) und genau eine Bildzeile am Ende. Das Glas steht in der Zeile der
ersten Linsenfläche; die Fläche, die wieder in Luft führt, schließt die Linse ab. Aufeinanderfolgende
Gläser ergeben ein verkittetes Element. Zusätzlich gibt es Tabellen für Wellenlängen (genau eine
Referenz) und Feldpunkte. Fehler erscheinen auf Deutsch mit Zeilennummer.

Hilfen: „Glas aus einem aktiven Katalog eintragen“ und der Knopf **Bildebene auf paraxialen Fokus
setzen**, der die letzte Dicke anpasst.

## Kopfzeile

Brennweite EFL, Schnittweite BFL, f/#, Eintrittspupille und paraxiale Bildebene. Darunter ein
Aufklapper mit Wellenlängen, Feldern, Pfaden und Flächen-IDs.

## Ansichten

**Layout:** Schnittebene yz oder xz, Strahlen als Fächer oder hexapolar, Real- oder Paraxial-Aiming,
Felder und Wellenlängen wählbar, verlorene Strahlen als rotes ×. Die Strahlquelle ist entweder die
Pupille mit Feldern (braucht eine Blende) oder ein **freies kollimiertes Bündel** (Radius,
Startebene, Neigung), das auch Systeme ohne Blende zeigt. Der Zoom auf die Bildebene schneidet den
Bereich davor aus.

**Spot:** RMS um Schwerpunkt und Hauptstrahl, GEO-Radius, angekommene Strahlen. Der Airy-Radius
(1,22·λ·f/#) ist nur ein grober Vergleichswert.

**OPD / Wellenfront:** RMS und PV in Wellen; Strehl nach Maréchal, exp(−(2π·RMS)²), gilt für kleine
Fehler.

**Seidel:** Summen S_I bis S_V, C_L, C_T und Beiträge je Fläche; W040 = S_I/8 in Wellen.

Spot, Ray Fans und OPD zeigen Warnungen der Bibliothek mit Fläche und Diagnosecode (z. B.
`rays.lost`, `stop.clips_beam`), einen Aufklapper mit den verlorenen Strahlen je Status und der Fläche
mit den meisten Verlusten sowie den Knopf **Ergebnis als JSON** (Format `raytatouille-result`, lesbar
mit `rt.results.load_json`).

**Prescription:** paraxialer Randstrahl (y, u, i) und Hauptstrahl (ȳ, ū, ī) je Flächenereignis mit
z-Position, Brechzahl danach und Lagrange-Invariante; darüber Baulänge, Objektabstand, paraxiale
Arbeitsblende 1/(2|n′u′|) und Bild-NA |n′u′|. Ein Diagramm zeigt die Strahlhöhen über z. Nur für
rotationssymmetrische Pfade; ohne Blende bleiben die Strahlspalten leer.

**Strahlenbündel:** Pupillenraster hexapolar, Gitter oder Zufall (fester Seed), Statustabelle,
Auftreffpunkte und CSV-Export.

**Pfade & Ghosts:** Strahlquelle wie im Layout (Pupille oder freies Bündel).
- *Transmission je Pfad:* mittlerer, kleinster und größter Leistungsanteil; verlorene Strahlen zählen 0.
  Für Systeme mit Strahlteilern, Gittern (eine Zeile je Beugungsordnung) oder Kristallen (o- und
  e-Strahl) das freie Bündel nehmen.
- *Optische Wegdifferenz:* OPL_b − OPL_a zweier Pfade, die auf derselben Fläche enden, in mm und in
  Wellen der gewählten Wellenlänge, als Karte über Pupille oder Bündel.
- *Ghosts:* nach Ankreuzen von „Ghost-Ranking berechnen“ alle Zwei-Reflexions-Ghosts des gewählten
  Pfads, sortiert nach relativer Bestrahlungsstärke im Bild. Der Auflösungsradius r₀ ist eine
  Modellwahl (Detektor). Braucht eine Blende.

**Polarisation:** Quelle unpolarisiert, linear (Winkel) oder zirkular. Karten über Pupille oder Bündel
für Transmission, Diattenuation, Retardance und Zirkularität, mittlerer Stokes-Vektor und
Transmission je Wellenlänge. Retardance ist nur für Strahlen definiert, die in ihrer
Einfallsrichtung austreten (Platten, Wellenplatten, ideale Elemente). Konventionen stehen in
`docs/architecture.md` der Bibliothek (ADR 0021).

**Materialien:** Katalogtabelle mit Suche und Filtern, Glaskarte (n_d über ν_d), Details und innere
Transmission, Dispersionskurven und Abbe-Zahl. Absolute Brechzahlen beziehen sich auf Systemtemperatur
und -druck; der Katalogwert n_d bezieht sich meist auf Luft und weicht daher leicht ab.

**Modell:** liest das geladene System aus dem Modellbaum der Bibliothek: Systemapertur, Objekt,
Feldart, eine Flächentabelle (Baugruppe, Element, Art, Material, z-Lage des Elements, Form, Radius, Konik, Apertur,
Wechselwirkung, Phase), die Pfade mit ihren Ereignissen sowie Parametertabelle und
Konfigurationen. `V` markiert Variablen, `→ NAME` an eine Parameterzeile gebundene Werte. Nur lesen.

**System-Datei:** zeigt das System als JSON und speichert es als `.rtt.json`.
