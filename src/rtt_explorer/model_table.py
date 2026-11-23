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


TERM_LABELS = {"ZernikeSag": "Zernike", "ZernikeFringeSag": "Zernike-Fringe", "XyPolynomial": "XY-Polynom",
               "GridSag": "Gitter"}

CURVATURE_FORMS = {"OddAsphere": "Odd Asphere", "QCon": "Forbes Q-con", "QBfs": "Forbes Q-bfs"}


def _radius_of_curvature(c) -> str:
    """Radius 1/c of a curvature Param (``∞`` for 0, `` V`` for a variable, ``c → NAME`` for a bound row)."""
    if getattr(c, "param", None):
        return f"c → {c.param}"
    value = _plain(c)
    text = "∞" if not value else num(1.0 / float(value))
    return text + (" V" if getattr(c, "variable", False) else "")


def _coefficients(base) -> str:
    return f"{len(base.coefficients)} Koeff."


def shape_text(stack) -> tuple[str, str, str]:
    """(form, radius, conic) of a model.ShapeStack."""
    base = stack.base
    kind = type(base).__name__
    if kind == "Plane":
        form, radius, conic = "plan", "∞", ""
    elif kind == "Biconic":
        form = "anamorph (Biconic)"
        radius = f"{param_text(base.radius_x)} / {param_text(base.radius_y)}"
        conic = f"{param_text(base.conic_x)} / {param_text(base.conic_y)}"
    elif kind in CURVATURE_FORMS:
        form = f"{CURVATURE_FORMS[kind]} ({_coefficients(base)})"
        radius, conic = _radius_of_curvature(base.curvature), param_text(base.conic)
    elif kind == "Axicon":
        form, radius, conic = f"Axicon ({num(base.angle_deg)}°)", "", ""
    elif hasattr(base, "radius"):
        radius, conic = param_text(base.radius), param_text(base.conic)
        if kind == "EvenAsphere":
            form = f"Asphäre ({_coefficients(base)})"
        elif kind == "Conic":
            form = "sphärisch/konisch"
        elif kind == "Toroid":
            form = f"Toroid (Rotationsradius {param_text(base.radius_of_rotation)}, {_coefficients(base)})"
        elif kind == "Cylinder":
            form = "Zylinder" + (f" ({_coefficients(base)})" if len(base.coefficients) else "")
        else:
            form = kind
    else:
        form, radius, conic = kind, "", ""
    terms = list(getattr(stack, "terms", []) or [])
    if terms:
        form += f" + {len(terms)} Zusatzterm" + ("e" if len(terms) > 1 else "")
        names = [TERM_LABELS[type(t).__name__] for t in terms if type(t).__name__ in TERM_LABELS]
        if names:
            form += f" ({', '.join(names)})"
    return form, radius, conic


def object_text(objects, object_z: float | None = None) -> tuple[str, str | None]:
    """(value, help) of the object in the model view: infinity, or the distance with its reference.

    Without a reference the distance counts from the global origin; with ``reference.surface`` (schema 0.8)
    from the nominal vertex of that surface, both along −z. ``object_z`` is the global z of the object from the
    compiled system and is added to the help when given."""
    if objects.at_infinity:
        return "unendlich", None
    distance = param_text(objects.distance)
    surface = getattr(getattr(objects, "reference", None), "surface", None)
    if surface:
        value = f"{distance} mm vor {surface}"
        help_text = f"Abstand vor dem nominalen Scheitel der Fläche {surface} längs −z"
    else:
        value, help_text = f"{distance} mm", "Abstand vom globalen Ursprung längs −z"
    if object_z is not None:
        help_text += f"; das Objekt liegt bei z = {num(object_z)} mm"
    return value, help_text


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
    if kind in ("IdealLens", "IdealCylinderLens"):
        cylinder = kind == "IdealCylinderLens"
        text = f"ideale {'Zylinderlinse' if cylinder else 'Linse'} f = {param_text(interaction.focal_length)}"
        if cylinder:
            text += f", Achse {num(interaction.axis_deg)}°"
        if getattr(interaction, "object_distance", None) is not None:
            text += f", Objekt {param_text(interaction.object_distance)}"
        return text
    return INTERACTIONS.get(kind, kind)


def ideal_lenses(root) -> dict[str, dict]:
    """Surface id -> {"cylinder", "f" (mm, None if not a number), "axis_deg"} of the ideal lenses."""
    lenses = {}
    for _, element in walk(root):
        for s in element.surfaces:
            kind = type(s.interaction).__name__
            if kind in ("IdealLens", "IdealCylinderLens"):
                f = _plain(s.interaction.focal_length)
                lenses[s.id] = {"cylinder": kind == "IdealCylinderLens", "f": None if f is None else float(f),
                                "axis_deg": float(_plain(getattr(s.interaction, "axis_deg", 0.0)) or 0.0)}
    return lenses


def power_in_plane(lens: dict, plane: str) -> bool:
    """Whether an ideal lens refracts in the drawing plane ``yz`` or ``xz``.

    A cylinder lens has power only along (-sin ψ, cos ψ) for the axis angle ψ (from x towards y)."""
    if not lens["cylinder"]:
        return True
    psi = math.radians(lens["axis_deg"])
    component = math.cos(psi) if plane == "yz" else math.sin(psi)
    return abs(component) > 1e-9


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
