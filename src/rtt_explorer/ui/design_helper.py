"""Builder: starting system from ``rt.design`` (singlet, cemented doublet, triplet, lens catalogue)."""

from __future__ import annotations

import json

import pandas as pd
import raytatouille as rt
import streamlit as st

from ..builder import BUILDER_COLUMNS, VARIABLE_COLUMNS
from ..design_rows import parse_materials, parse_numbers, radii_for_library, rows_from_system_dict

# kind -> (label, radii, thicknesses, gaps, materials, image distance); radius 0 is plano
KINDS = {
    "singlet": ("Singlet", "100, -100", "5", "", "CONST:1.5168", 94.0),
    "doublet": ("Dublett (verkittet)", "62, -44, -130", "4, 2.5", "", "CONST:1.5168, CONST:1.62", 96.0),
    "triplet": ("Triplet", "30, -200, -40, 35, 80, -30", "4, 1.5, 4", "6, 7",
                "CONST:1.62, CONST:1.7, CONST:1.62", 50.0),
}
COUNTS = {"singlet": (2, 1, 0, 1), "doublet": (3, 2, 0, 2), "triplet": (6, 3, 2, 3)}


def design_helper(epd: float) -> None:
    """Expander in front of the surface table; "Übernehmen" replaces the table by the helper's system."""
    from ..compat import FEATURES

    if not FEATURES.design:
        return
    with st.expander("Konstruktionshelfer: Singlet, Dublett oder Triplet aus wenigen Zahlen (rt.design)"):
        source = st.radio("Quelle", ["Parameter", "Linsenkatalog (JSON)"], horizontal=True, key="design_source")
        c1, c2, c3 = st.columns(3)
        stop = c1.number_input("Abstand Blende → erste Fläche (mm)", value=5.0, min_value=0.001, format="%.3f",
                               key="design_stop")
        semi = c2.number_input("Halbdurchmesser der Linsenflächen (mm, 0 = frei)", value=12.7, min_value=0.0,
                               key="design_sd")
        if source == "Parameter":
            kind = st.selectbox("Art", list(KINDS), format_func=lambda k: KINDS[k][0], key="design_kind")
            _, radii0, thick0, gaps0, mats0, image0 = KINDS[kind]
            image = c3.number_input("Abstand letzte Fläche → Bild (mm)", value=image0, min_value=0.001,
                                    format="%.3f", key=f"design_image_{kind}")
            radii = st.text_input("Radien (mm, 0 = plan; Dezimalpunkt; Komma, Semikolon oder Leerzeichen trennen)",
                                  radii0, key=f"design_radii_{kind}")
            thick = st.text_input("Dicken (mm)", thick0, key=f"design_thick_{kind}")
            gaps = st.text_input("Luftabstände zwischen den Linsen (mm)", gaps0, key=f"design_gaps_{kind}") \
                if kind == "triplet" else ""
            mats = st.text_input("Gläser (KATALOG:GLAS oder CONST:n)", mats0, key=f"design_materials_{kind}")
            label = "Als Flächentabelle übernehmen"
        else:
            image = c3.number_input("Abstand letzte Fläche → Bild (mm)", value=90.0, min_value=0.001,
                                    format="%.3f", key="design_image_catalog")
            up = st.file_uploader("Linsenkatalog (.json, Format raytatouille-lenses)", type=["json"],
                                  key="design_catalog")
            entries = _read_catalog(up)
            entry_name = st.selectbox("Linse", list(entries), key="design_entry") if entries else None
            label = "Linse aus dem Katalog übernehmen"
        st.caption("Die Blende liegt vor der ersten Linse und hat den Radius EPD/2; Wellenlängen und Feldpunkte "
                   "bleiben wie sie sind. Danach lässt sich die Tabelle wie gewohnt bearbeiten. Eine Blende "
                   "zwischen den Linsen oder auf einer Fläche stellt man in der Tabelle selbst ein.")
        if not st.button(label, key="design_apply"):
            return
        try:
            if source == "Parameter":
                system = _build(kind, radii, thick, gaps, mats, epd, stop, semi, image)
            elif entry_name is None:
                st.error("Es ist kein Katalog geladen.")
                return
            else:
                system = rt.design.from_catalog(entries[entry_name], epd=epd, stop_distance=stop,
                                                image_distance=image, semi_diameter=semi if semi > 0 else None)
            rows = rows_from_system_dict(json.loads(system.to_json()))
        except (rt.RaytatouilleError, ValueError) as error:
            st.error(f"Konstruktionshelfer: {error}")
            return
        ss = st.session_state
        df = pd.DataFrame(rows, columns=BUILDER_COLUMNS)
        for col in VARIABLE_COLUMNS:
            df[col] = False
        ss.bdf = df
        ss.bver = ss.get("bver", 0) + 1
        ss.bedited = df.copy()
        st.success(f"Flächentabelle ersetzt: {len(rows)} Zeilen.")


def _build(kind, radii, thick, gaps, mats, epd, stop, semi, image):
    n_radii, n_thick, n_gaps, n_mats = COUNTS[kind]
    r = radii_for_library(parse_numbers(radii, n_radii, "Radien"))
    t = parse_numbers(thick, n_thick, "Dicken")
    m = parse_materials(mats, n_mats, "Gläser")
    common = {"epd": epd, "stop_distance": stop, "image_distance": image,
              "semi_diameter": semi if semi > 0 else None}
    if kind == "singlet":
        return rt.design.singlet(r, t[0], m[0], **common)
    if kind == "doublet":
        return rt.design.doublet(r, t, m, **common)
    return rt.design.triplet(r, t, parse_numbers(gaps, n_gaps, "Luftabstände"), m, **common)


def _read_catalog(up) -> dict:
    """Entries of an uploaded lens catalogue by name; empty (with a message) if there is none or it is invalid."""
    if up is None:
        return {}
    try:
        catalog = rt.design.parse_lens_catalog(up.getvalue().decode("utf-8"))
    except (rt.RaytatouilleError, ValueError, UnicodeDecodeError) as error:
        st.error(f"Linsenkatalog: {error}")
        return {}
    return {entry.name: entry for entry in catalog.lenses}
