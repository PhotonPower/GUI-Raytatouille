"""Design helper result -> surface table of the builder (pure Python, no Streamlit, no library).

``rt.design.singlet/doublet/triplet`` return a ``System``; its file form (``json.loads(system.to_json())``)
follows a fixed pattern (ADR 0053): a stop node, lens nodes with surfaces relative to their node, a detector.
``rows_from_system_dict`` reads that pattern and returns rows for the builder table (``BUILDER_COLUMNS``), so
the builder shows exactly what the library built. Messages are German: they are shown as they are.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

_SPLIT = re.compile(r"[,;\s]+")


def _tokens(text: str) -> list[str]:
    return [t for t in _SPLIT.split(text.strip()) if t]


def parse_numbers(text: str, count: int, what: str) -> list[float]:
    """``count`` numbers from text separated by comma, semicolon or blanks (decimal point, no decimal comma)."""
    tokens = _tokens(text)
    values = []
    for token in tokens:
        try:
            values.append(float(token))
        except ValueError:
            raise ValueError(f"{what}: „{token}“ ist keine Zahl.") from None
    if len(values) != count:
        raise ValueError(f"{what}: {count} Werte erwartet, {len(values)} gefunden.")
    return values


def parse_materials(text: str, count: int, what: str) -> list[str]:
    """``count`` material references (``CATALOG:NAME`` or ``CONST:n``) separated by comma, semicolon or blanks."""
    tokens = _tokens(text)
    if len(tokens) != count:
        raise ValueError(f"{what}: {count} Werte erwartet, {len(tokens)} gefunden.")
    return tokens


def radii_for_library(radii: Sequence[float]) -> list[float | None]:
    """The library has ``None`` for plano; the table and the inputs use radius 0."""
    return [None if r == 0 else r for r in radii]


def _position(item: dict) -> float:
    return float(item.get("pose", {}).get("position", [0.0, 0.0, 0.0])[2])


def _radius(surface: dict) -> tuple[float, float]:
    """(radius, conic) of a surface; a surface without a shape is plano (radius 0)."""
    base = surface.get("shape", {}).get("base")
    if base is None:
        return 0.0, 0.0
    return float(base.get("radius", 0.0)), float(base.get("conic", 0.0))


def _aperture(surface: dict) -> float:
    aperture = surface.get("aperture")
    return float(aperture["radius"]) if aperture and aperture.get("type") == "circular" else 0.0


def rows_from_system_dict(data: dict) -> list[list]:
    """Builder table rows (Typ, Radius, Konik, Dicke, Material danach, Halbdurchmesser, Coating) of a design system.

    The thickness of a row is the distance to the next vertex. A glass stands in the row of the first surface
    of its segment, the last surface of a lens leads back into air. Raises ValueError if the stop sits on a
    lens surface (the table has stop rows only) or the system does not follow the design pattern.
    """
    if "stop" in data.get("aperture", {}):
        raise ValueError("Eine Blende auf einer Linsenfläche kennt die Flächentabelle nicht; "
                         "die Blende muss vor der ersten Linse liegen (Blendenabstand).")
    entries: list[dict] = []  # typ, radius, conic, z, material, sd
    for node in data["root"]["children"]:
        kind, z0 = node["type"], _position(node)
        if kind == "stop":
            for s in node["surfaces"]:
                entries.append({"typ": "Blende", "radius": 0.0, "conic": 0.0, "z": z0 + _position(s), "mat": "AIR",
                                "sd": _aperture(s)})
        elif kind == "lens":
            material = node["material"]
            materials = [material] if isinstance(material, str) else list(material)
            for j, s in enumerate(node["surfaces"]):
                radius, conic = _radius(s)
                entries.append({"typ": "Fläche", "radius": radius, "conic": conic, "z": z0 + _position(s),
                                "mat": materials[j] if j < len(materials) else "AIR", "sd": _aperture(s)})
        elif kind == "detector":
            for s in node["surfaces"]:
                entries.append({"typ": "Bild", "radius": 0.0, "conic": 0.0, "z": z0 + _position(s), "mat": "AIR",
                                "sd": 0.0})
        else:
            raise ValueError(f"Knoten vom Typ „{kind}“ kommt in einem Konstruktionshelfer nicht vor.")
    if not entries or entries[-1]["typ"] != "Bild":
        raise ValueError("Das System hat keinen Detektor als letztes Element.")
    rows = []
    for i, e in enumerate(entries):
        thickness = 0.0 if e["typ"] == "Bild" else round(entries[i + 1]["z"] - e["z"], 12)
        rows.append([e["typ"], e["radius"], e["conic"], thickness, e["mat"], e["sd"], ""])
    return rows
