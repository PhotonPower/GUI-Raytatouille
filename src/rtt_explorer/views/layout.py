"""View "Layout"."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import raytatouille as rt
import streamlit as st

from ..colors import path_linestyle, wavelength_rgb
from ..context import AppContext
from ..drawing import draw_builder_sketch, draw_geometry_api, surface_extents
from ..model_table import ideal_lenses
from ..ui.common import STRETCH, show

TITLE = "Layout"


def render(ctx: AppContext) -> None:
    """Render the view "Layout"."""
    features = ctx.features
    comp = ctx.comp
    path_choice = ctx.path_choice
    field_ids = ctx.field_ids
    wl_ids = ctx.wl_ids
    wl_um = ctx.wl_um
    ref_wl = ctx.ref_wl
    epd_value = ctx.epd_value
    can_aim = ctx.can_aim
    builder_context = ctx.builder_context
    field_label = ctx.field_label
    aim_map = ctx.aim_map
    make_batch = ctx.make_batch
    source_ui = ctx.source_ui
    c1, c2, c3, c4 = st.columns(4)
    plane = c1.radio("Schnittebene", ["yz", "xz"], horizontal=True) if features.layout else "yz"
    kind = c2.radio("Strahlen", ["Fächer", "Hexapolar"], horizontal=True)
    if kind == "Fächer":
        n_rays = c3.slider("Strahlen im Fächer", 3, 41, 11)
    else:
        n_rays = c3.slider("Ringe (hexapolar)", 1, 8, 4)
    aim = aim_map[c4.radio("Aiming", list(aim_map), horizontal=True, key="aim_layout")]
    d1, d2, d3 = st.columns(3)
    sel_fields = d1.multiselect("Felder", field_ids, default=field_ids, format_func=field_label)
    wl_mode = d2.radio("Wellenlängen", ["Referenz", "alle (Farben)"], horizontal=True)
    show_lost = d3.checkbox("Verluste markieren", value=True)
    label_surfaces = d3.checkbox("Flächen beschriften", value=False)
    equal_scale = d3.checkbox("Gleiche Achsenskalierung", value=True)
    # The library traces one explicit path at a time; a beam splitter does not split rays at run time,
    # each branch is a path of its own. Drawing all paths shows both arms of an interferometer.
    path_names = list(comp.path_names)
    all_paths = len(path_names) > 1 and d1.checkbox(
        "Alle Pfade zeichnen", value=True, key="layout_all_paths",
        help="Die Bibliothek verfolgt jeden Pfad einzeln; ein Strahlteiler teilt die Strahlen nicht. "
             "Gezeichnet werden alle Pfade des Modells, in Referenzfarben je Pfad eine Farbe, in "
             "Spektralfarben je Pfad eine Linienart. Aus: nur der Pfad aus der Seitenleiste.")
    draw_paths = path_names if all_paths else [path_choice]

    if not features.paths:
        st.info("Strahlen im Layout brauchen `trace(..., record_path=True)` (nicht in dieser "
                "Bibliotheksversion).")
    if not features.layout and builder_context is None:
        st.info("Für Flächen und Linsen braucht diese Ansicht `raytatouille.layout` (PR #90). Es "
                "werden nur die Strahlen gezeigt; im Modus 'System bauen' gibt es eine Skizze.")

    src = source_ui("layout") if features.paths else {"free": False}
    bundles = []  # (recorded rays, colour, line style, field, wavelength)
    rays_errors = []
    cmap = plt.get_cmap("tab10")
    if features.paths and (sel_fields or src["free"]):
        wl_sel = [ref_wl] if wl_mode == "Referenz" else wl_ids
        for p, path in enumerate(draw_paths):
            try:
                for f in ([0] if src["free"] else sel_fields):
                    for w in wl_sel:
                        ray_batch, _, _ = make_batch(src, kind, n_rays, plane, f, w, aim, path)
                        _, recorded = rt.trace.trace(comp, ray_batch, path=path, record_path=True)
                        style = "-"
                        if wl_mode != "Referenz":
                            colour = wavelength_rgb(wl_um[w])
                            style = path_linestyle(p) if all_paths else "-"
                        elif all_paths:
                            colour = cmap(p % 10)
                        else:
                            colour = "tab:blue" if src["free"] else cmap(f % 10)
                        bundles.append((recorded, colour, style, f, w))
            except (rt.RaytatouilleError, ValueError) as error:
                rays_errors.append(f"Pfad „{path}“: {error}" if all_paths else str(error))
    for error in rays_errors:
        st.warning(f"Keine Strahlen: {error}")

    lat = 1 if plane == "yz" else 0
    fig, ax = plt.subplots(figsize=(11, 4.8))
    default_h = (epd_value / 2 * 1.3) if epd_value and math.isfinite(epd_value) else 10.0
    surfs_list = []
    if features.layout:
        surfs_list = rt.layout.surfaces(comp)
        est_sources = [b[0] for b in bundles]
        if features.paths and can_aim and any(sf.aperture is None for sf in surfs_list):
            # Heights of surfaces without aperture: from a bundle over all fields, independent of
            # the fields chosen for drawing.
            for path in draw_paths:
                try:
                    for f_all in field_ids:
                        rb, _, _ = make_batch({"free": False}, "Hexapolar", 6, plane, f_all, ref_wl, aim, path)
                        _, rp = rt.trace.trace(comp, rb, path=path, record_path=True)
                        est_sources.append(rp)
                except (rt.RaytatouilleError, ValueError):
                    pass
        est = surface_extents(surfs_list, est_sources) if est_sources else {}
        try:
            ideal = ideal_lenses(ctx.system.root) if features.model else {}
            draw_geometry_api(ax, comp, plane, est, default_h, label_surfaces, ideal)
        except (rt.RaytatouilleError, ValueError) as error:
            st.warning(f"Geometrie konnte nicht gezeichnet werden: {error}")
    elif builder_context is not None:
        draw_builder_sketch(builder_context["rows"], builder_context["epd"], ax)

    points_z, points_l = [], []
    for recorded, colour, style, _f, w in bundles:
        pos = np.asarray(recorded.position)
        z, lt = pos[:, :, 2], pos[:, :, lat]
        lw = 0.7 if wl_mode == "Referenz" else max(0.4, 1.8 - 0.55 * wl_ids.index(w))
        ax.plot(z.T, lt.T, style, color=colour, lw=lw)
        points_z.append(z[np.isfinite(z)])
        points_l.append(lt[np.isfinite(z)])
        if show_lost:
            lost = np.nonzero(np.asarray(recorded.lost_at) >= 0)[0]
            for i in lost:
                slot = int(recorded.lost_at[i]) + 1
                ax.plot(z[i, slot], lt[i, slot], "x", color="red", ms=5, mew=1.3)
    handles = []
    if bundles and wl_mode == "Referenz" and all_paths:
        handles = [plt.Line2D([], [], color=cmap(p % 10), label=path) for p, path in enumerate(draw_paths)]
    elif bundles and wl_mode == "Referenz" and not src["free"]:
        handles = [plt.Line2D([], [], color=cmap(f % 10), label=field_label(f)) for f in sel_fields]
    elif bundles and wl_mode != "Referenz":
        handles = [plt.Line2D([], [], color=wavelength_rgb(wl_um[w]), label=f"{wl_um[w]:.4f} µm")
                   for w in wl_ids]
        if all_paths:
            handles += [plt.Line2D([], [], color="gray", ls=path_linestyle(p), label=path)
                        for p, path in enumerate(draw_paths)]
    if handles:
        ax.legend(handles=handles, fontsize=7, loc="upper left", ncol=2)

    zoom = False
    if bundles:
        zoom = st.checkbox("Auf die Bildebene zoomen", value=False)
    if zoom:
        z_img = float(np.nanmean([np.asarray(b[0].position)[:, -1, 2] for b in bundles]))
        width = st.slider("Ausschnitt vor der Bildebene (mm)", 1.0, 200.0, 20.0)
        ax.set_xlim(z_img - width, z_img + 0.1 * width)
        zs, ls = np.concatenate(points_z), np.concatenate(points_l)
        window = (zs >= z_img - width) & (zs <= z_img + 0.1 * width)
        if window.any():
            span = max(float(np.abs(ls[window]).max()) * 1.2, 1e-3)
            ax.set_ylim(-span, span)
    elif equal_scale:
        ax.set_aspect("equal", adjustable="datalim")
    if not zoom:
        ax.autoscale_view()
    ax.axhline(0, color="gray", lw=0.5, ls="--")
    ax.set_xlabel("z / mm")
    ax.set_ylabel(("y" if plane == "yz" else "x") + " / mm")
    show(fig)

    if bundles:
        lost_counts: dict[str, int] = {}
        total_rays = 0
        for recorded, *_ in bundles:
            total_rays += len(recorded.lost_at)
            events = np.asarray(recorded.event_surfaces)
            for j in np.asarray(recorded.lost_at):
                if j >= 0:
                    sid = comp.surface_ids[int(events[int(j)])]
                    lost_counts[sid] = lost_counts.get(sid, 0) + 1
        if lost_counts:
            st.markdown("**Verlorene Strahlen je Fläche**")
            st.dataframe(pd.DataFrame({"Fläche": list(lost_counts), "Strahlen": list(lost_counts.values()),
                                       "Anteil (%)": [100 * v / total_rays for v in lost_counts.values()]}),
                         hide_index=True, **STRETCH)
        else:
            st.caption(f"Alle {total_rays} gezeichneten Strahlen erreichen die Bildebene.")
