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
    tolerance: bool = False  # raytatouille.tolerance: expand, sensitivity, monte_carlo (0.9)
    irradiance: bool = False  # analysis.irradiance_map (0.10)
    design: bool = False  # rt.design: singlet, doublet, triplet, lens catalogues (after 0.10)
    surface_types: bool = False  # model.Biconic, Toroid, Cylinder, OddAsphere, Axicon, QCon, QBfs (0.10)
    freeform: bool = False  # model.ZernikeFringeSag, XyPolynomial, GridSag (schema 0.11)
    anamorphic_first_order: bool = False  # paraxial.first_order_section (0.10)
    aperture_shapes: bool = False  # model.PolygonAperture and surface obscurations (schema 0.11)
    inactive: bool = False  # Element.active, Assembly.active, schema 0.10
    on_iteration: bool = False  # optim.IterationState, optimize(on_iteration=) (0.10)
    object_reference: bool = False  # model.ObjectSpace.reference, schema 0.8
    stop_on_surface: bool = False  # model.SystemAperture.stop, schema 0.8
    schemas: bool = False  # rt.schema(): JSON schemas of the file formats (0.10)

    @classmethod
    def detect(cls) -> Features:
        analysis = getattr(rt, "analysis", None)
        trace = getattr(rt, "trace", None)
        model = getattr(rt, "model", None)
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
            tolerance=hasattr(getattr(rt, "tolerance", None), "monte_carlo")
            and hasattr(rt.tolerance, "sensitivity")
            and hasattr(rt.tolerance, "expand"),
            irradiance=hasattr(analysis, "irradiance_map"),
            design=hasattr(getattr(rt, "design", None), "singlet"),
            surface_types=hasattr(model, "Biconic") and hasattr(model, "OddAsphere"),
            freeform=hasattr(model, "ZernikeFringeSag"),
            anamorphic_first_order=hasattr(getattr(rt, "paraxial", None), "first_order_section"),
            aperture_shapes=hasattr(model, "PolygonAperture") and hasattr(model, "CircularObscuration"),
            inactive=hasattr(getattr(model, "Element", None), "active"),
            on_iteration=hasattr(getattr(rt, "optim", None), "IterationState"),
            object_reference=hasattr(getattr(model, "ObjectSpace", None), "reference"),
            stop_on_surface=hasattr(getattr(model, "SystemAperture", None), "stop"),
            schemas=hasattr(rt, "schema"),
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
            ("Toleranzierung (rt.tolerance)", self.tolerance),
            ("Bestrahlungsstärke (analysis.irradiance_map)", self.irradiance),
            ("Konstruktionshelfer (rt.design)", self.design),
            ("Flächentypen: anamorph, Odd Asphere, Axicon, Forbes", self.surface_types),
            ("Freiformterme: Zernike, XY-Polynom, Gitter (Schema 0.11)", self.freeform),
            ("Erste Ordnung je Schnitt (anamorph)", self.anamorphic_first_order),
            ("Aperturformen und Obskurationen (Schema 0.11)", self.aperture_shapes),
            ("Aktiv-Flag an Bauteilen (Schema 0.10)", self.inactive),
            ("Zwischenstand der Optimierung (on_iteration)", self.on_iteration),
            ("Objektbezug auf eine Fläche (Schema 0.8)", self.object_reference),
            ("Blende auf einer Fläche (Schema 0.8)", self.stop_on_surface),
            ("JSON-Schemas (rt.schema)", self.schemas),
        ]


FEATURES = Features.detect()
