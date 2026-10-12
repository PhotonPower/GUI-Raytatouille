"""System builder: surface table to ``.rtt.json`` dictionary (pure Python, no library needed).

The table works like the lens data editor of classic optics programs: one row per surface, the
z position follows from the sum of the thicknesses. All error messages are German because they
are shown to the user as they are.
"""

from __future__ import annotations

import math
import re

import pandas as pd

AIR_WORDS = {"", "AIR", "VACUUM"}
BUILDER_COLUMNS = ["Typ", "Radius_mm", "Konik", "Dicke_mm", "Material_danach", "Halbdurchm_mm",
                   "Coating"]
# Optional check box columns: radius, conic constant and thickness of the row are optimization variables.
VARIABLE_COLUMNS = ["R_var", "K_var", "D_var"]
MERIT_COLUMNS = ["Operand", "Ziel", "Gewicht"]
# Merit table label -> (operand or generator, file entry without path/target/weight, needs a target)
MERIT_OPERANDS = {
    "EFL": ("operand", {"type": "efl"}, True),
    "BFL": ("operand", {"type": "bfl"}, True),
    "Blendenzahl bildseitig": ("operand", {"type": "image_fnumber"}, True),
    "Randstrahl im Fokus": ("operand", {"type": "ray_y", "surface": "IMG", "py": 1.0, "target": 0.0}, False),
    "RMS-Spot": ("generator", {"type": "rms_spot"}, False),
    "RMS-Wellenfront": ("generator", {"type": "rms_wavefront"}, False),
}
MIN_THICKNESS = 0.01  # lower bound of a variable thickness, mm
_VARIABLE_ROW = re.compile(r"^([RKD])(\d+)$")
_VARIABLE_TARGET = {"R": "Radius_mm", "K": "Konik", "D": "Dicke_mm"}


def _singlet(r1, r2, t, mat, last, k1=0.0, coating=""):
    return [["Blende", 0.0, 0.0, 5.0, "AIR", 10.0, ""],
            ["Fläche", r1, k1, t, mat, 12.7, coating],
            ["Fläche", r2, 0.0, last, "AIR", 12.7, coating],
            ["Bild", 0.0, 0.0, 0.0, "AIR", 0.0, ""]]


PRESETS = {
    "Plankonvex-Singlet f ≈ 100 mm (n = 1,5168)": _singlet(51.68, 0.0, 4.0, "CONST:1.5168", 97.363),
    "Bikonvexes Singlet (n = 1,5168)": _singlet(100.0, -100.0, 5.0, "CONST:1.5168", 94.0),
    "Singlet mit AR-Coating (braucht Coating-Katalog DEMO)":
        _singlet(52.0, 0.0, 4.0, "CONST:1.52", 97.368, coating="DEMO:AR_MGF2"),
    "Verkittetes Dublett (nur Demo, nicht optimiert)": [
        ["Blende", 0.0, 0.0, 5.0, "AIR", 10.0, ""],
        ["Fläche", 62.0, 0.0, 4.0, "CONST:1.5168", 12.7, ""],
        ["Fläche", -44.0, 0.0, 2.5, "CONST:1.62", 12.7, ""],
        ["Fläche", -130.0, 0.0, 96.0, "AIR", 12.7, ""],
        ["Bild", 0.0, 0.0, 0.0, "AIR", 0.0, ""]],
    "Parabolische Asphäre-Demo: Konik −1 (Plankonvex)": _singlet(51.68, 0.0, 4.0, "CONST:1.5168",
                                                                  97.363, k1=-1.0),
}


def num(value, default=0.0) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return default if math.isnan(v) else v


