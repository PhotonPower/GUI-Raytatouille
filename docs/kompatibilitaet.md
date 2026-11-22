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
| `configs` | `System.resolved` und `CompiledSystem.configuration` | Keine Konfigurationsauswahl; kompiliert wird die Vorgabe | ab 0.7.0 (#165, #169) |
| `optim` | `raytatouille.optim.optimize` | Ansicht Optimierung zeigt nur einen Hinweis | ab 0.7.0 (#167–#170) |
| `reports` | `analysis.dimension_report`, `analysis.raytrace_report` | Ansicht Reports zeigt nur einen Hinweis | ab 0.7.0 (#177) |
| `gauss` | `trace.GaussPupil`, `trace.gauss_pupil_weights` | Kein Raster „Gauß-Quadratur“ im Strahlenbündel | ab 0.7.0 (#168) |
| `wavefront` | `analysis.pupil_function`, `analysis.zernike_fit` | OPD ohne Fokusverschiebung und Zernike-Fit; Strehl als Näherung der Oberfläche | ab 0.8.0 (#202, #203, #209) |
| `diffraction` | `analysis.psf`, `mtf`, `encircled_energy`, `through_focus` | Ansicht Beugung zeigt nur einen Hinweis | ab 0.8.0 (#205, #206, #209) |
| `ideal_lens` | `model.IdealLens` | Kein Zeilentyp Ideallinse im Baukasten; Dateien mit idealer Linse (Schema 0.5.0) lassen sich nicht laden | ab 0.8.0 (#178) |
| `jones` | `analysis.jones_pupil`, `analysis.stokes_pupil` | Polarisation ohne Jones-Pupille und Stokes-Karte | ab 0.8.0 (#208, #211) |
| `interferogram` | `analysis.interferogram` | Pfade & Ghosts ohne Interferogramm | ab 0.8.0 (#210) |
| `point_list` | `trace.PointListPupil` | Kein Raster „Punktliste“ im Strahlenbündel | ab 0.8.0 |
| `object_medium` | `model.ObjectSpace.medium` | Layout färbt den Objektraum nicht ein (Dateien mit `object.medium`, Schema 0.7, lassen sich ohnehin nicht laden) | nach 0.8.0 (Schema 0.7, #282) |
| `tolerance` | `raytatouille.tolerance` (`expand`, `sensitivity`, `monte_carlo`) | Ansicht Toleranzen zeigt nur einen Hinweis | ab 0.9.0 (#253–#260) |
| `irradiance` | `analysis.irradiance_map` | Ansicht Bestrahlungsstärke zeigt nur einen Hinweis | ab 0.10.0 (#379) |
| `design` | `rt.design.singlet` | Keine Konstruktionshelfer im Baukasten | nach 0.10.0 (#321) |
| `surface_types` | `model.Biconic`, `model.OddAsphere` (Axicon, Q-con, Q-bfs gehören dazu) | Dateien mit diesen Flächen lassen sich nicht laden | ab 0.10.0 (#314, #315) |
| `freeform` | `model.ZernikeFringeSag` (XY-Polynom und Gitter gehören dazu) | Dateien mit Freiformtermen (Schema 0.11) lassen sich nicht laden | nach 0.10.0 (#316) |
| `anamorphic_first_order` | `paraxial.first_order_section` | Keine erste Ordnung je Schnitt für anamorphe Systeme | ab 0.10.0 (#315) |
| `aperture_shapes` | `model.PolygonAperture`, `model.CircularObscuration` | Layout zeichnet Polygone und Obskurationen nicht; Dateien damit (Schema 0.11) lassen sich nicht laden | nach 0.10.0 (#320) |
| `inactive` | `model.Element.active` | Kein Schalter „aktiv“ je Bauteil | ab 0.10.0 (#380) |
| `on_iteration` | `optim.IterationState` | Optimierung ohne Live-Verlauf | ab 0.10.0 (#378) |
| `object_reference` | `model.ObjectSpace.reference` | Dateien mit `object.reference` (Schema 0.8) lassen sich nicht laden | ab 0.10.0 (#288) |
| `stop_on_surface` | `model.SystemAperture.stop` | Dateien mit `aperture.stop` (Schema 0.8) lassen sich nicht laden | ab 0.10.0 (#53) |
| `schemas` | `rt.schema` | Keine Schema-Prüfung der System-Datei | ab 0.10.0 (#386) |

## Getestet

- 2026-11-22, Raytatouille `main` (0.10.0 plus 21 Commits, `82b0d63`), Linux, Python 3.13: alle Tests
  grün; alle Flags vorhanden. Die Ansichten nutzen die neuen Flags noch nicht; sie sind nur erkannt
  und in der Seitenleiste aufgelistet.

Windows 11, Python 3.12, Streamlit 1.65, Bibliothek mit MSVC und vcpkg gebaut:

- 2026-10-12, Raytatouille `v0.8.0` (Commit `451ab4c`): alle Tests grün; alle Flags vorhanden.
- 2026-10-12, Raytatouille `v0.7.0` mit den Referenzsystemen und Katalogen von `v0.7.0`: alle Tests
  grün, die 0.8-Tests werden übersprungen; ohne `wavefront` und `diffraction`.
- 2026-10-10, Raytatouille `v0.7.0` (Commit `41fff00`): alle Tests grün; alle Flags vorhanden.
- 2026-10-09, Raytatouille `main` (0.6.0, Commit `9dab188`): alle Tests grün; ohne `configs`, `optim`,
  `reports` und `gauss`.

Stand 2026-10-07, Linux, Python 3.12, Streamlit aktuell:

- Raytatouille `main` (0.4.0, Commit `b5c5884`): alle Tests grün; ohne `layout`.
- Raytatouille Branch `worktree-issue-81` (PR #90): alle Tests grün; mit `layout`, aber ohne `alias`.

Die CI baut die Bibliothek aus `main`; per „Run workflow“ lässt sich ein anderer Branch oder
Commit angeben (`library_ref`).

## Streamlit

Ab 1.49 heißt der Breitenparameter von Tabellen `width="stretch"`, davor `use_container_width`.
`stretch.stretch_kwargs` wählt den passenden. Mindestversion ist 1.40.
