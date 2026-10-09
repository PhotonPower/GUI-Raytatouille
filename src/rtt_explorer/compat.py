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

    @classmethod
    def detect(cls) -> Features:
        analysis = getattr(rt, "analysis", None)
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
        ]


FEATURES = Features.detect()
