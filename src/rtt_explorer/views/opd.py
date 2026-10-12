"""View "OPD / Wellenfront"."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from raytatouille import analysis as an
from raytatouille import plot as rtplot

from ..context import AppContext
from ..diffraction import marechal_strehl, zernike_rows
from ..ui.common import STRETCH, run, show, show_result_notes

TITLE = "OPD / Wellenfront"

ZERNIKE_TERMS = [15, 37, 66]  # complete up to radial order n = 4, 6 and 10


def render(ctx: AppContext) -> None:
    """Render the view "OPD / Wellenfront"."""
    comp = ctx.comp
    path_choice = ctx.path_choice
    field_ids = ctx.field_ids
    wl_ids = ctx.wl_ids
    field_label = ctx.field_label
    wl_label = ctx.wl_label
    wavefront = ctx.features.wavefront
    c1, c2, c3, c4 = st.columns(4)
    f = c1.selectbox("Feld", field_ids, format_func=field_label)
    w = c2.selectbox("Wellenlänge", [None] + wl_ids,
                     format_func=lambda i: "Referenz" if i is None else wl_label(i))
    grid = c3.slider("Gitter", 9, 81, 33, step=2)
    shift = c4.number_input("Fokusverschiebung (mm)", value=0.0, step=0.001, format="%.4f", key="opd_focus",
                            disabled=not wavefront,
                            help="Verschiebt den Mittelpunkt der Referenzkugel entlang des Hauptstrahls "
                                 "(positiv in Lichtrichtung)." if wavefront else
                                 "Erst ab Raytatouille 0.8 (focus_shift).")
    extra = {"focus_shift": shift} if wavefront else {}
    opd = run("OPD-Karte", an.opd_map, comp, path=path_choice, field=f, wavelength=w, grid=grid, **extra)
    if opd is None:
        return
    fit = _zernike_fit(ctx, f, w, shift) if wavefront else None
    m = st.columns(4)
    m[0].metric("RMS", f"{opd.rms:.4f} Wellen")
    m[1].metric("PV", f"{opd.pv:.4f} Wellen")
    if fit is not None:
        m[2].metric("σ um den besten Fokus", f"{fit.sigma_bf:.4f} Wellen",
                    help="Standardabweichung der Wellenfront ohne Kolben, Kippung und Defokus (Z1 bis Z4), "
                         "aus dem Zernike-Fit der Bibliothek.")
        m[3].metric("Strehl (Maréchal)", f"{fit.strehl:.3f}",
                    help="exp(−(2π·σ_bf·λ_ref/λ)²) aus rt.analysis.zernike_fit, gut bis etwa 0,1. "
                         "Die Strehlzahl aus der Beugungs-PSF zeigt die Ansicht Beugung.")
    elif not wavefront:
        lam = ctx.wl_um[ctx.ref_wl if w is None else w]
        # GUI approximation (older library without Zernike fit): S = exp(-(2 pi RMS lambda_ref / lambda)^2)
        strehl = marechal_strehl(opd.rms, ctx.wl_um[ctx.ref_wl], lam)
        m[3].metric("Strehl (Maréchal, Näherung)", f"{strehl:.3f}",
                    help="Näherung der Oberfläche: exp(−(2π·RMS·λ_ref/λ)²), gilt für kleine Fehler.")
    a, b = st.columns(2)
    with a:
        fig, ax = plt.subplots(figsize=(5.5, 5))
        rtplot.opd_map(opd, ax)
        show(fig)
    with b:
        fan = run("OPD-Fan", an.opd_fan, comp, path=path_choice, field=f, wavelength=w, points=41, **extra)
        if fan is not None:
            fig, ax = plt.subplots(figsize=(5.5, 5))
            rtplot.opd_fan(fan, ax)
            show(fig)
    show_result_notes(comp, opd, "opd_map", "opd_map")
    if fit is not None:
        _zernike_table(comp, fit)


def _zernike_fit(ctx: AppContext, field: int, wavelength: int | None, shift: float):
    """Zernike fit of the pupil function (64 x 64 cells) of the library, or None after an error."""
    terms = st.session_state.get("opd_terms", ZERNIKE_TERMS[1])
    pupil = run("Pupillenfunktion", an.pupil_function, ctx.comp, path=ctx.path_choice, field=field,
                wavelength=wavelength, focus_shift=shift)
    if pupil is None:
        return None
    return run("Zernike-Fit", an.zernike_fit, pupil, terms=terms)


def _zernike_table(comp, fit) -> None:
    with st.expander("Zernike-Koeffizienten (Noll)"):
        st.selectbox("Anzahl Terme", ZERNIKE_TERMS, index=1, key="opd_terms")
        nm = [an.noll_to_nm(j) for j in range(1, len(fit.coefficients) + 1)]
        table = pd.DataFrame(zernike_rows(list(fit.coefficients), [(k.n, k.m) for k in nm]))
        st.dataframe(table, hide_index=True, **STRETCH,
                     column_config={"Koeffizient (Wellen)": st.column_config.NumberColumn(format="%.5f")})
        st.caption(f"Orthonormale Zernike-Polynome nach Noll, Koeffizienten in Wellen bei λ_ref. "
                   f"σ = {fit.sigma:.4f} Wellen (ohne Kolben), Rest-RMS des Fits {fit.residual_rms:.2e} Wellen, "
                   f"{fit.cells} Zellen.")
        st.download_button("Koeffizienten als CSV", table.to_csv(index=False).encode(), file_name="zernike.csv",
                           mime="text/csv")
    show_result_notes(comp, fit, "zernike", "zernike")
