"""View "Verzeichnung & Feldkrümmung"."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from raytatouille import analysis as an
from raytatouille import plot as rtplot

from ..context import AppContext
from ..ui.common import STRETCH, run, show

TITLE = "Verzeichnung & Feldkrümmung"


def render(ctx: AppContext) -> None:
    """Render the view "Verzeichnung & Feldkrümmung"."""
    comp = ctx.comp
    path_choice = ctx.path_choice
    samples = st.slider("Feldstützstellen", 3, 41, 11)
    dist = run("Verzeichnung", an.distortion, comp, path=path_choice, samples=samples)
    curv = run("Feldkrümmung", an.field_curvature, comp, path=path_choice, samples=samples)
    a, b = st.columns(2)
    if dist is not None:
        with a:
            fig, ax = plt.subplots(figsize=(5.5, 4.5))
            rtplot.distortion(dist, ax)
            show(fig)
            st.dataframe(pd.DataFrame({"rel. Feld": dist.fraction, "Verzeichnung (%)": dist.percent,
                                       "reale Höhe (mm)": dist.real_height,
                                       "paraxiale Höhe (mm)": dist.paraxial_height}),
                         hide_index=True, **STRETCH)
    if curv is not None:
        with b:
            fig, ax = plt.subplots(figsize=(5.5, 4.5))
            rtplot.field_curvature(curv, ax)
            show(fig)
            st.dataframe(pd.DataFrame({"rel. Feld": curv.fraction, "tangential (mm)": curv.tangential,
                                       "sagittal (mm)": curv.sagittal,
                                       "Astigmatismus (µm)": 1000 * (np.asarray(curv.tangential)
                                                                    - np.asarray(curv.sagittal))}),
                         hide_index=True, **STRETCH)
