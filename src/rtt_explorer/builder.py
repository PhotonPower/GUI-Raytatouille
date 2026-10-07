"""System builder: surface table to ``.rtt.json`` dictionary (pure Python, no library needed).

The table works like the lens data editor of classic optics programs: one row per surface, the
z position follows from the sum of the thicknesses. All error messages are German because they
are shown to the user as they are.
"""

from __future__ import annotations

import math

import pandas as pd

AIR_WORDS = {"", "AIR", "VACUUM"}
BUILDER_COLUMNS = ["Typ", "Radius_mm", "Konik", "Dicke_mm", "Material_danach", "Halbdurchm_mm",
                   "Coating"]


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
        }
        rows.append(row)
        if typ != "Bild":
            if not row["t"] > 0:
                raise ValueError(f"Zeile {i + 1}: Dicke muss > 0 sein (Abstand bis zur nächsten Zeile).")
            z += row["t"]
    return rows


def build_system_dict(name: str, epd: float, wl_df: pd.DataFrame, field_df: pd.DataFrame,
                      rows: list[dict]) -> dict:
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

    def surface_dict(row, first_z):
        surface = {"id": row["id"]}
        if row["z"] - first_z != 0.0:
            surface["pose"] = {"position": [0.0, 0.0, row["z"] - first_z]}
        if row["radius"] != 0.0:
            base = {"type": "conic", "radius": row["radius"]}
            if row["conic"] != 0.0:
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

    def pose(z):
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
            children.append({"type": "stop", "name": "stop", **pose(row["z"]),
                             "surfaces": [{"id": "STO",
                                           "aperture": {"type": "circular", "radius": row["sd"]}}]})
            i += 1
        elif row["typ"] == "Bild":
            if i > 0 and not is_air(rows[i - 1]["mat"]):
                raise ValueError("Die letzte Fläche muss in Luft enden (Material danach = AIR).")
            children.append({"type": "detector", "name": "image", **pose(row["z"]),
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
                "type": "lens", "name": f"L{lens_no}", **pose(first_z),
                "material": mats[0] if len(set(mats)) == 1 else mats,
                "surfaces": [surface_dict(g, first_z) for g in group],
            })
            i = j + 1

    return {
        "schema_version": "0.2.0",
        "name": name,
        "units": {"length": "mm", "wavelength": "um"},
        "wavelengths": wavelengths,
        "aperture": {"type": "epd", "value": float(epd)},
        "fields": {"type": "angle_deg", "points": points},
        "root": {"type": "assembly", "name": "system", "children": children},
        "paths": [{"name": "main", "events": "auto"}],
    }