def flag(value) -> bool:
    """Check box value of a table cell; empty cells (None, NaN) are False."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return False
    return bool(value)


def is_air(material) -> bool:
    return str(material or "").strip().upper() in AIR_WORDS


def surface_rows(df: pd.DataFrame) -> list[dict]:
    """Normalised rows with global z; raises ValueError (German message) on bad tables."""
    rows, z = [], 0.0
    for i, r in enumerate(df.to_dict("records")):
        typ = r.get("Typ")
        if typ not in ("Fläche", "Blende", "Bild"):
            raise ValueError(f"Zeile {i + 1}: Typ muss Fläche, Blende oder Bild sein.")
        coating = r.get("Coating")
        row = {
            "i": i, "typ": typ, "radius": num(r.get("Radius_mm")), "conic": num(r.get("Konik")),
            "t": num(r.get("Dicke_mm"), float("nan")),
            "mat": str(r.get("Material_danach") or "AIR").strip(),
            "sd": num(r.get("Halbdurchm_mm")),
            "coating": "" if coating is None or (isinstance(coating, float) and math.isnan(coating))
            else str(coating).strip(),
            "z": z,
            "r_var": flag(r.get("R_var")), "k_var": flag(r.get("K_var")), "d_var": flag(r.get("D_var")),
        }
        rows.append(row)
        if typ != "Bild":
            if not row["t"] > 0:
                raise ValueError(f"Zeile {i + 1}: Dicke muss > 0 sein (Abstand bis zur nächsten Zeile).")
            z += row["t"]
    return rows


def merit_section(merit_df: pd.DataFrame | None) -> dict | None:
    """The ``optimization`` section from the merit table, None if the table has no rows."""
    operands, generators = [], []
    if merit_df is None:
        return None
    for i, m in enumerate(merit_df.to_dict("records")):
        label = str(m.get("Operand") or "").strip()
        if not label or label == "nan":
            continue
        if label not in MERIT_OPERANDS:
            raise ValueError(f"Merit-Funktion Zeile {i + 1}: unbekannter Operand '{label}'.")
        kind, entry, needs_target = MERIT_OPERANDS[label]
        entry = {**entry, "path": "main"}
        target = num(m.get("Ziel"), float("nan"))
        if needs_target:
            if math.isnan(target):
                raise ValueError(f"Merit-Funktion Zeile {i + 1}: {label} braucht einen Zielwert.")
            entry["target"] = target
        weight = num(m.get("Gewicht"), 1.0)
        if not weight >= 0:
            raise ValueError(f"Merit-Funktion Zeile {i + 1}: Das Gewicht muss ≥ 0 sein.")
        if weight != 1.0:
            entry["weight"] = weight
        (operands if kind == "operand" else generators).append(entry)
    if not operands and not generators:
        return None
    return {"operands": operands, "generators": generators}


def table_updates(variables: list[tuple[str, float]]) -> list[tuple[int, str, float]]:
    """(table row index, column, value) for optimized parameter rows named R<n>, K<n> or D<n>.

    The builder names the rows of its variables after the quantity and the table row (1-based), so
    the result of an optimization can be written back into the table. Other rows are ignored."""
    updates = []
    for row, value in variables:
        match = _VARIABLE_ROW.match(row or "")
        if match:
            updates.append((int(match.group(2)) - 1, _VARIABLE_TARGET[match.group(1)], float(value)))
    return updates


def build_system_dict(name: str, epd: float, wl_df: pd.DataFrame, field_df: pd.DataFrame,
                      rows: list[dict], merit_df: pd.DataFrame | None = None) -> dict:
    """The system as ``.rtt.json`` dictionary.

    Without variables and merit table this is schema 0.2.0. With them (schema 0.4.0) every variable
    becomes a row of the parameter table, named R<n>, K<n> or D<n> after the quantity and table row,
    and positions behind a variable thickness become expression rows (Z<n>, Z<n>REL)."""
    if not rows or rows[-1]["typ"] != "Bild" or sum(r["typ"] == "Bild" for r in rows) != 1:
        raise ValueError("Die letzte Zeile muss genau eine Bildzeile (Typ 'Bild') sein.")
    if sum(r["typ"] == "Blende" for r in rows) > 1:
        raise ValueError("Es ist höchstens eine Blende erlaubt.")
    if not any(r["typ"] == "Blende" for r in rows):
        raise ValueError("Eine Blendenzeile (Typ 'Blende') wird für Pupille und Aiming gebraucht.")
    if not epd > 0:
        raise ValueError("Der Eintrittspupillendurchmesser muss > 0 sein.")

    wavelengths = []
    refs = 0
    for _, w in wl_df.iterrows():
        um = num(w.get("um"), float("nan"))
        if not um > 0:
            continue
        entry = {"um": um}
        if num(w.get("weight"), 1.0) != 1.0:
            entry["weight"] = num(w.get("weight"), 1.0)
        if bool(w.get("Referenz")):
            entry["reference"] = True
            refs += 1
        wavelengths.append(entry)
    if not wavelengths:
        raise ValueError("Mindestens eine Wellenlänge (µm) ist nötig.")
    if refs != 1:
        raise ValueError("Genau eine Wellenlänge muss als Referenz markiert sein.")

    points = []
    for _, f in field_df.iterrows():
        point = {}
        if num(f.get("x_deg")) != 0.0:
            point["x"] = num(f.get("x_deg"))
        if num(f.get("y_deg")) != 0.0:
            point["y"] = num(f.get("y_deg"))
        if num(f.get("weight"), 1.0) != 1.0:
            point["weight"] = num(f.get("weight"), 1.0)
        points.append(point)
    if not points:
        raise ValueError("Mindestens ein Feldpunkt ist nötig.")

    optimization = merit_section(merit_df)
    value_rows: list[dict] = []  # parameter rows of the variables, in table order
    expression_rows: list[dict] = []  # positions behind a variable thickness, after the value rows

    def variable(prefix: str, row: dict, value: float, **extra) -> dict:
        name = f"{prefix}{row['i'] + 1}"
        value_rows.append({"name": name, "value": value, "variable": True, **extra})
        return {"param": name}

    # Thickness of each row as a term of a position expression: its parameter row or the number.
    terms = []
    for row in rows:
        if row["typ"] != "Bild" and row["d_var"]:
            variable("D", row, row["t"], min=MIN_THICKNESS)
            terms.append(f"D{row['i'] + 1}")
        else:
            terms.append(repr(float(row["t"])) if row["typ"] != "Bild" else "")

    def position(start: int, end: int, plain: float, name: str):
        """Distance from row ``start`` to row ``end``: the number, or a bound expression row if a
        variable thickness lies in between."""
        between = terms[start:end]
        if not any(t.startswith("D") for t in between):
            return plain
        expression_rows.append({"name": name, "expression": " + ".join(between)})
        return {"param": name}

    def surface_dict(row, first_z, first_index):
        surface = {"id": row["id"]}
        z_rel = position(first_index, row["i"], row["z"] - first_z, f"Z{row['i'] + 1}REL")
        if z_rel != 0.0:
            surface["pose"] = {"position": [0.0, 0.0, z_rel]}
        if (row["r_var"] or row["k_var"]) and row["radius"] == 0.0:
            raise ValueError(f"Zeile {row['i'] + 1}: Eine plane Fläche (Radius 0) kann nicht variabel sein; "
                             "einen Startradius eintragen (z. B. 1000).")
        if row["radius"] != 0.0:
            radius = variable("R", row, row["radius"]) if row["r_var"] else row["radius"]
            base = {"type": "conic", "radius": radius}
            if row["k_var"]:
                base["conic"] = variable("K", row, row["conic"])
            elif row["conic"] != 0.0:
                base["conic"] = row["conic"]
            surface["shape"] = {"base": base}
        if row["sd"] > 0:
            surface["aperture"] = {"type": "circular", "radius": row["sd"]}
        if row["coating"]:
            if ":" not in row["coating"]:
                raise ValueError(f"Zeile {row['i'] + 1}: Coating als KATALOG:NAME angeben "
                                 "(z. B. DEMO:AR_MGF2).")
            surface["interaction"] = {"type": "coating", "name": row["coating"]}
        return surface

    def pose(row):
        z = position(0, row["i"], row["z"], f"Z{row['i'] + 1}")
        return {"pose": {"position": [0.0, 0.0, z]}} if z != 0.0 else {}

    children, lens_no, i = [], 0, 0
    while i < len(rows):
        row = rows[i]
        if row["typ"] == "Blende":
            if i > 0 and not is_air(rows[i - 1]["mat"]):
                raise ValueError(f"Zeile {i + 1}: Die Blende muss in Luft liegen, nicht im Glas.")
            if not row["sd"] > 0:
                raise ValueError(f"Zeile {i + 1}: Die Blende braucht einen Halbdurchmesser > 0.")
            row["id"] = "STO"
            children.append({"type": "stop", "name": "stop", **pose(row),
                             "surfaces": [{"id": "STO",
                                           "aperture": {"type": "circular", "radius": row["sd"]}}]})
            i += 1
        elif row["typ"] == "Bild":
            if i > 0 and not is_air(rows[i - 1]["mat"]):
                raise ValueError("Die letzte Fläche muss in Luft enden (Material danach = AIR).")
            children.append({"type": "detector", "name": "image", **pose(row),
                             "surfaces": [{"id": "IMG"}]})
            i += 1
        else:
            if is_air(row["mat"]):
                raise ValueError(
                    f"Zeile {i + 1}: Fläche zwischen Luft und Luft. Bei der ersten Linsenfläche "
                    "das Glas in 'Material_danach' eintragen (z. B. CONST:1.5168).")
            lens_no += 1
            group, mats = [row], []
            j = i
            while True:
                mats.append(rows[j]["mat"])
                j += 1
                if j >= len(rows) or rows[j]["typ"] != "Fläche":
                    raise ValueError(f"Zeile {rows[j - 1]['i'] + 1}: Das Glas muss auf einer Fläche "
                                     "enden (Fläche mit Material danach = AIR).")
                group.append(rows[j])
                if is_air(rows[j]["mat"]):
                    break
            for k, g in enumerate(group, start=1):
                g["id"] = f"L{lens_no}.S{k}"
            first_z = group[0]["z"]
            children.append({
                "type": "lens", "name": f"L{lens_no}", **pose(group[0]),
                "material": mats[0] if len(set(mats)) == 1 else mats,
                "surfaces": [surface_dict(g, first_z, group[0]["i"]) for g in group],
            })
            i = j + 1

    system = {
        "schema_version": "0.2.0",
        "name": name,
        "units": {"length": "mm", "wavelength": "um"},
        "wavelengths": wavelengths,
        "aperture": {"type": "epd", "value": float(epd)},
        "fields": {"type": "angle_deg", "points": points},
        "root": {"type": "assembly", "name": "system", "children": children},
        "paths": [{"name": "main", "events": "auto"}],
    }
    if value_rows or optimization:
        # Parameter table and optimization section exist from schema 0.4.0 on.
        system["schema_version"] = "0.4.0"
        if value_rows or expression_rows:
            system["parameters"] = value_rows + expression_rows
        if optimization:
            system["optimization"] = optimization
    return system
