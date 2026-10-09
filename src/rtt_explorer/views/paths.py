"""View "Pfade & Ghosts": transmission per path, OPL difference of two paths and the ghost ranking."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import raytatouille as rt
import streamlit as st

from ..context import AppContext
from ..rays import collimated_batch
from ..ui.common import STRETCH, diagnostic_line, fmt, run, show

TITLE = "Pfade & Ghosts"


def render(ctx: AppContext) -> None:
    """Render the view "Pfade & Ghosts"."""
    if not ctx.features.path_eval:
        st.info("Die installierte Bibliotheksversion hat keine Pfadauswertung "
                "(`analysis.path_transmission`, ab 0.6).")
        return
    comp = ctx.comp
    c1, c2, c3 = st.columns(3)
    f = c1.selectbox("Feld", ctx.field_ids, format_func=ctx.field_label, key="paths_field")
    w = c2.selectbox("Wellenlänge", ctx.wl_ids, index=ctx.ref_wl, format_func=ctx.wl_label, key="paths_wl")
    rings = c3.slider("Ringe (hexapolar)", 1, 12, 4, key="paths_rings")
    src = ctx.source_ui("paths")

    def start_kwargs() -> tuple[dict, np.ndarray | None, np.ndarray | None]:
        """Keyword arguments for the start rays and the start coordinates for plots (free beam)."""
        if src["free"]:
            batch = collimated_batch("Hexapolar", rings, "yz", src["radius"], src["z0"], src["tx"], src["ty"], w)
            return {"start": batch}, np.asarray(batch.pos_x), np.asarray(batch.pos_y)
        return {"field": f, "wavelength": w, "rays": f"hexapolar:{rings}"}, None, None

    kwargs, start_x, start_y = start_kwargs()
    _transmission_table(comp, kwargs)
    if len(comp.path_names) >= 2:
        _opl_difference(ctx, kwargs, start_x, start_y, w)
    _ghosts(ctx, f, w, rings)


def _transmission_table(comp, kwargs: dict) -> None:
    st.markdown("**Transmission je Pfad** (Leistungsanteil der gestarteten Strahlen, verlorene zählen 0)")
    rows, notes = [], []
    for name in comp.path_names:
        try:
            t = rt.analysis.path_transmission(comp, name, **kwargs)
        except (rt.RaytatouilleError, ValueError) as error:
            rows.append({"Pfad": name, "Mittel": float("nan"), "Min": float("nan"), "Max": float("nan"),
                         "angekommen": "–", "meiste Verluste an": "", "Hinweis": str(error)})
            continue
        worst = t.losses.worst_surface
        rows.append({"Pfad": name, "Mittel": t.mean, "Min": t.min, "Max": t.max,
                     "angekommen": f"{t.rays_arrived}/{t.rays_launched}",
                     "meiste Verluste an": "" if worst is None else comp.surface_ids[int(worst)], "Hinweis": ""})
        notes += [f"{name}: {diagnostic_line(comp, d)}" for d in t.warnings]
    table = pd.DataFrame(rows)
    if not table["Hinweis"].astype(bool).any():
        table = table.drop(columns="Hinweis")
    st.dataframe(table, hide_index=True, **STRETCH,
                 column_config={k: st.column_config.NumberColumn(k, format="%.4f") for k in ("Mittel", "Min", "Max")})
    if len(rows) > 1 and np.isfinite(table["Mittel"]).any():
        fig, ax = plt.subplots(figsize=(8, 0.5 + 0.4 * len(rows)))
        ax.barh(table["Pfad"], table["Mittel"].fillna(0.0), color="tab:blue")
        ax.invert_yaxis()
        ax.set_xlabel("mittlere Transmission")
        ax.set_xlim(0, max(1.0, float(np.nanmax(table["Mittel"]))))
        ax.grid(alpha=0.3, axis="x")
        show(fig)
    if notes:
        with st.expander(f"Warnungen der Bibliothek ({len(notes)})"):
            for text in notes:
                st.write("- " + text)


def _opl_difference(ctx: AppContext, kwargs: dict, start_x, start_y, w: int) -> None:
    comp = ctx.comp
    st.markdown("**Optische Wegdifferenz zweier Pfade** (OPL_b − OPL_a auf der gemeinsamen Bildfläche)")
    names = list(comp.path_names)
    a, b = st.columns(2)
    path_a = a.selectbox("Pfad a", names, index=0, key="opl_a")
    path_b = b.selectbox("Pfad b", names, index=1, key="opl_b")
    if path_a == path_b:
        st.caption("Zwei verschiedene Pfade wählen.")
        return
    d = run("OPL-Differenz", rt.analysis.opl_difference, comp, path_a, path_b, **kwargs)
    if d is None:
        return
    pts = d.points
    alive = np.asarray(pts.status) == int(rt.trace.RayStatus.ALIVE)
    delta = np.asarray(pts.delta, dtype=float)
    wl_mm = ctx.wl_um[w] / 1000.0
    m = st.columns(3)
    m[0].metric("Δ Hauptstrahl", "–" if d.chief is None else f"{fmt(d.chief, 6)} mm")
    m[1].metric("Δ Hauptstrahl in Wellen", "–" if d.chief is None else fmt(d.chief / wl_mm, 3),
                help=f"Δ / λ mit λ = {ctx.wl_um[w]:.4f} µm (Vakuumwellenlänge)")
    m[2].metric("Strahlen auf beiden Pfaden", f"{int(alive.sum())}/{len(alive)}")
    if alive.any():
        x = start_x if start_x is not None else np.asarray(pts.px)
        y = start_y if start_y is not None else np.asarray(pts.py)
        fig, ax = plt.subplots(figsize=(5.5, 4.6))
        sc = ax.scatter(x[alive], y[alive], c=delta[alive] / wl_mm, s=30, cmap="coolwarm")
        fig.colorbar(sc, ax=ax, label="Δ / λ")
        ax.set_aspect("equal", adjustable="datalim")
        ax.set_xlabel("x am Start / mm" if start_x is not None else "px")
        ax.set_ylabel("y am Start / mm" if start_x is not None else "py")
        ax.set_title(f"{path_b} − {path_a}")
        show(fig)
    for text in sorted(set(diagnostic_line(comp, x) for x in d.warnings)):
        st.warning(text)


@st.cache_resource(show_spinner="Ghost-Pfade werden kompiliert …", max_entries=4)
def _ghost_system(system_key: str, base: str, _system, _lib, _coatings):
    return rt.compile_with_ghosts(_system, base, _lib, _coatings)


def _ghosts(ctx: AppContext, f: int, w: int, rings: int) -> None:
    st.markdown("**Ghosts** (Zwei-Reflexions-Ghosts des gewählten Pfads, ADR 0027 der Bibliothek)")
    if not ctx.features.ghosts:
        st.info("Die installierte Bibliotheksversion hat keine Ghost-Analyse (ab 0.6).")
        return
    if not ctx.can_aim:
        st.info("Das Ghost-Ranking startet die Strahlen über die Pupille und braucht deshalb eine Blende.")
        return
    c1, c2 = st.columns([1, 2])
    r0_um = c1.number_input("Auflösungsradius r₀ (µm)", min_value=0.1, value=5.0, step=1.0, key="ghost_r0",
                            help="Auflösung des Detektors; eine Modellwahl, keine Naturkonstante.")
    if not c2.checkbox("Ghost-Ranking berechnen", value=False, key="ghost_on",
                       help="Kompiliert alle Zwei-Reflexions-Ghosts und verfolgt sie; bei vielen Flächen "
                            "dauert das."):
        return
    try:
        ghosts = _ghost_system(ctx.system_key, ctx.path_choice, ctx.system, ctx.lib, ctx.coatings)
    except (rt.RaytatouilleError, ValueError) as error:
        st.error(f"Ghost-Pfade: {error}")
        return
    if len(ghosts.ghosts) == 0:
        st.info("Dieser Pfad hat keine Ghosts (weniger als zwei brechende Flächen).")
        return
    ranking = run("Ghost-Ranking", rt.analysis.ghost_ranking, ghosts, field=f, wavelength=w,
                  rays=f"hexapolar:{rings}", resolution_radius=r0_um / 1000.0)
    if ranking is None:
        return
    e = ranking.entries
    names = list(ghosts.system.path_names)
    ids = list(ghosts.system.surface_ids)
    table = pd.DataFrame({
        "Ghost": [names[int(p)] for p in np.asarray(e.path)],
        "Reflexion 1": [ids[int(s)] for s in np.asarray(e.surface_j)],
        "Reflexion 2": [ids[int(s)] for s in np.asarray(e.surface_i)],
        "rel. Bestrahlungsstärke": np.asarray(e.relative_irradiance, dtype=float),
        "rel. Leistung": np.asarray(e.relative_power, dtype=float),
        "RMS-Radius (µm)": 1000 * np.asarray(e.rms_radius, dtype=float),
        "Strahlen": np.asarray(e.rays_arrived),
        "Fokusversatz (mm)": np.asarray(e.focus_offset, dtype=float),
    })
    m = st.columns(3)
    m[0].metric("Ghosts", len(table))
    m[1].metric("Nutzbild: Leistung", fmt(ranking.base_power, 4))
    m[2].metric("Nutzbild: RMS-Radius", f"{1000 * ranking.base_rms_radius:.2f} µm")
    st.dataframe(table, hide_index=True, **STRETCH,
                 column_config={"rel. Bestrahlungsstärke": st.column_config.NumberColumn(format="%.3e"),
                                "rel. Leistung": st.column_config.NumberColumn(format="%.3e"),
                                "RMS-Radius (µm)": st.column_config.NumberColumn(format="%.1f"),
                                "Fokusversatz (mm)": st.column_config.NumberColumn(format="%.3f")})
    st.caption("Sortiert nach ρ = (P_g/P_b)·(r_b² + r₀²)/(r_g² + r₀²) der Bibliothek, geometrisch ohne Beugung. "
               "Ghosts mit wenigen angekommenen Strahlen bekommen fast den vollen Faktor; Spalte Strahlen prüfen. "
               "Reflexion 1 ist die hintere Fläche, an der das Licht zuerst zurückgeworfen wird, Reflexion 2 "
               "die vordere, die es wieder nach vorn schickt.")
    for text in sorted(set(diagnostic_line(ctx.comp, x) for x in ranking.warnings)):
        st.warning(text)
