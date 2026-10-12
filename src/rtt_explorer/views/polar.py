"""View "Polarisation"."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import raytatouille as rt
import streamlit as st

from ..context import AppContext
from ..pupil_points import jones_text, nearest_index
from ..ui.common import STRETCH, run, show, show_result_notes

TITLE = "Polarisation"

JONES_BASES = {"Doppelpol": "DOUBLE_POLE", "Dipol": "DIPOLE"}


def render(ctx: AppContext) -> None:
    """Render the view "Polarisation"."""
    features = ctx.features
    comp = ctx.comp
    path_choice = ctx.path_choice
    field_ids = ctx.field_ids
    wl_ids = ctx.wl_ids
    wl_um = ctx.wl_um
    ref_wl = ctx.ref_wl
    field_label = ctx.field_label
    wl_label = ctx.wl_label
    aim_map = ctx.aim_map
    make_batch = ctx.make_batch
    source_ui = ctx.source_ui
    if not features.polar:
        st.info("Die installierte Bibliotheksversion hat kein `raytatouille.polar` (ab 0.4).")
    else:
        polar = rt.polar
        c1, c2, c3, c4 = st.columns(4)
        f = c1.selectbox("Feld", field_ids, format_func=field_label)
        w = c2.selectbox("Wellenlänge", wl_ids, index=ref_wl, format_func=wl_label)
        rings = c3.slider("Ringe (hexapolar)", 1, 15, 6)
        aim = aim_map[c4.radio("Aiming", list(aim_map), horizontal=True, key="aim_polar")]
        s1, s2 = st.columns([2, 2])
        source = s1.radio("Quelle", ["Unpolarisiert", "Linear", "Rechtszirkular (S₃ > 0)",
                                      "Linkszirkular (S₃ < 0)"], horizontal=True)
        angle = 0.0
        if source == "Linear":
            angle = s2.slider("Polarisationswinkel (° von x nach y)", 0, 180, 0)

        def source_vector() -> np.ndarray | None:
            if source == "Unpolarisiert":
                return None
            if source == "Linear":
                a = math.radians(angle)
                return np.array([math.cos(a), math.sin(a), 0.0], dtype=complex)
            sign = -1.0 if source.startswith("Rechts") else 1.0  # (1, -i)/sqrt2 gives S3 > 0
            return np.array([1.0, sign * 1j, 0.0], dtype=complex) / math.sqrt(2.0)

        psrc = source_ui("polar")

        def traced(wavelength: int, ring_count: int):
            batch, bx, by = make_batch(psrc, "Hexapolar", ring_count, "yz", f, wavelength, aim)
            rt.trace.trace(comp, batch, path=path_choice)
            vec = source_vector()
            e_state = None if vec is None else polar.transverse_polarization(batch, vec)
            return batch, e_state, bx, by

        try:
            batch, e_state, bx, by = traced(w, rings)
        except (rt.RaytatouilleError, ValueError) as error:
            st.error(f"Strahlverfolgung: {error}")
            batch = None
        if batch is not None:
            alive = np.asarray(batch.status) == int(rt.trace.RayStatus.ALIVE)
            trans = polar.transmission(batch, e_state)
            diat = polar.diattenuation(batch).value
            ret = np.degrees(polar.retardance(batch).value)
            st_par = polar.stokes(batch, e_state, [1.0, 0.0, 0.0]) if e_state is not None else None
            n_alive = int(alive.sum())
            if n_alive == 0:
                st.warning("Kein Strahl erreicht die Bildebene.")
            else:
                m = st.columns(5)
                m[0].metric("Mittlere Transmission", f"{trans[alive].mean():.4f}")
                m[1].metric("Min / Max", f"{trans[alive].min():.4f} / {trans[alive].max():.4f}")
                m[2].metric("Mittlere Diattenuation", f"{diat[alive].mean():.4f}")
                defined = alive & np.isfinite(ret)
                m[3].metric("Retardance (Ø, Grad)", f"{ret[defined].mean():.2f}" if defined.any() else "–",
                            help="Nur für Strahlen definiert, die in ihrer Einfallsrichtung austreten "
                                 "(Platten, Wellenplatten, ideale Elemente), nicht für fokussierte Strahlen.")
                m[4].metric("Strahlen angekommen", f"{n_alive}/{len(alive)}")

                panels = [("Transmission (Leistung)", trans, "viridis"),
                          ("Diattenuation", diat, "magma")]
                if (alive & np.isfinite(ret)).any():
                    panels.append(("Retardance (Grad)", ret, "twilight"))
                if st_par is not None:
                    s0 = np.where(st_par[:, 0] > 0, st_par[:, 0], np.nan)
                    panels.append(("Zirkularität S₃ / S₀", st_par[:, 3] / s0, "coolwarm"))
                px, py = bx, by
                cols = st.columns(2)
                for k, (title, values, cmap_name) in enumerate(panels):
                    with cols[k % 2]:
                        fig, ax = plt.subplots(figsize=(5, 4.3))
                        mask = alive & np.isfinite(values)
                        sc = ax.scatter(px[mask], py[mask], c=values[mask], s=26, cmap=cmap_name)
                        fig.colorbar(sc, ax=ax, format="%.5g")
                        ax.set_aspect("equal")
                        ax.set_xlabel("x am Start / mm" if psrc["free"] else "px")
                        ax.set_ylabel("y am Start / mm" if psrc["free"] else "py")
                        ax.set_title(title + (" über dem Bündel" if psrc["free"] else " über der Pupille"))
                        show(fig)
                if st_par is not None:
                    w_s = trans[alive] / trans[alive].sum()
                    mean_s = (st_par[alive] * w_s[:, None]).sum(axis=0)
                    dop = math.sqrt(mean_s[1] ** 2 + mean_s[2] ** 2 + mean_s[3] ** 2) / mean_s[0]
                    st.markdown("**Mittlerer Stokes-Vektor am Bild** (Achse e₁ = globales x, "
                                "gewichtet mit der Transmission)")
                    st.dataframe(pd.DataFrame({"S₀": [mean_s[0]], "S₁/S₀": [mean_s[1] / mean_s[0]],
                                               "S₂/S₀": [mean_s[2] / mean_s[0]],
                                               "S₃/S₀": [mean_s[3] / mean_s[0]], "Polarisationsgrad": [dop]}),
                                 hide_index=True, **STRETCH)
            st.markdown("**Transmission je Wellenlänge** (gleiches Feld und gleiche Quelle, hexapolar 4)")
            rows_t = []
            for wi in wl_ids:
                try:
                    b2, e2, _, _ = traced(wi, 4)
                    alive2 = np.asarray(b2.status) == int(rt.trace.RayStatus.ALIVE)
                    t2 = polar.transmission(b2, e2)
                    rows_t.append({"Wellenlänge (µm)": wl_um[wi],
                                   "Mittlere Transmission": float(t2[alive2].mean()) if alive2.any()
                                   else float("nan")})
                except (rt.RaytatouilleError, ValueError):
                    rows_t.append({"Wellenlänge (µm)": wl_um[wi], "Mittlere Transmission": float("nan")})
            table_t = pd.DataFrame(rows_t)
            a, b = st.columns([1, 1])
            a.dataframe(table_t, hide_index=True, **STRETCH)
            fig, ax = plt.subplots(figsize=(5, 3))
            ax.plot(table_t["Wellenlänge (µm)"], table_t["Mittlere Transmission"], "o-")
            ax.set_xlabel("Wellenlänge / µm")
            ax.set_ylabel("Transmission")
            ax.grid(alpha=0.3)
            with b:
                show(fig)
            st.caption("Konventionen (Fresnel, Händigkeit, PRT-Matrix) stehen in docs/architecture.md "
                       "und ADR 0021. Coatings wirken nur, wenn der Coating-Katalog aktiv ist.")
        if features.jones:
            _jones(ctx, f, w, aim, psrc, source_vector())


def _jones(ctx: AppContext, f: int, w: int, aim, psrc: dict, vec) -> None:
    """Jones pupil of the library (ADR 0034): diattenuation and physical retardance per pupil point, also
    for focused beams, and the Stokes map of the chosen polarized source."""
    st.markdown("**Jones-Pupille** (Bibliothek: Diattenuation und physikalische Retardance, auch für "
                "fokussierte Strahlen)")
    an = rt.analysis
    c1, c2 = st.columns(2)
    n = c1.slider("Raster (n × n Pupillenpunkte)", 5, 41, 17, step=2, key="jones_grid")
    basis = JONES_BASES[c2.radio("Ausgangsbasis", list(JONES_BASES), horizontal=True, key="jones_basis",
                                 help="Doppelpol: singulär nur entgegen dem Hauptstrahl (Vorgabe); "
                                      "Dipol: Basis nach Lam mit Polen bei ±y′.")]
    if psrc["free"]:
        # Start-ray form (also for folded paths): the ray nearest to the beam axis is the chief ray.
        batch, bx, by = ctx.make_batch(psrc, "Hexapolar", (n - 1) // 2, "yz", f, w, aim)
        kwargs = {"start": batch, "chief": nearest_index(list(bx), list(by))}
    else:
        kwargs = {"field": f, "wavelength": w, "rays": f"grid:{n}", "aiming": aim}
    jp = run("Jones-Pupille", an.jones_pupil, ctx.comp, ctx.path_choice, basis=getattr(an.JonesBasis, basis),
             **kwargs)
    if jp is None:
        if not psrc["free"]:
            st.caption("Gefaltete oder gekippte Pfade: Strahlquelle „Kollimiertes Bündel (frei)“ wählen.")
        return
    alive = np.asarray(jp.status) == int(rt.trace.RayStatus.ALIVE)
    if not alive.any():
        st.warning("Kein Pupillenpunkt erreicht die Bildfläche.")
        return
    if psrc["free"]:
        x, y, xlabel, ylabel = bx, by, "x am Start / mm", "y am Start / mm"
    else:
        x, y, xlabel, ylabel = np.asarray(jp.px), np.asarray(jp.py), "px", "py"
    diat = np.asarray(jp.diattenuation, dtype=float)
    ret = np.degrees(np.asarray(jp.retardance, dtype=float))
    m = st.columns(4)
    m[0].metric("Transmission (unpolarisiert, Ø)", f"{np.nanmean(np.asarray(jp.transmission)[alive]):.4f}")
    m[1].metric("Diattenuation max", f"{np.nanmax(diat[alive]):.4f}")
    m[2].metric("Retardance max", f"{np.nanmax(ret[alive]):.3f} °")
    m[3].metric("Pupillenpunkte", f"{int(alive.sum())}/{len(alive)}")
    # Fixed colour ranges: an automatic range would show rounding noise of a uniform map as a pattern.
    tiny = 1e-6
    panels = [("Diattenuation D", diat, "magma", (0.0, max(float(np.nanmax(diat[alive])), tiny))),
              ("Retardance (Grad)", ret, "magma", (0.0, max(float(np.nanmax(ret[alive])), tiny)))]
    if vec is not None:
        stokes = run("Stokes-Karte", an.stokes_pupil, jp, complex(vec[0]), complex(vec[1]))
        if stokes is not None:
            s0 = np.asarray(stokes.s0, dtype=float)
            s0 = np.where(s0 > 0, s0, np.nan)
            panels += [("Zirkularität S₃ / S₀ am Ausgang", np.asarray(stokes.s3) / s0, "coolwarm", (-1.0, 1.0)),
                       ("Orientierung der Ellipse (Grad)", np.degrees(np.asarray(stokes.orientation)), "twilight",
                        (0.0, 180.0))]
    cols = st.columns(2)
    for k, (title, values, cmap_name, (vmin, vmax)) in enumerate(panels):
        with cols[k % 2]:
            fig, ax = plt.subplots(figsize=(5, 4.3))
            mask = alive & np.isfinite(values)
            sc = ax.scatter(x[mask], y[mask], c=values[mask], s=26, cmap=cmap_name, vmin=vmin, vmax=vmax)
            fig.colorbar(sc, ax=ax, format="%.5g")
            ax.set_aspect("equal")
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            show(fig)
    centre = nearest_index(list(jp.px), list(jp.py)) if not psrc["free"] else kwargs["chief"]
    j = np.asarray(jp.j)[centre]
    st.markdown("**Jones-Matrix am Hauptstrahl** (Zeilen: Ausgang x′, y′; Spalten: Eingang x, y)")
    st.dataframe(pd.DataFrame([[jones_text(v) for v in row] for row in j], index=["x′", "y′"],
                              columns=["x", "y"]), **STRETCH)
    st.caption("J = exp(−2πi·w·λ_ref/λ)·Bᵀ_aus·P·B_ein der Bibliothek; Eingangsbasis am Hauptstrahl x_in, y_in. "
               "Die Stokes-Karte nimmt die gewählte Quelle in dieser Basis.")
    show_result_notes(ctx.comp, jp, "jones_pupil", "jones_pupil")

