"""View "Farbfehler"."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from raytatouille import analysis as an
from raytatouille import plot as rtplot

from ..context import AppContext
from ..ui.common import STRETCH, run, show

TITLE = "Farbfehler"


def render(ctx: AppContext) -> None:
    """Render the view "Farbfehler"."""
    comp = ctx.comp
    path_choice = ctx.path_choice
    field_ids = ctx.field_ids
    wl_ids = ctx.wl_ids
    wl_um = ctx.wl_um
    field_label = ctx.field_label
    wl_label = ctx.wl_label
    if len(wl_ids) < 2:
        st.info("Für Farbfehler braucht das System mindestens zwei Wellenlängen.")
    else:
        c1, c2, c3 = st.columns(3)
        first = c1.selectbox("Erste Wellenlänge", wl_ids, index=0, format_func=wl_label)
        second = c2.selectbox("Zweite Wellenlänge", wl_ids, index=len(wl_ids) - 1, format_func=wl_label)
        zone = c3.slider("Pupillenzone (Realstrahl)", 0.1, 1.0, 1.0, step=0.05)
        lc = run("Farblängsfehler", an.longitudinal_colour, comp, path=path_choice,
                 pair=(first, second), zone=zone)
        if lc is not None:
            m = st.columns(2)
            m[0].metric("Farblängsfehler paraxial", f"{1000 * lc.paraxial:.2f} µm")
            m[1].metric("Farblängsfehler real", f"{1000 * lc.real:.2f} µm")
            fig, ax = plt.subplots(figsize=(6, 4))
            rtplot.longitudinal_colour(lc, ax)
            show(fig)
        st.markdown("**Farbquerfehler**")
        f = st.selectbox("Feld", field_ids, format_func=field_label)
        lat_c = run("Farbquerfehler", an.lateral_colour, comp, path=path_choice, field=f)
        if lat_c is not None:
            st.dataframe(pd.DataFrame({
                "Wellenlänge (µm)": wl_um, "Hauptstrahl x (mm)": lat_c.chief.x,
                "Hauptstrahl y (mm)": lat_c.chief.y,
                "Versatz x (µm)": 1000 * np.asarray(lat_c.offset.x),
                "Versatz y (µm)": 1000 * np.asarray(lat_c.offset.y)}),
                hide_index=True, **STRETCH)
