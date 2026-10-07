# Roadmap und Grenzen

Die Bibliothek sammelt GUI-Anforderungen in
[`docs/feedback/gui-anforderungen.md`](https://github.com/PhotonPower/Raytatouille/blob/main/docs/feedback/gui-anforderungen.md)
(G1 bis G9). Daraus ergibt sich, was der Explorer schon nutzt und was ihm fehlt. Die Liste ist ein
Vorschlag, keine Zusage.

## Bereits genutzt

- **G1 Strahlpfade:** Strahlen im Layout und die Tabelle verlorener Strahlen.
- **G2 Geometrie-Export (PR #90):** Linsenschnitt über `raytatouille.layout`, sobald verfügbar.
- **G9 Materialbibliothek:** Katalog-Browser, Glaskarte, Katalog-Alias.

## Bekannte Grenzen

- **Kein Modelleditor (G3):** Der Baukasten erzeugt JSON aus einer Tabelle, es gibt keinen Rückweg
  vom Modell zur Tabelle, kein Undo und keine Skriptausgabe der Aktionen.
- **Kein Abbruch, kein Fortschritt (G4):** Große Rechnungen blockieren die Bedienung.
- **Kein Footprint, keine automatische freie Öffnung (G6).**
- **Keine Optimierung** und keine Mehrpfad-Systeme über das hinaus, was die Bibliothek anbietet.
- **Streamlit rechnet bei jeder Eingabe neu.** Für sehr große Systeme ist das träge.
- Ungetestet: Windows, Python 3.10 im Betrieb.

## Ideen

- Ansichten für G6 und G7 (Footprint, Through-Focus-Spot), sobald die Bibliothek sie liefert.
- Prescription-Report mit Daten aus G5.
- Hochgeladene Systeme in der Flächentabelle anzeigen, sobald G3 ein Lesen des Modells erlaubt.
