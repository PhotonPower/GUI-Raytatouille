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

    @classmethod
    def detect(cls) -> Features:
        return cls(
            paths=_has_record_path(),
            layout=hasattr(rt, "layout"),
            glasses=hasattr(rt.MaterialLibrary, "glasses"),
            alias=hasattr(rt.MaterialLibrary, "add_catalog_text"),
            polar=hasattr(rt, "polar"),
            coatings=hasattr(rt, "CoatingLibrary"),
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
        ]


FEATURES = Features.detect()
