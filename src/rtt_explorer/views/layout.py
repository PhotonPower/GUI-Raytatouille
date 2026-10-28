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
from ..layout_geometry import exit_segments, stub_length
from ..layout_zoom import Window, checked_window, fit_aspect, image_plane_z, image_window, source_point, source_window
from ..model_table import ideal_lenses
from ..ui.common import STRETCH, show

TITLE = "Layout"

ZOOM_KEYS = ("z0", "z1", "l0", "l1")  # widget keys layout_zoom_<name> of the window fields


def _show_window(mode: str, window: Window) -> None:
    """Set the view mode and the window fields; the fields are not created yet in this run."""
    st.session_state["layout_view_mode"] = mode
    st.session_state["layout_view_box"] = window
    for name, value in zip(ZOOM_KEYS, window):
        st.session_state[f"layout_zoom_{name}"] = float(value)


def box_aspect(fig, ax) -> float:
    """Width over height of the axes box on the figure."""
    box, (fig_w, fig_h) = ax.get_position(), fig.get_size_inches()
    return float(box.width * fig_w / (box.height * fig_h))


def _zoom_controls(ax, fig, bundles, lat: int, lat_name: str, points_z, points_l) -> Window | None:
    """Buttons "Gesamtes System", "Auf Quelle zoomen" and "Auf Bildebene zoomen" plus a window to
    choose by hand.

    Returns the window to draw, or ``None`` for the whole system. A window applies until another
    button is pressed; the source window follows the field "Quellfenster", the image window the
    field "Bildfenster". ``points_z`` and ``points_l`` are the drawn ray points (z and lateral)."""
    ax.autoscale_view()
    full = (*ax.get_xlim(), *ax.get_ylim())
    point = source_point([np.asarray(b[0].position) for b in bundles], lat)
    z_image = image_plane_z([(np.asarray(b[0].position), np.asarray(b[0].lost_at)) for b in bundles])
    ss = st.session_state
    ss.setdefault("layout_view_mode", "all")
    ss.setdefault("layout_view_box", full)
    for name, value in zip(ZOOM_KEYS, ss["layout_view_box"]):
        ss.setdefault(f"layout_zoom_{name}", float(value))
    ss.setdefault("layout_zoom_half", 3.0)
    ss.setdefault("layout_zoom_image_width", 20.0)

    def source_view() -> Window:
        assert point is not None
        return source_window(point[0], point[1], float(ss["layout_zoom_half"]), box_aspect(fig, ax))

    def image_view() -> Window:
        assert z_image is not None
        return image_window(z_image, float(ss["layout_zoom_image_width"]), points_z, points_l, full[2:])

    b1, b2, b3 = st.columns(3)
    if b1.button("Gesamtes System", key="layout_view_all",
                 help="Zeigt alles, was gezeichnet ist."):
        _show_window("all", full)
    if b2.button("Auf Quelle zoomen", key="layout_view_source", disabled=point is None,
                 help="Fenster um den Startpunkt der gezeichneten Strahlen (die Quelle). Ohne Strahlen nicht "
                      "verfügbar."):
        _show_window("source", source_view())
    if b3.button("Auf Bildebene zoomen", key="layout_view_image", disabled=z_image is None,
                 help="Der Bereich vor der Bildebene, in der Höhe der Strahlen dort. Nicht verfügbar, wenn kein "
                      "Strahl die Bildebene erreicht."):
        _show_window("image", image_view())
    _, c2, c3 = st.columns(3)
    c2.number_input("Quellfenster ± mm", 0.01, 1.0e4, step=0.5, key="layout_zoom_half", disabled=point is None,
                    help="Halbe Breite des Fensters um die Quelle in z.")
    c3.number_input("Bildfenster vor der Bildebene (mm)", 0.01, 1.0e4, step=5.0, key="layout_zoom_image_width",
                    disabled=z_image is None,
                    help="Breite des Ausschnitts vor der Bildebene; dahinter bleibt ein Zehntel davon.")
    with st.expander("Ausschnitt wählen"):
        e1, e2, e3, e4 = st.columns(4)
        z0 = e1.number_input("z von (mm)", format="%.3f", key="layout_zoom_z0")
        z1 = e2.number_input("z bis (mm)", format="%.3f", key="layout_zoom_z1")
        l0 = e3.number_input(f"{lat_name} von (mm)", format="%.3f", key="layout_zoom_l0")
        l1 = e4.number_input(f"{lat_name} bis (mm)", format="%.3f", key="layout_zoom_l1")
        if st.button("Ausschnitt übernehmen", key="layout_view_apply"):
            try:
                window = checked_window(z0, z1, l0, l1)
            except ValueError as error:
                st.error(str(error))
            else:
                ss["layout_view_mode"], ss["layout_view_box"] = "box", window
    mode = ss["layout_view_mode"]
    if mode == "source" and point is not None:
        return source_view()
    if mode == "image":
        if z_image is None:
            st.caption("Kein Strahl erreicht die Bildebene; es wird das gesamte System gezeigt.")
            return None
        return image_view()
    if mode == "box":
        return tuple(ss["layout_view_box"])  # type: ignore[return-value]
    return None


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
    # A recorded path ends at its last event; rays leaving a mirror or a total internal reflection
    # there would end in the air. Continue them faintly, except behind a detector.
    stubs_drawn = False
    length = stub_length(points_z, points_l)
    for recorded, colour, style, _f, w in bundles:
        events = np.asarray(recorded.event_surfaces)
        if not surfs_list or not len(events) or surfs_list[int(events[-1])].kind == "detector":
            continue
        start, end = exit_segments(recorded.position, recorded.direction, recorded.lost_at, length)
        if len(start):
            lw = 0.7 if wl_mode == "Referenz" else max(0.4, 1.8 - 0.55 * wl_ids.index(w))
            ax.plot(np.vstack([start[:, 2], end[:, 2]]), np.vstack([start[:, lat], end[:, lat]]), style,
                    color=colour, lw=lw, alpha=0.35)
            stubs_drawn = True
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

    view_window = _zoom_controls(ax, fig, bundles, lat, "y" if plane == "yz" else "x", points_z, points_l)
    if view_window is not None:
        if equal_scale:  # widen the shorter direction so that the scales stay equal
            view_window = fit_aspect(view_window, box_aspect(fig, ax))
        ax.set_xlim(view_window[0], view_window[1])
        ax.set_ylim(view_window[2], view_window[3])
    elif equal_scale:
        ax.set_aspect("equal", adjustable="datalim")
    if view_window is None:
        ax.autoscale_view()
    ax.axhline(0, color="gray", lw=0.5, ls="--")
    ax.set_xlabel("z / mm")
    ax.set_ylabel(("y" if plane == "yz" else "x") + " / mm")
    show(fig)
    if stubs_drawn:
        st.caption("Blass: Austrittsrichtung nach dem letzten Ereignis des Pfads (die Länge dient nur der "
                   "Orientierung). Hinter einem Detektor endet der Pfad, dort gibt es kein Stück.")

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
