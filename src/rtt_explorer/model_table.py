"""The model tree of a system as table rows (pure logic, no Streamlit, no library).

The objects come from ``System.root`` (``raytatouille.model``). The functions only read attributes
and the class name of the active variant (``Plane``, ``Conic``, ...), so tests can use fakes.
"""

from __future__ import annotations

import math

ELEMENT_KINDS = {"lens": "Linse", "mirror": "Spiegel", "plate": "Platte", "thin_element": "dünnes Element",
                 "stop": "Blende", "detector": "Detektor"}

INTERACTIONS = {"Fresnel": "Fresnel", "IdealMirror": "Spiegel (ideal)", "IdealAntiReflection": "AR (ideal)",
                "Absorber": "Absorber", "IdealBeamSplitter": "Strahlteiler (ideal)",
                "IdealPolarizer": "Polarisator (ideal)", "IdealRetarder": "Verzögerer (ideal)"}


def _plain(value):
    """The number of a model.Param (recognised by its ``variable`` flag), else the value itself."""
    return value.value if hasattr(value, "variable") else value


def num(value) -> str:
    """Short number text; infinity as ∞. A model.Param is shown with param_text."""
    if hasattr(value, "variable"):
        return param_text(value)
    if value is None:
        return ""
    v = float(value)
    return ("∞" if v > 0 else "-∞") if math.isinf(v) else f"{v:g}"


def param_text(p) -> str:
    """A model.Param: its value, ``V`` for a variable, ``→ NAME`` for a bound parameter row."""
    if p is None:
        return ""
    if getattr(p, "param", None):
        return f"→ {p.param}"
    return num(p.value) + (" V" if getattr(p, "variable", False) else "")


def shape_text(stack) -> tuple[str, str, str]:
    """(form, radius, conic) of a model.ShapeStack."""
    base = stack.base
    kind = type(base).__name__
    if kind == "Plane":
        form, radius, conic = "plan", "∞", ""
    else:
        radius, conic = param_text(base.radius), param_text(base.conic)
        if kind == "EvenAsphere":
            form = f"Asphäre ({len(base.coefficients)} Koeff.)"
        elif kind == "Conic":
            form = "sphärisch/konisch"
        else:
            form = kind
    terms = len(getattr(stack, "terms", []) or [])
    if terms:
        form += f" + {terms} Zusatzterm" + ("e" if terms > 1 else "")
    return form, radius, conic


def aperture_text(aperture) -> str:
    """Clear aperture of a surface in mm; ``frei`` without aperture."""
    if aperture is None:
        return "frei"
    kind = type(aperture).__name__
    if kind == "CircularAperture":
        inner = _plain(getattr(aperture, "inner_radius", 0.0)) or 0.0
        return f"r {num(inner)} … {num(aperture.radius)}" if inner > 0 else f"r {num(aperture.radius)}"
    if kind == "RectangularAperture":
        return f"±{num(aperture.half_width_x)} × ±{num(aperture.half_width_y)}"
    if kind == "EllipticalAperture":
        return f"Ellipse {num(aperture.semi_axis_x)} × {num(aperture.semi_axis_y)}"
    return kind


def interaction_text(interaction) -> str:
    kind = type(interaction).__name__
    if kind == "CoatingRef":
        return f"Coating {interaction.name}"
    return INTERACTIONS.get(kind, kind)


def phase_text(phases) -> str:
    parts = []
    for ph in phases or []:
        kind = type(ph).__name__
        if kind == "LinearGrating":
            parts.append(f"Gitter {num(ph.lines_per_mm)} /mm")
        elif kind == "RadialPhase":
            parts.append("radiale Phase")
        else:
            parts.append(kind)
    return ", ".join(parts)


def material_text(element) -> str:
    crystal = getattr(element, "crystal", None)
    if crystal is not None:
        return f"{crystal.ordinary} / {crystal.extraordinary}"
    return element.material or ", ".join(getattr(element, "segment_materials", []) or [])


def pose_z_text(pose) -> str:
    text = param_text(pose.position[2])
    reference = getattr(getattr(pose, "reference", None), "name", "ABSOLUTE")
    return text + (" (relativ)" if reference != "ABSOLUTE" else "")


def walk(node, groups: tuple[str, ...] = ()):
    """(assembly names below the root, element) in tree order."""
    for child in node.children:
        if hasattr(child, "children"):
            yield from walk(child, groups + (child.name,))
        else:
            yield groups, child


def surface_rows(root) -> list[dict]:
    """One row per surface: assembly, element, kind, material, position and surface data."""
    rows = []
    for groups, element in walk(root):
        kind = element.kind.name.lower()
        for s in element.surfaces:
            form, radius, conic = shape_text(s.shape)
            rows.append({
                "Baugruppe": " / ".join(groups), "Element": element.name, "Art": ELEMENT_KINDS.get(kind, kind),
                "Material": material_text(element), "Element-z (mm)": pose_z_text(element.pose), "Fläche": s.id,
                "Form": form, "Radius (mm)": radius, "Konik": conic, "Apertur (mm)": aperture_text(s.aperture),
                "Wechselwirkung": interaction_text(s.interaction), "Phase": phase_text(getattr(s, "phases", [])),
            })
    return rows
