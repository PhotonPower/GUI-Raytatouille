"""Header: first-order data, focus helper (builder mode) and wavelength/field overview."""

from __future__ import annotations

import pandas as pd
import raytatouille as rt
import streamlit as st

from ..builder import num
from ..context import AppContext
from .common import fmt


def first_order(comp, path: str):
    """Paraxial first-order data of the path, or ``None`` with a hint if not available."""
    try:
        return rt.paraxial.first_order(comp, path=path)
    except rt.RaytatouilleError as error:
        if anamorphic_sections(comp, path) is not None:
            return None  # render_header shows the data per section instead
        st.info(f"Paraxiale Kenndaten nicht verfügbar: {error}. Layout, Strahlen und Polarisation "
                "funktionieren trotzdem.")
        return None


def anamorphic_sections(comp, path: str):
    """``(first order in x, first order in y)`` of an anamorphic path (library 0.10), else ``None``.

    ``paraxial.first_order`` has no answer there (ADR 0042); ``first_order_section`` gives the two
    principal sections. ``None`` also when the sections themselves are not defined (decentred surfaces)."""
    paraxial = rt.paraxial
    if not (hasattr(paraxial, "is_anamorphic") and hasattr(paraxial, "first_order_section")):
        return None
    try:
        if not paraxial.is_anamorphic(comp, path):
            return None
        return tuple(paraxial.first_order_section(comp, path=path, section=section)
                     for section in (paraxial.Section.X, paraxial.Section.Y))
    except (rt.RaytatouilleError, ValueError):
        return None


def render_header(ctx: AppContext) -> None:
    """Metrics row, the "move image plane to paraxial focus" button and the overview expander."""
    ss = st.session_state
    comp, fo = ctx.comp, ctx.first_order
    builder_context = ctx.builder_context

    if fo is not None:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Brennweite EFL", f"{fmt(fo.efl)} mm")
        c2.metric("Schnittweite BFL", f"{fmt(fo.bfl)} mm")
        c3.metric("Blendenzahl f/#", fmt(ctx.fnum, 2))
        c4.metric("Eintrittspupille Ø", f"{fmt(ctx.epd_value)} mm")
        c5.metric("Paraxiale Bildebene z", f"{fmt(fo.rear_focal_z)} mm")
        ss.focus_shift = None
        if builder_context is not None:
            ss.focus_shift = fo.rear_focal_z - builder_context["rows"][-1]["z"]

    elif (sections := anamorphic_sections(comp, ctx.path_choice)) is not None:
        fx, fy = sections

        def both(getter) -> str:
            return f"{fmt(getter(fx))} | {fmt(getter(fy))}"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Brennweite EFL (x | y)", f"{both(lambda f: f.efl)} mm")
        c2.metric("Schnittweite BFL (x | y)", f"{both(lambda f: f.bfl)} mm")
        c3.metric("Eintrittspupille Ø", f"{fmt(ctx.epd_value)} mm")
        c4.metric("Paraxiale Bildebene z (x | y)", f"{both(lambda f: f.rear_focal_z)} mm")
        st.caption("Anamorphes System: Die Kenndaten gelten je Hauptschnitt (x und y), "
                   "`–` heißt afokal im Schnitt.")
        ss.focus_shift = None

    if builder_context is not None and ss.get("focus_shift") is not None:
        st.write(f"Die Bildebene liegt {ss.focus_shift:+.4f} mm neben dem paraxialen Fokus.")

        def move_focus():
            df = ss.bedited.reset_index(drop=True).copy()
            if len(df) >= 2 and df.iloc[-1]["Typ"] == "Bild":
                df.loc[len(df) - 2, "Dicke_mm"] = num(df.loc[len(df) - 2, "Dicke_mm"]) + ss.focus_shift
                ss.bdf = df
                ss.bver += 1

        st.button("Bildebene auf paraxialen Fokus setzen", on_click=move_focus)

    with st.expander("Wellenlängen, Felder, Pfade"):
        st.write(pd.DataFrame({"Wellenlänge µm": ctx.wl_um, "Gewicht": list(comp.wavelength_weights),
                               "Referenz": [i == ctx.ref_wl for i in range(len(ctx.wl_um))]}))
        st.write(pd.DataFrame({"Feld": [ctx.field_label(i) for i in range(comp.field_count)]}))
        st.write("Pfade:", ", ".join(comp.path_names), "| Flächen:", ", ".join(comp.surface_ids))
