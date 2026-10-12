"""View "Beugung": diffraction PSF, MTF, encircled energy and Strehl ratio through focus (library 0.8, M6)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from raytatouille import analysis as an
from raytatouille import plot as rtplot

from ..context import AppContext
from ..diffraction import airy_radius_um, ee_radii, focus_shifts, radius_at_energy, rayleigh_depth_mm
from ..ui.common import fmt, run, show, show_result_notes

TITLE = "Beugung"

GRIDS = [32, 64, 128]  # pupil cells per side; about (pi/4) N^2 rays per wavelength
KINDS = ["PSF", "MTF", "Eingeschlossene Energie", "Through-Focus"]
EE_CENTRES = {"Referenzpunkt C′": "REFERENCE", "lineare Phase (folgt einer Kippung)": "LINEAR_PHASE"}


def render(ctx: AppContext) -> None:
    """Render the view "Beugung"."""
    if not ctx.features.diffraction:
        st.info("Die installierte Bibliotheksversion rechnet keine Beugung (PSF, MTF; ab Raytatouille 0.8).")
        return
    c1, c2, c3, c4 = st.columns(4)
    f = c1.selectbox("Feld", ctx.field_ids, format_func=ctx.field_label, key="diff_field")
    w = c2.selectbox("Wellenlänge", [None] + ctx.wl_ids, key="diff_wl",
                     format_func=lambda i: "polychromatisch" if i is None else ctx.wl_label(i))
    grid = c3.selectbox("Pupillengitter", GRIDS, index=1, key="diff_grid", format_func=lambda n: f"{n} × {n}",
                        help="Zellen der Pupillenfunktion je Seite; feiner ist genauer und langsamer.")
    shift = c4.number_input("Fokusverschiebung (mm)", value=0.0, step=0.001, format="%.4f", key="diff_focus",
                            help="Entlang des Hauptstrahls, positiv in Lichtrichtung.")
    kind = st.radio("Auswertung", KINDS, horizontal=True, key="diff_kind")
    common = {"path": ctx.path_choice, "field": f, "grid": grid}
    wavelengths = None if w is None else [w]
    lam = ctx.wl_um[ctx.ref_wl if w is None else w]
    airy = airy_radius_um(lam, ctx.working_fnum)
    if kind == "PSF":
        _psf(ctx, common, wavelengths, shift, airy)
    elif kind == "MTF":
        _mtf(ctx, common, wavelengths, shift)
    elif kind == "Eingeschlossene Energie":
        _encircled_energy(ctx, common, wavelengths, shift, airy)
    else:
        _through_focus(ctx, common, w, lam)
    st.caption("Beugungsrechnung der Bibliothek aus der Pupillenfunktion (FFT bzw. Autokorrelation); "
               "polychromatisch mit den Gewichten der Wellenlängen im System.")


def _psf(ctx: AppContext, common: dict, wavelengths, shift: float, airy: float | None) -> None:
    psf = run("PSF", an.psf, ctx.comp, wavelengths=wavelengths, focus_shift=shift, **common)
    if psf is None:
        return
    step_um = 1000 * float(np.linalg.norm(np.asarray(psf.lattice)[:, 0]))
    m = st.columns(4)
    m[0].metric("Strehlzahl", f"{psf.strehl:.4f}", help="Intensität am Referenzpunkt C′ relativ zum fehlerfreien "
                                                         "System, aus der Beugungs-PSF der Bibliothek.")
    m[1].metric("Gitterabstand", f"{step_um:.3f} µm")
    m[2].metric("Airy-Radius (Näherung)", f"{airy:.2f} µm" if airy else "–", help="1,22 · λ · N_w")
    m[3].metric("Energieverlust am Rand", f"{100 * psf.edge_energy_deficit:.2f} %",
                help="Anteil der Pupillenenergie in angeschnittenen Randzellen.")
    a, b = st.columns([3, 2])
    log = b.checkbox("logarithmisch", value=True, key="diff_psf_log")
    full = step_um * psf.length / 2  # half width of the lattice, µm
    if airy:
        half = min(full, airy * b.slider("Ausschnitt ± (Airy-Radien)", 1, 40, 5, key="diff_psf_zoom"))
    else:
        half = full * b.slider("Ausschnitt (% des Gitters)", 1, 100, 100, key="diff_psf_zoom_rel") / 100
    with a:
        fig, ax = plt.subplots(figsize=(6, 5.2))
        rtplot.psf(psf, ax, log=log)
        ax.set_xlim(-half, half)
        ax.set_ylim(-half, half)
        ax.set_title(f"PSF, Strehl {psf.strehl:.4g}")
        show(fig)
    with b:
        xy = psf.positions() * 1000  # µm
        values = np.asarray(psf.intensity) / max(psf.peak.value, np.finfo(float).tiny)
        c = psf.length // 2
        fig, ax = plt.subplots(figsize=(4.5, 3.6))
        ax.plot(xy[c, :, 0], values[c, :], label="Schnitt entlang x")
        ax.plot(xy[:, c, 1], values[:, c], label="Schnitt entlang y")
        if airy:
            for sign in (-1, 1):
                ax.axvline(sign * airy, color="gray", ls="--", lw=0.8)
        ax.set_xlim(-half, half)
        ax.set_xlabel("Ort / µm")
        ax.set_ylabel("I / I_max")
        ax.grid(alpha=0.3)
        ax.legend(fontsize="small")
        show(fig)
    show_result_notes(ctx.comp, psf, "psf", "psf")


def _mtf(ctx: AppContext, common: dict, wavelengths, shift: float) -> None:
    mtf = run("MTF", an.mtf, ctx.comp, wavelengths=wavelengths, focus_shift=shift, **common)
    if mtf is None:
        return
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for name, curve in (("tangential", mtf.tangential), ("sagittal", mtf.sagittal)):
        ax.plot(curve.frequency, curve.modulation, label=name)
    ax.set_xlabel("Ortsfrequenz / (Linienpaare/mm)")
    ax.set_ylabel("MTF")
    ax.set_ylim(0.0, 1.05)
    ax.set_xlim(left=0.0)
    ax.grid(alpha=0.3)
    ax.legend()
    show(fig)
    rows = [{"Richtung": name, "Frequenz (Lp/mm)": float(nu), "MTF": float(v)}
            for name, curve in (("tangential", mtf.tangential), ("sagittal", mtf.sagittal))
            for nu, v in zip(curve.frequency, curve.modulation)]
    st.download_button("Kurven als CSV", pd.DataFrame(rows).to_csv(index=False).encode(), file_name="mtf.csv",
                       mime="text/csv")
    st.caption("Tangential: Verschiebung der Pupille in py (meridional für ein Feld auf der y-Achse), "
               "sagittal: in px.")
    show_result_notes(ctx.comp, mtf, "mtf", "mtf")


def _encircled_energy(ctx: AppContext, common: dict, wavelengths, shift: float, airy: float | None) -> None:
    centre_label = st.radio("Mittelpunkt der Kreise", list(EE_CENTRES), horizontal=True, key="diff_ee_centre")
    options = {"centre": getattr(an.EeCentre, EE_CENTRES[centre_label]), "wavelengths": wavelengths,
               "focus_shift": shift, **common}
    # The largest allowed radius is known only from a result: probe with radius 0, then sample up to it.
    probe = run("Eingeschlossene Energie", an.encircled_energy, ctx.comp, [0.0], **options)
    if probe is None:
        return
    ee = run("Eingeschlossene Energie", an.encircled_energy, ctx.comp, ee_radii(probe.radius_max, 200), **options)
    if ee is None:
        return
    radii, energy = list(ee.radii), list(ee.energy)
    m = st.columns(4)
    for col, level in zip(m, (0.5, 0.8, 0.9)):
        r = radius_at_energy(radii, energy, level)
        col.metric(f"Radius {int(100 * level)} %", "–" if r is None else f"{1000 * r:.2f} µm",
                   help="Linear zwischen den berechneten Radien interpoliert.")
    m[3].metric("größter Radius", f"{1000 * ee.radius_max:.2f} µm",
                help="Ein Viertel der kürzesten Periode der periodischen PSF (Grenze der Bibliothek).")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(np.asarray(radii) * 1000, energy)
    if airy and airy < 1000 * radii[-1]:
        ax.axvline(airy, color="gray", ls="--", lw=0.8, label=f"Airy-Radius (Näherung) {fmt(airy, 2)} µm")
        ax.legend()
    ax.set_xlabel("Radius / µm")
    ax.set_ylabel("eingeschlossene Energie")
    ax.set_ylim(0.0, 1.05)
    ax.set_xlim(left=0.0)
    ax.grid(alpha=0.3)
    show(fig)
    show_result_notes(ctx.comp, ee, "encircled_energy", "encircled_energy")


def _through_focus(ctx: AppContext, common: dict, w: int | None, lam: float) -> None:
    if w is None:
        st.caption("Through-Focus rechnet monochromatisch, hier bei der Referenzwellenlänge.")
    depth = rayleigh_depth_mm(lam, ctx.working_fnum)
    a, b = st.columns(2)
    if depth:
        factor = a.slider("Bereich ± (Vielfache der Rayleigh-Tiefe)", 1, 40, 4, key="diff_tf_factor",
                          help=f"Rayleigh-Tiefenschärfe δz = 2·λ·N_w² ≈ {1000 * depth:.2f} µm (Näherung).")
        half_range = factor * depth
    else:
        half_range = a.number_input("Bereich ± (mm)", 1e-4, 100.0, 0.1, format="%.4f", key="diff_tf_range")
    steps = b.slider("Fokuslagen", 5, 81, 41, step=2, key="diff_tf_steps")
    tf = run("Through-Focus", an.through_focus, ctx.comp, wavelength=w, shifts=focus_shifts(half_range, steps),
             **common)
    if tf is None:
        return
    shifts, strehl = np.asarray(tf.shifts), np.asarray(tf.strehl)
    best = int(np.argmax(strehl))
    m = st.columns(3)
    m[0].metric("Strehlzahl bei 0", f"{strehl[steps // 2]:.4f}")
    m[1].metric("beste Fokuslage", f"{1000 * shifts[best]:.2f} µm", help="Größte Strehlzahl der Stützstellen.")
    m[2].metric("Strehlzahl dort", f"{strehl[best]:.4f}")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(shifts * 1000, strehl, "o-", ms=3)
    if depth:
        ax.axvspan(-1000 * depth, 1000 * depth, color="gray", alpha=0.15, label="±δz (Rayleigh, Näherung)")
        ax.legend()
    ax.set_xlabel("Fokusverschiebung / µm")
    ax.set_ylabel("Strehlzahl")
    ax.set_ylim(0.0, 1.05)
    ax.grid(alpha=0.3)
    show(fig)
    show_result_notes(ctx.comp, tf, "through_focus", "through_focus")
