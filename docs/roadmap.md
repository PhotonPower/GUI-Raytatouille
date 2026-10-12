# Roadmap und Grenzen

Die Bibliothek sammelt GUI-Anforderungen in
[`docs/feedback/gui-anforderungen.md`](https://github.com/PhotonPower/Raytatouille/blob/main/docs/feedback/gui-anforderungen.md)
(G1 bis G9). Daraus ergibt sich, was der Explorer schon nutzt und was ihm fehlt. Die Liste ist ein
Vorschlag, keine Zusage.

## Bereits genutzt

- **G1 Strahlpfade:** Strahlen im Layout und die Tabelle verlorener Strahlen.
- **G2 Geometrie-Export:** Linsenschnitt über `raytatouille.layout` (ab 0.5.0).
- **G3 Modell lesen:** Ansicht Modell (Flächen, Pfade, Parametertabelle, Konfigurationen).
- **G5 Prescription:** Ansicht Prescription.
- **G9 Materialbibliothek:** Katalog-Browser, Glaskarte, Katalog-Alias.
- **G10 Diagnosen und Ergebnisformat:** Warnungen mit Code und Fläche, Verlusttabellen, JSON-Export.
- **Multi-Path (0.6.0):** Pfadtransmission, OPL-Differenz und Ghost-Ranking.
- **Optimierung (0.7.0):** Merit-Funktion aus der Datei, Lauf, Ergebnis übernehmen; Konfigurationen,
  Reports (R1) und Gauß-Pupille.

## Bekannte Grenzen

- **Kein Modelleditor (G3):** Die Bibliothek kann das Modell mit `rt.Editor` ändern (JSON Patch,
  Undo, Redo); der Explorer liest es nur. Der Baukasten erzeugt weiter JSON aus einer Tabelle.
- **Kein Abbruch, kein Fortschritt (G4):** Die Bibliothek bietet `cancel=` und `progress=`; der
  Explorer nutzt sie noch nicht, weil Streamlit aus den Rechen-Threads der Bibliothek nicht zeichnen
  darf. Große Rechnungen blockieren die Bedienung.
- **Kein Footprint, keine automatische freie Öffnung (G6).**
- **Merit-Funktion nur aus der Datei:** Operanden, Generatoren und Variablen lassen sich im Explorer
  nicht bearbeiten, nur in der `.rtt.json`.
- **Optimierung und Mehrpfad-Systeme** nur so weit, wie die Bibliothek sie anbietet (z. B. keine
  exakten Nebenbedingungen im Optimierer, #196 der Bibliothek).
- **Streamlit rechnet bei jeder Eingabe neu.** Für sehr große Systeme ist das träge.
- Ungetestet: Python 3.10 im Betrieb. Windows ist getestet (siehe [Kompatibilität](kompatibilitaet.md)),
  läuft aber nicht in der CI.

## Ideen

- Ansichten für G6 und G7 (Footprint, Through-Focus-Spot), sobald die Bibliothek sie liefert.
- Modell bearbeiten mit `rt.Editor` (Undo, Redo, Verlauf als Skript), statt nur Tabelle zu JSON.
- Abbruchknopf und Fortschrittsbalken über `CancelToken` und `progress=`.
- Merit-Funktion und Variablen in der Oberfläche bearbeiten (über `rt.Editor`).
- Alle Konfigurationen eines Zooms nebeneinander zeichnen.
