"""Feature detection: which functions the installed ``raytatouille`` version offers.

The explorer runs against several library versions. Missing functions are hidden in the UI
instead of raising errors (see ``docs/kompatibilitaet.md``).
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass

import raytatouille as rt


def _has_record_path() -> bool:
    try:
        return "record_path" in inspect.signature(rt.trace.trace).parameters
    except (TypeError, ValueError):
        return False


@dataclass(frozen=True)
class Features:
    """Optional library functions, detected once at import time."""

    paths: bool  # trace(..., record_path=True)
    layout: bool  # raytatouille.layout
    glasses: bool  # MaterialLibrary.glasses
    alias: bool  # MaterialLibrary.add_catalog_text (catalogue alias)
    polar: bool  # raytatouille.polar
    coatings: bool  # CoatingLibrary
    diagnostics: bool = False  # RaytatouilleWarning, Diagnostic.code, result.losses (G10)
    prescription: bool = False  # paraxial.prescription (G5)
    model: bool = False  # System.root and the model tree (G3, read only)
    path_eval: bool = False  # analysis.path_transmission and analysis.opl_difference
    ghosts: bool = False  # compile_with_ghosts and analysis.ghost_ranking
    results: bool = False  # to_json() on result objects (raytatouille.results)
    configs: bool = False  # compile(..., configuration=) and System.resolved
    optim: bool = False  # raytatouille.optim (optimize, MeritFunction)
    reports: bool = False  # analysis.dimension_report, system_report, raytrace_report
    gauss: bool = False  # trace.GaussPupil (Gauss quadrature pupil sampling)
    wavefront: bool = False  # analysis.pupil_function, zernike_fit and focus_shift of opd_map (0.8)
    diffraction: bool = False  # analysis.psf, mtf, encircled_energy, through_focus (0.8)
    ideal_lens: bool = False  # model.IdealLens and model.IdealCylinderLens, schema 0.5.0 (0.8)
    jones: bool = False  # analysis.jones_pupil and analysis.stokes_pupil (0.8)
    interferogram: bool = False  # analysis.interferogram (0.8)
    point_list: bool = False  # trace.PointListPupil (0.8)
    object_medium: bool = False  # model.ObjectSpace.medium, schema 0.7 (ADR 0037)

    @classmethod
    def detect(cls) -> Features:
        analysis = getattr(rt, "analysis", None)
        trace = getattr(rt, "trace", None)
        return cls(
            paths=_has_record_path(),
            layout=hasattr(rt, "layout"),
            glasses=hasattr(rt.MaterialLibrary, "glasses"),
            alias=hasattr(rt.MaterialLibrary, "add_catalog_text"),
            polar=hasattr(rt, "polar"),
            coatings=hasattr(rt, "CoatingLibrary"),
            diagnostics=hasattr(rt, "RaytatouilleWarning") and hasattr(analysis, "RayLosses"),
            prescription=hasattr(getattr(rt, "paraxial", None), "prescription"),
            model=hasattr(rt.System, "root") and hasattr(rt, "model"),
            path_eval=hasattr(analysis, "path_transmission") and hasattr(analysis, "opl_difference"),
            ghosts=hasattr(rt, "compile_with_ghosts") and hasattr(analysis, "ghost_ranking"),
            results=hasattr(rt, "results"),
            # nanobind functions have no reliable signature: detect by the attributes added with them
            configs=hasattr(rt.System, "resolved") and hasattr(rt.CompiledSystem, "configuration"),
            optim=hasattr(getattr(rt, "optim", None), "optimize"),
            reports=hasattr(analysis, "dimension_report") and hasattr(analysis, "raytrace_report"),
            gauss=hasattr(trace, "GaussPupil") and hasattr(trace, "gauss_pupil_weights"),
            wavefront=hasattr(analysis, "pupil_function") and hasattr(analysis, "zernike_fit"),
            diffraction=all(hasattr(analysis, name) for name in ("psf", "mtf", "encircled_energy", "through_focus")),
            ideal_lens=hasattr(getattr(rt, "model", None), "IdealLens"),
            jones=hasattr(analysis, "jones_pupil") and hasattr(analysis, "stokes_pupil"),
            interferogram=hasattr(analysis, "interferogram"),
            point_list=hasattr(trace, "PointListPupil"),
            object_medium=hasattr(getattr(getattr(rt, "model", None), "ObjectSpace", None), "medium"),
        )

    def rows(self) -> list[tuple[str, bool]]:
        """(label, available) for the sidebar overview."""
        return [
            ("Strahlpfade (record_path)", self.paths),
            ("Layout-Geometrie (rt.layout)", self.layout),
            ("Glaskatalog-Browser (MaterialLibrary.glasses)", self.glasses),
            ("Katalog-Alias", self.alias),
            ("Polarisation (rt.polar)", self.polar),
            ("Coatings (CoatingLibrary)", self.coatings),
            ("Diagnosecodes und Strahlverluste", self.diagnostics),
            ("Prescription (paraxial.prescription)", self.prescription),
            ("Modell lesen (System.root)", self.model),
            ("Pfadtransmission und OPL-Differenz", self.path_eval),
            ("Ghost-Analyse (compile_with_ghosts)", self.ghosts),
            ("Ergebnisse als JSON (to_json)", self.results),
            ("Konfigurationen (compile configuration=)", self.configs),
            ("Optimierung (rt.optim)", self.optim),
            ("Reports (Abmessungen, Systemdaten, Raytrace)", self.reports),
            ("Gauß-Pupille (trace.GaussPupil)", self.gauss),
            ("Pupillenfunktion und Zernike-Fit", self.wavefront),
            ("Beugung: PSF, MTF, eingeschl. Energie", self.diffraction),
            ("Ideale Linse (Schema 0.5.0)", self.ideal_lens),
            ("Jones-Pupille und Stokes-Karte", self.jones),
            ("Interferogramm zweier Pfade", self.interferogram),
            ("Pupillenpunkte als Liste", self.point_list),
            ("Medium im Objektraum (Schema 0.7)", self.object_medium),
        ]


FEATURES = Features.detect()
