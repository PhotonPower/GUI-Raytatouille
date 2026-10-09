# Kompatibilität mit Bibliotheksversionen

Der Explorer prüft beim Start, welche Funktionen die installierte `raytatouille` hat
(`compat.Features.detect`), statt Versionsnummern zu vergleichen. Das ist robust gegenüber
Entwicklungsständen, die zwischen zwei Releases liegen ([ADR 0005](adr/0005.md)). Die Seitenleiste
zeigt das Ergebnis unter „Funktionen dieser Bibliotheksversion“.

| Flag | Erkannt an | Fehlt es | Stand in der Bibliothek |
| --- | --- | --- | --- |
| `paths` | `trace(..., record_path=True)` | Keine Strahlen im Layout | `main` (#88) |
| `layout` | `raytatouille.layout` | Layout ohne Flächen; im Baukasten gibt es eine Skizze | ab 0.5.0 (PR #90) |
| `glasses` | `MaterialLibrary.glasses` | Materialien ohne Katalog-Browser und Glaskarte | `main` (#89) |
| `alias` | `MaterialLibrary.add_catalog_text` | Gleichnamige Kataloge nicht gemeinsam ladbar; Katalog über temporäre Datei | `main` (#89) |
| `polar` | `raytatouille.polar` | Ansicht Polarisation zeigt nur einen Hinweis | ab 0.4.0 |
| `coatings` | `CoatingLibrary` | Systeme mit Coatings lassen sich nicht kompilieren | ab 0.4.0 |
| `diagnostics` | `RaytatouilleWarning` und `analysis.RayLosses` | Warnungen nur als Text ohne Code, keine Verlusttabelle | ab 0.5.0 (#86) |
| `prescription` | `paraxial.prescription` | Ansicht Prescription zeigt nur einen Hinweis | ab 0.5.0 (#84) |
| `model` | `System.root` und `raytatouille.model` | Ansicht Modell zeigt nur einen Hinweis | ab 0.5.0 (#82) |
| `path_eval` | `analysis.path_transmission`, `analysis.opl_difference` | Ansicht Pfade & Ghosts zeigt nur einen Hinweis | ab 0.6.0 (#122) |
| `ghosts` | `compile_with_ghosts`, `analysis.ghost_ranking` | Kein Ghost-Ranking | ab 0.6.0 (#123, #124) |
| `results` | `raytatouille.results` (`to_json()` der Ergebnisse) | Kein JSON-Export der Ergebnisse | ab 0.5.0 (#86) |

## Getestet

Stand 2026-10-09, Windows 11, Python 3.12, Streamlit 1.65, Bibliothek mit MSVC und vcpkg gebaut:

- Raytatouille `main` (0.6.0, Commit `9dab188`): alle Tests grün; alle Flags vorhanden.

Stand 2026-10-07, Linux, Python 3.12, Streamlit aktuell:

- Raytatouille `main` (0.4.0, Commit `b5c5884`): alle Tests grün; ohne `layout`.
- Raytatouille Branch `worktree-issue-81` (PR #90): alle Tests grün; mit `layout`, aber ohne `alias`.

Die CI baut die Bibliothek aus `main`; per „Run workflow“ lässt sich ein anderer Branch oder
Commit angeben (`library_ref`).

## Streamlit

Ab 1.49 heißt der Breitenparameter von Tabellen `width="stretch"`, davor `use_container_width`.
`stretch.stretch_kwargs` wählt den passenden. Mindestversion ist 1.40.
