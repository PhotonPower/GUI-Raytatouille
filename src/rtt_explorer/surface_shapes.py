"""Surface forms of the builder table beyond sphere and conic (pure logic, no Streamlit, no library).

A row of the builder table has the columns ``Radius_mm`` and ``Konik`` for the main section and the
text column ``Form_Parameter`` (``key=value; key=value``, lists comma separated) for everything else.
``shape_base`` returns the ``shape.base`` dictionary of the file format (schema 0.9, ADR 0042/0043).
All error messages are German because they are shown as they are.
"""

from __future__ import annotations

import math

FORMS = ("", "Biconic", "Toroid", "Zylinder", "Odd Asphere", "Axicon", "Forbes Q-con", "Forbes Q-bfs")

# form -> (keys that are lists, keys that are single numbers); every key is optional here, the
# required ones are checked in shape_base
_KEYS = {
    "Biconic": ((), ("radius_y", "conic_y")),
    "Toroid": (("coefficients",), ("radius_of_rotation",)),
    "Zylinder": (("coefficients",), ()),
    "Odd Asphere": (("coefficients",), ()),
    "Axicon": ((), ("angle_deg",)),
    "Forbes Q-con": (("coefficients",), ("normalization_radius",)),
    "Forbes Q-bfs": (("coefficients",), ("normalization_radius",)),
}
# Forms whose file entry carries a curvature (1/R) instead of a radius
CURVATURE_TYPES = {"Odd Asphere": "odd_asphere", "Forbes Q-con": "qcon", "Forbes Q-bfs": "qbfs"}


def _number(text: str, key: str, n: int) -> float:
    try:
        value = float(text)
    except ValueError:
        raise ValueError(f"Zeile {n}: '{key}' ist keine Zahl: {text.strip()}") from None
    if not math.isfinite(value):
        raise ValueError(f"Zeile {n}: '{key}' muss endlich sein")
    return value


def parse_extra(text, form: str, n: int) -> dict:
    """The ``Form_Parameter`` cell as a dictionary; ``n`` is the 1-based table row for messages."""
    if text is None or (isinstance(text, float) and math.isnan(text)) or not str(text).strip():
        return {}
    lists, scalars = _KEYS.get(form, ((), ()))
    allowed = lists + scalars
    result: dict = {}
    for part in str(text).split(";"):
        if not part.strip():
            continue
        key, sep, value = part.partition("=")
        key = key.strip()
        if not sep:
            raise ValueError(f"Zeile {n}: '{key}' braucht die Form schlüssel=wert")
        if key not in allowed:
            raise ValueError(f"Zeile {n}: Form {form} kennt den Schlüssel '{key}' nicht "
                             f"(erlaubt: {', '.join(allowed) or 'keine'})")
        if key in result:
            raise ValueError(f"Zeile {n}: '{key}' steht doppelt")
        if key in lists:
            result[key] = [_number(item, key, n) for item in value.split(",") if item.strip()]
        else:
            items = [item for item in value.split(",") if item.strip()]
            if len(items) != 1:
                raise ValueError(f"Zeile {n}: '{key}' erwartet genau eine Zahl")
            result[key] = _number(items[0], key, n)
    return result


def _need(extra: dict, key: str, form: str, n: int) -> float:
    if key not in extra:
        raise ValueError(f"Zeile {n}: {form} braucht {key} (Spalte Form-Parameter, z. B. {key}=…)")
    return extra[key]


def _is_zero(value) -> bool:
    return isinstance(value, (int, float)) and value == 0.0


def shape_base(form: str, radius, conic, extra: dict, n: int) -> dict:
    """``shape.base`` of a row. ``radius`` and ``conic`` are numbers or ``{"param": NAME}`` (variables)."""
    base: dict
    if form == "Axicon":
        if not (_is_zero(radius) and _is_zero(conic)):
            raise ValueError(f"Zeile {n}: Ein Axicon hat keinen Radius und keine Konik; beide Spalten auf 0 lassen.")
        angle = _need(extra, "angle_deg", form, n)
        if not -90.0 < angle < 90.0:
            raise ValueError(f"Zeile {n}: Der Winkel eines Axicons muss zwischen −90° und 90° liegen.")
        return {"type": "axicon", "angle_deg": angle}
    if form in CURVATURE_TYPES:
        if isinstance(radius, dict):
            raise ValueError(f"Zeile {n}: {form} trägt eine Krümmung; der Radius kann hier keine Variable sein.")
        base = {"type": CURVATURE_TYPES[form], "curvature": 0.0 if radius == 0.0 else 1.0 / radius}
    else:
        if _is_zero(radius):
            raise ValueError(f"Zeile {n}: {form} braucht einen Radius ≠ 0 (Spalte Radius).")
        if form == "Biconic":
            radius_y = _need(extra, "radius_y", form, n)
            if radius_y == 0.0:
                raise ValueError(f"Zeile {n}: {form} braucht radius_y ≠ 0.")
            base = {"type": "biconic", "radius_x": radius, "radius_y": radius_y}
        elif form == "Toroid":
            rotation = _need(extra, "radius_of_rotation", form, n)
            if rotation == 0.0:
                raise ValueError(f"Zeile {n}: {form} braucht radius_of_rotation ≠ 0.")
            base = {"type": "toroid", "radius": radius, "radius_of_rotation": rotation}
        elif form == "Zylinder":
            base = {"type": "cylinder", "radius": radius}
        else:
            raise ValueError(f"Zeile {n}: unbekannte Form '{form}'.")
    if not _is_zero(conic):
        base["conic_x" if form == "Biconic" else "conic"] = conic
    if form == "Biconic" and extra.get("conic_y", 0.0) != 0.0:
        base["conic_y"] = extra["conic_y"]
    if form in ("Toroid", "Zylinder"):
        if extra.get("coefficients"):
            base["coefficients"] = extra["coefficients"]
    elif form == "Odd Asphere":
        if not extra.get("coefficients"):
            raise ValueError(f"Zeile {n}: Odd Asphere braucht mindestens einen Koeffizienten "
                             "(coefficients=A1, A2, …).")
        base["coefficients"] = extra["coefficients"]
    elif form in ("Forbes Q-con", "Forbes Q-bfs"):
        rho = _need(extra, "normalization_radius", form, n)
        if not rho > 0.0:
            raise ValueError(f"Zeile {n}: normalization_radius muss > 0 sein.")
        base["normalization_radius"] = rho
        base["coefficients"] = extra.get("coefficients", [])
    return base
