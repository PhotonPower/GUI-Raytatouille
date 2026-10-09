"""The compiled system and everything derived from it, handed to every view."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import raytatouille as rt

from .catalogs import Candidates
from .compat import Features
from .ui import ray_source


@dataclass
class AppContext:
    """State of one script run, built after the system compiled successfully.

    Views read from the context and never from module globals, so each view is a plain function
    ``render(ctx)``.
    """

    features: Features
    system: Any  # rt.System
    comp: Any  # rt.CompiledSystem
    lib: Any  # rt.MaterialLibrary
    system_dict: dict  # parsed JSON of the system
    path_choice: str
    first_order: Any | None  # rt.paraxial result, None if not available
    can_aim: bool
    candidates: Candidates
    named: list[tuple[str, str]]  # (candidate label, catalogue name in the system)
    builder_context: dict | None = None  # surface rows and EPD in mode "System bauen"
    coatings: Any | None = None  # rt.CoatingLibrary of the active coating catalogues, None without
    configuration: int | None = None  # compiled configuration (column of the parameter table), None: default
    system_key: str = ""  # JSON text of the system plus catalogues, a cache key for derived results
    wl_um: list[float] = field(default_factory=list)
    ref_wl: int = 0
    field_ids: list[int] = field(default_factory=list)
    wl_ids: list[int] = field(default_factory=list)

    # ------------------------------------------------------------------ derived values
    @property
    def epd_value(self) -> float | None:
        fo = self.first_order
        return fo.entrance_pupil.diameter if fo is not None and fo.entrance_pupil is not None else None

    @property
    def fnum(self) -> float | None:
        fo = self.first_order
        epd = self.epd_value
        return (abs(fo.efl) / epd) if fo is not None and epd and fo.efl else None

    @property
    def aim_map(self) -> dict:
        return {"Real": rt.trace.Aiming.REAL, "Paraxial": rt.trace.Aiming.PARAXIAL}

    @property
    def fields_json(self) -> list[dict]:
        return self.system_dict.get("fields", {}).get("points", [])

    @property
    def field_unit(self) -> str:
        field_type = self.system_dict.get("fields", {}).get("type", "angle_deg")
        return {"angle_deg": "°", "object_height": " mm", "paraxial_image_height": " mm"}.get(field_type, "")

    # ------------------------------------------------------------------ labels
    def field_label(self, i: int) -> str:
        if i < len(self.fields_json):
            p = self.fields_json[i]
            unit = self.field_unit
            return f"Feld {i}: x={p.get('x', 0)}{unit}, y={p.get('y', 0)}{unit}"
        return f"Feld {i}"

    def wl_label(self, i: int) -> str:
        return f"{i}: {self.wl_um[i]:.4f} µm" + (" (Referenz)" if i == self.ref_wl else "")

    # ------------------------------------------------------------------ ray sources
    def source_ui(self, key: str) -> dict:
        return ray_source.source_ui(self, key)

    def make_batch(self, src: dict, kind: str, n: int, plane: str, field: int, wl: int, aim):
        return ray_source.make_batch(self, src, kind, n, plane, field, wl, aim)
