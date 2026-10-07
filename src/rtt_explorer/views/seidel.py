"""View "Seidel"."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from raytatouille import analysis as an

from ..context import AppContext
from ..ui.common import STRETCH, run, show

TITLE = "Seidel"


def render(ctx: AppContext) -> None:
    """Render the view "Seidel"."""
    comp = ctx.comp
    path_choice = ctx.path_choice
    wl_ids = ctx.wl_ids
    wl_um = ctx.wl_um
    ref_wl = ctx.ref_wl
    wl_label = ctx.wl_label
    c1, c2 = st.columns(2)
    first = c1.selectbox("Farbpaar: erste", wl_ids, index=0, format_func=wl_label, key="sf")
    second = c2.selectbox("Farbpaar: zweite", wl_ids, index=len(wl_ids) - 1, format_func=wl_label, key="ss")
    pair = (first, second) if first != second else None
    seidel = run("Seidel-Summen", an.seidel, comp, path=path_choice, pair=pair)
    if seidel is not None:
        total = seidel.sum
        names = {"S_I Sphärische Aberration": total.s1, "S_II Koma": total.s2, "S_III Astigmatismus": total.s3,
                 "S_IV Petzval": total.s4, "S_V Verzeichnung": total.s5,
                 "C_L Farblängsfehler": total.c_l, "C_T Farbquerfehler": total.c_t}
        st.dataframe(pd.DataFrame({"Summe": list(names), "Wert (mm)": list(names.values())}),
                     hide_index=True, **STRETCH)
        w040 = total.s1 / 8.0 / (wl_um[ref_wl] * 1e-3)
        st.caption(f"W040 = S_I / 8 = {w040:.3f} Wellen bei {wl_um[ref_wl]:.4f} µm.")
        surf = seidel.surfaces
        ids = [comp.surface_ids[int(i)] for i in surf.surface]
        per = pd.DataFrame({"Fläche": ids, "S_I": surf.s1, "S_II": surf.s2, "S_III": surf.s3,
                            "S_IV": surf.s4, "S_V": surf.s5, "C_L": surf.c_l, "C_T": surf.c_t})
        st.dataframe(per, hide_index=True, **STRETCH)
        fig, ax = plt.subplots(figsize=(8, 4))
        x = np.arange(len(ids))
        for k, col in enumerate(["S_I", "S_II", "S_III", "S_IV", "S_V"]):
            ax.bar(x + (k - 2) * 0.16, per[col], width=0.16, label=col)
        ax.set_xticks(x, ids)
        ax.axhline(0, color="k", lw=0.6)
        ax.set_ylabel("Beitrag / mm")
        ax.set_title("Seidel-Beiträge je Fläche")
        ax.legend(ncol=5)
        show(fig)
