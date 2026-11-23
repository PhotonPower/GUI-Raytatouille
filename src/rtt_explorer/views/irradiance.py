"""View "Bestrahlungsstärke": the irradiance (footprint) on any surface of a path (library 0.10, ADR 0048)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import raytatouille as rt
import streamlit as st

from ..context import AppContext
from ..detector_image import scaled
from ..irradiance_logic import cell_size_um, event_label, loss_rows, max_rays, visits
from ..irradiance_rays import (
    Traced,
    auto_extent,
    irradiance,
    irradiance_extent,
    path_events,
    trace_rays,
)
from ..ui.common import STRETCH, show

TITLE = "Bestrahlungsstärke"

RAY_STEPS = [1_000, 5_000, 10_000, 20_000, 50_000, 100_000, 200_000, 500_000, 1_000_000, 2_000_000, 4_000_000]
COLOUR_MAPS = ["inferno", "viridis", "magma", "hot", "gray"]
LOG_FLOOR = 1.0e-4
EXTENT_MODES = {"Aus den Strahlen": "auto", "Apertur der Fläche": "aperture", "Frei": "manual"}


# One entry only: 4 million rays hold about 2 GB.
@st.cache_resource(show_spinner="Strahlen werden berechnet …", max_entries=1)
def _traced(system_key: str, configuration: int | None, path: str, field: int, wavelength: int, n_rays: int,
            aim_name: str, surface: int, _comp, _aiming) -> Traced:
    """The rays of one setting; cached, so that changing the grid, the area or the colours does not trace again."""
    return trace_rays(_comp, path, field, wavelength, n_rays, _aiming, surface)


def _manual_extent(auto: tuple[float, float, float, float] | None):
    """The area typed in by hand, or None (with a message) if it is empty."""
    ss = st.session_state
    for name, value in zip(("x0", "x1", "y0", "y1"), auto or (-1.0, 1.0, -1.0, 1.0)):
        ss.setdefault(f"irr_{name}", float(value))
    c = st.columns(4)
    values = (c[0].number_input("x von (mm)", format="%.4f", key="irr_x0"),
              c[1].number_input("x bis (mm)", format="%.4f", key="irr_x1"),
              c[2].number_input("y von (mm)", format="%.4f", key="irr_y0"),
              c[3].number_input("y bis (mm)", format="%.4f", key="irr_y1"))
    if not (values[1] > values[0] and values[3] > values[2]):
        st.error("Bereich leer: es muss x von < x bis und y von < y bis gelten.")
        return None
    return values


def render(ctx: AppContext) -> None:
    """Render the view "Bestrahlungsstärke"."""
    if not ctx.features.irradiance:
        st.info("Die installierte Bibliotheksversion hat keine Bestrahlungsstärke "
                "(`analysis.irradiance_map`, ab 0.10).")
        return
    if not ctx.can_aim:
        st.info("Ohne Blende kann die Pupille nicht gezielt werden; die Bestrahlungsstärke braucht eine Blende.")
        return
    comp = ctx.comp
    c1, c2, c3, c4 = st.columns(4)
    field = c1.selectbox("Feld", ctx.field_ids, format_func=ctx.field_label, key="irr_field")
    wavelength = c2.selectbox("Wellenlänge", ctx.wl_ids, index=ctx.wl_ids.index(ctx.ref_wl),
                              format_func=ctx.wl_label, key="irr_wl")
    aim_name = c4.radio("Aiming", list(ctx.aim_map), horizontal=True, key="irr_aim")
    try:
        events = path_events(comp, ctx.path_choice, field, wavelength, ctx.aim_map[aim_name])
    except (rt.RaytatouilleError, ValueError) as error:
        st.error(f"Pfad: {error}")
        return
    by_surface = visits(events)
    surfaces = list(by_surface)
    surface = c3.selectbox("Fläche", surfaces, index=surfaces.index(events[-1]), key="irr_surface",
                           format_func=lambda i: comp.surface_ids[i],
                           help="Jede Fläche des gewählten Pfads. Die Bestrahlungsstärke zählt die einfallende "
                                "Leistung, nicht die, die nach der Fläche weiterläuft.")
    visit_events = by_surface[surface]
    is_last = events[-1] == surface

    d1, d2, d3, d4 = st.columns(4)
    event = None
    if len(visit_events) > 1:
        labels = {e: event_label(e, k, len(visit_events)) for k, e in enumerate(visit_events)}
        event = d1.selectbox("Besuch", [None] + visit_events, key="irr_event",
                             format_func=lambda e: "alle Besuche (Summe)" if e is None else labels[e],
                             help="Eine Fläche, die der Pfad mehrfach trifft (Doppelpass, Spiegel), zählt "
                                  "standardmäßig alle Besuche zusammen.")
    steps = [n for n in RAY_STEPS if n <= max_rays(is_last)]
    n_rays = d2.select_slider("Strahlen", steps, value=min(100_000, steps[-1]), key="irr_rays",
                              format_func=lambda n: f"{n:,}".replace(",", " "),
                              help="Pupillenpunkte gleichmäßig in der Fläche. Bis 100 000 Strahlen gilt für jede "
                                   "Fläche; mehr gibt es nur für die letzte Fläche des Pfads (ohne Aufzeichnung). "
                                   "1 Mio. Strahlen brauchen etwa 0,6 GB und 2 s, 4 Mio. etwa 2 GB und 7 s.")
    nx = int(d3.number_input("Zellen x", 4, 2048, 128, 4, key="irr_nx"))
    ny = int(d4.number_input("Zellen y", 4, 2048, 128, 4, key="irr_ny"))
    e1, e2, e3 = st.columns(3)
    mode = EXTENT_MODES[e1.radio("Bereich", list(EXTENT_MODES), horizontal=True, key="irr_extent")]
    scale = {"linear": "linear", "logarithmisch": "log"}[
        e2.radio("Skala", ["linear", "logarithmisch"], horizontal=True, key="irr_scale",
                 help=f"Logarithmisch: von {LOG_FLOOR:g} bis 1 des Maximums.")]
    cmap = e3.selectbox("Farbtabelle", COLOUR_MAPS, key="irr_cmap")

    try:
        traced = _traced(ctx.system_key, ctx.configuration, ctx.path_choice, field, wavelength, n_rays, aim_name,
                         surface, comp, ctx.aim_map[aim_name])
        auto = auto_extent(comp, traced, surface, event) if mode != "aperture" else None
        manual = _manual_extent(auto or auto_extent(comp, traced, surface, event)) if mode == "manual" else None
        if mode == "manual" and manual is None:
            return
        extent = irradiance_extent(comp, surface, mode, manual, auto)
        result = irradiance(comp, traced, surface, event, nx, ny, extent)
    except (rt.RaytatouilleError, ValueError, RuntimeError) as error:
        st.error(str(error))
        return

    x_edges, y_edges = np.asarray(result.x_edges), np.asarray(result.y_edges)
    values = np.asarray(result.values)
    dx, dy = cell_size_um(x_edges, y_edges)
    m = st.columns(4)
    m[0].metric("Strahlen gezählt", f"{result.rays_counted}/{traced.launched}",
                help="Strahlen, die in dieser Karte ankommen; die übrigen stehen unten mit ihrem Grund.")
    m[1].metric("Leistung gezählt", f"{result.weight_counted:.1f}",
                help="Summe der einfallenden Gewichte. Mit gleichem Gewicht je Pupillenpunkt ist das die Zahl der "
                     "Strahlen mal der Transmission bis zur Fläche.")
    m[2].metric("Spitzenwert", f"{values.max():.3g} /mm²" if values.size else "–",
                help="Größte Bestrahlungsstärke: einfallendes Gewicht je projizierter Zellfläche.")
    m[3].metric("Zellgröße", f"{dx:.2f} × {dy:.2f} µm")
    if not result.rays_counted:
        st.warning("Kein Strahl liegt im gewählten Bereich der Karte.")
        return

    fig, ax = plt.subplots(figsize=(7, 6))
    extent_plot = (x_edges[0], x_edges[-1], y_edges[0], y_edges[-1])
    pic = ax.imshow(scaled(values, scale, LOG_FLOOR), extent=extent_plot, origin="lower", cmap=cmap, vmin=0.0,
                    vmax=1.0, interpolation="nearest", aspect="equal")
    bar = fig.colorbar(pic, ax=ax)
    bar.set_label("relative Bestrahlungsstärke" + (f" (logarithmisch, {LOG_FLOOR:g} bis 1)" if scale == "log" else ""))
    ax.set_xlabel(f"x / mm ({comp.surface_ids[surface]}, lokal)")
    ax.set_ylabel(f"y / mm ({comp.surface_ids[surface]}, lokal)")
    show(fig)
    with st.expander("Strahlen, die nicht in der Karte zählen"):
        st.dataframe(pd.DataFrame(loss_rows(result.outside_grid, result.vignetted, result.not_reached)),
                     hide_index=True, **STRETCH)
    csv = pd.DataFrame(values, index=pd.Index(0.5 * (y_edges[:-1] + y_edges[1:]), name="y_mm"),
                       columns=[f"{x:.6g}" for x in 0.5 * (x_edges[:-1] + x_edges[1:])]).to_csv()
    st.download_button("Karte als CSV (Zeilen y, Spalten x in mm)", csv.encode(), file_name="bestrahlungsstaerke.csv",
                       mime="text/csv", key="irr_csv")
    if hasattr(result, "to_json"):
        st.download_button("Ergebnis als JSON", result.to_json(indent=1).encode(),
                           file_name="bestrahlungsstaerke.result.json", mime="application/json", key="irr_json")
    st.caption("Einfallendes Gewicht je projizierter Zellfläche in der lokalen Ebene der Fläche, in Gewicht je mm². "
               "Die Leistung der Karte ist die Summe der Werte mal der Zellfläche.")
