# Kompatibilität mit Bibliotheksversionen

Der Explorer prüft beim Start, welche Funktionen die installierte `raytatouille` hat
(`compat.Features.detect`), statt Versionsnummern zu vergleichen. Das ist robust gegenüber
Entwicklungsständen, die zwischen zwei Releases liegen ([ADR 0005](adr/0005.md)). Die Seitenleiste
zeigt das Ergebnis unter „Funktionen dieser Bibliotheksversion“.

| Flag | Erkannt an | Fehlt es | Stand in der Bibliothek |
| --- | --- | --- | --- |
| `paths` | `trace(..., record_path=True)` | Keine Strahlen im Layout | `main` (#88) |
| `layout` | `raytatouille.layout` | Layout ohne Flächen; im Baukasten gibt es eine Skizze | PR #90, bei Erstellung offen |
| `glasses` | `MaterialLibrary.glasses` | Materialien ohne Katalog-Browser und Glaskarte | `main` (#89) |
| `alias` | `MaterialLibrary.add_catalog_text` | Gleichnamige Kataloge nicht gemeinsam ladbar; Katalog über temporäre Datei | `main` (#89) |
| `polar` | `raytatouille.polar` | Ansicht Polarisation zeigt nur einen Hinweis | ab 0.4.0 |
| `coatings` | `CoatingLibrary` | Systeme mit Coatings lassen sich nicht kompilieren | ab 0.4.0 |

## Getestet

Stand 2026-10-07, Linux, Python 3.12, Streamlit aktuell:

- Raytatouille `main` (0.4.0, Commit `b5c5884`): alle Tests grün; ohne `layout`.
- Raytatouille Branch `worktree-issue-81` (PR #90): alle Tests grün; mit `layout`, aber ohne `alias`.

Die CI baut die Bibliothek aus `main`; per „Run workflow“ lässt sich ein anderer Branch oder
Commit angeben (`library_ref`).

## Streamlit

Ab 1.49 heißt der Breitenparameter von Tabellen `width="stretch"`, davor `use_container_width`.
`stretch.stretch_kwargs` wählt den passenden. Mindestversion ist 1.40.
