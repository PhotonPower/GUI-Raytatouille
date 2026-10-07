"""View "Spot"."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import raytatouille as rt
import streamlit as st
from raytatouille import analysis as an
from raytatouille import plot as rtplot

from ..context import AppContext
from ..ui.common import STRETCH, run, show

TITLE = "Spot"


def render(ctx: AppContext) -> None:
    """Render the view "Spot"."""
    comp = ctx.comp
    path_choice = ctx.path_choice
    field_ids = ctx.field_ids
    wl_ids = ctx.wl_ids
    wl_um = ctx.wl_um
    ref_wl = ctx.ref_wl
    fnum = ctx.fnum
    field_label = ctx.field_label
    wl_label = ctx.wl_label
    aim_map = ctx.aim_map
    c1, c2, c3, c4 = st.columns(4)
    f = c1.selectbox("Feld", field_ids, format_func=field_label)
    w_opts = [None] + wl_ids
    w = c2.selectbox("Wellenlänge", w_opts,
                     format_func=lambda i: "polychromatisch" if i is None else wl_label(i))
    rings = c3.slider("Ringe (hexapolar)", 1, 30, 8)
    aim = aim_map[c4.radio("Aiming", list(aim_map), horizontal=True)]
    spot = run("Spot", an.spot, comp, path=path_choice, field=f, wavelength=w,
               rays=f"hexapolar:{rings}", aiming=aim)
    if spot is not None:
        m = st.columns(5)
        m[0].metric("RMS um Schwerpunkt", f"{1000 * spot.stats.rms_centroid:.2f} µm")
        m[1].metric("RMS um Hauptstrahl", f"{1000 * spot.stats.rms_chief:.2f} µm")
        m[2].metric("GEO-Radius (Hauptstrahl)", f"{1000 * spot.stats.geo_chief:.2f} µm")
        m[3].metric("Strahlen angekommen", f"{spot.rays_arrived}/{spot.rays_launched}")
        airy = 1.22 * wl_um[ref_wl] * fnum if fnum else None
        m[4].metric("Airy-Radius (Näherung)", f"{airy:.2f} µm" if airy else "–",
                    help="1,22 · λ_ref · f/#, nur ein grober Vergleichswert.")
        fig, ax = plt.subplots(figsize=(6, 6))
        rtplot.spot(spot, ax)
        if airy:
            ax.add_patch(plt.Circle((spot.chief.x, spot.chief.y), airy / 1000, fill=False,
                                    color="gray", ls="--", label="Airy-Radius"))
            ax.legend()
        show(fig)
    st.markdown("**Übersicht über alle Felder** (polychromatisch, hexapolar 8)")
    table, overview_errors = [], []
    for i in field_ids:
        try:
            s = an.spot(comp, path=path_choice, field=i, rays="hexapolar:8", aiming=aim)
            table.append({"Feld": field_label(i), "RMS (µm)": 1000 * s.stats.rms_chief,
                          "GEO (µm)": 1000 * s.stats.geo_chief,
                          "vignettiert (%)": 100 * s.vignetted_fraction})
        except (rt.RaytatouilleError, ValueError) as error:
            table.append({"Feld": field_label(i), "RMS (µm)": float("nan"), "GEO (µm)": float("nan"),
                          "vignettiert (%)": float("nan")})
            overview_errors.append(f"{field_label(i)}: {error}")
    st.dataframe(pd.DataFrame(table), hide_index=True, **STRETCH)
    if overview_errors:
        st.caption(overview_errors[0] + (" (gleiche Ursache bei weiteren Feldern)"
                                         if len(overview_errors) > 1 else ""))
