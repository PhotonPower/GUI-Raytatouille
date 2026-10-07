# Installation

Der Explorer braucht das Python-Paket `raytatouille`. Es ist ein C++-Projekt und wird aus dem
Quellcode gebaut; es liegt nicht auf PyPI.

## 1. Bibliothek bauen (Linux, Ubuntu 24.04)

```bash
sudo apt-get install cmake ninja-build g++ libeigen3-dev nlohmann-json3-dev libtbb-dev
git clone https://github.com/PhotonPower/Raytatouille.git
python -m venv .venv && source .venv/bin/activate
pip install "./Raytatouille[plot]"
python -c "import raytatouille as rt; print(rt.__version__)"
```

Der Build dauert einige Minuten. Falls pip keinen Zugriff auf PyPI für die Build-Werkzeuge hat:
`pip install scikit-build-core==1.1.1 nanobind==2.13.0` und dann `pip install --no-build-isolation ...`
(so wurde der Explorer getestet).

**Windows:** Die Bibliothek wird dort mit vcpkg gebaut, siehe deren README und `AGENTS.md`. Ein
Windows-Lauf des Explorers ist bisher nicht getestet.

## 2. Explorer installieren

```bash
git clone https://github.com/PhotonPower/GUI-Raytatouille.git
pip install -e ./GUI-Raytatouille
```

Ohne Installation genügt `pip install -r requirements.txt` und `streamlit run streamlit_app.py`.
Der Extra `pip install -e ".[lib]"` holt die Bibliothek direkt aus GitHub (braucht dieselben
Systempakete wie oben).

## 3. Starten

```bash
rtt-explorer                       # öffnet http://localhost:8501
rtt-explorer --server.port 8600    # zusätzliche Streamlit-Optionen werden durchgereicht
```

## Beispielsysteme und Kataloge

Die Referenzsysteme (`tests/reference`) und Kataloge (`tests/catalogs`) liegen im Repo der
Bibliothek. Der Explorer sucht es in dieser Reihenfolge:

1. Umgebungsvariable `RTT_REPO`
2. aktueller Ordner
3. übergeordnete Ordner der Programmdatei
4. Ordner `Raytatouille` neben dem aktuellen Ordner

Wird nichts gefunden, bleiben „System bauen“ und „Datei hochladen“ nutzbar; eigene AGF- und
Coating-Kataloge lassen sich in der Seitenleiste hochladen.

## Fehlersuche

| Symptom | Ursache und Abhilfe |
| --- | --- |
| „Das Paket `raytatouille` ist nicht installiert“ | Bibliothek in derselben Umgebung installieren (Schritt 1) |
| „Repo nicht gefunden“ | `RTT_REPO` setzen oder den Pfad in der Seitenleiste eintragen |
| Im Layout fehlen Linsen | Die Bibliotheksversion hat kein `raytatouille.layout` (siehe [Kompatibilität](kompatibilitaet.md)) |
| Glas „nicht im gewählten Katalog gefunden“ | Passenden Katalog unter „Aktive Glaskataloge“ wählen (z. B. `m2/schott.agf` für das Cooke-Triplet) |
