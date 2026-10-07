"""View "Ray Fans"."""

from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st
from raytatouille import analysis as an
from raytatouille import plot as rtplot

from ..context import AppContext
from ..ui.common import run, show

TITLE = "Ray Fans"


def render(ctx: AppContext) -> None:
    """Render the view "Ray Fans"."""
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
    points = c3.slider("Punkte", 5, 101, 41)
    fan = run("Ray Fan", an.ray_fan, comp, path=path_choice, field=f, wavelength=w, points=points)
    if fan is not None:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        rtplot.ray_fan(fan, ax)
        show(fig)
