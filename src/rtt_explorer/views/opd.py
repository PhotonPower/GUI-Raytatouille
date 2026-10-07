"""View "OPD / Wellenfront"."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import streamlit as st
from raytatouille import analysis as an
from raytatouille import plot as rtplot

from ..context import AppContext
from ..ui.common import run, show

TITLE = "OPD / Wellenfront"


def render(ctx: AppContext) -> None:
    """Render the view "OPD / Wellenfront"."""
    comp = ctx.comp
    path_choice = ctx.path_choice
    field_ids = ctx.field_ids
    wl_ids = ctx.wl_ids
    field_label = ctx.field_label
    wl_label = ctx.wl_label
    c1, c2, c3 = st.columns(3)
    f = c1.selectbox("Feld", field_ids, format_func=field_label)
    w = c2.selectbox("Wellenlänge", [None] + wl_ids,
                     format_func=lambda i: "Referenz" if i is None else wl_label(i))
    grid = c3.slider("Gitter", 9, 81, 33, step=2)
    opd = run("OPD-Karte", an.opd_map, comp, path=path_choice, field=f, wavelength=w, grid=grid)
    if opd is not None:
        strehl = math.exp(-((2 * math.pi * opd.rms) ** 2))
        m = st.columns(3)
        m[0].metric("RMS", f"{opd.rms:.4f} Wellen")
        m[1].metric("PV", f"{opd.pv:.4f} Wellen")
        m[2].metric("Strehl (Maréchal)", f"{strehl:.3f}", help="exp(−(2π·RMS)²), gilt für kleine Fehler.")
        a, b = st.columns(2)
        with a:
            fig, ax = plt.subplots(figsize=(5.5, 5))
            rtplot.opd_map(opd, ax)
            show(fig)
        with b:
            fan = run("OPD-Fan", an.opd_fan, comp, path=path_choice, field=f, wavelength=w, points=41)
            if fan is not None:
                fig, ax = plt.subplots(figsize=(5.5, 5))
                rtplot.opd_fan(fan, ax)
                show(fig)
