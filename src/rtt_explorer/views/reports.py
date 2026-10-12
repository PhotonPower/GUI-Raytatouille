"""View "Reports": dimensions, system data and ray trace tables of the library (#177) with CSV export."""

from __future__ import annotations

import io

import pandas as pd
import raytatouille as rt
import streamlit as st

from ..context import AppContext
from ..ui.common import STRETCH, diagnostic_line, run

TITLE = "Reports"


def _frame(report) -> pd.DataFrame:
    """The report as the library writes it to CSV (column names, status and aperture names included)."""
    return pd.read_csv(io.StringIO(report.to_csv()), keep_default_na=True)


def _downloads(report, stem: str, key: str) -> None:
    a, b = st.columns(2)
    a.download_button("Als CSV", report.to_csv().encode(), file_name=f"{stem}.csv", mime="text/csv",
                      key=f"csv_{key}")
    b.download_button("Als JSON", report.to_json(indent=1).encode(), file_name=f"{stem}.result.json",
                      mime="application/json", key=f"json_{key}")


def render(ctx: AppContext) -> None:
    """Render the view "Reports"."""
    if not ctx.features.reports:
        st.info("Die installierte Bibliotheksversion hat keine Reports (`analysis.dimension_report`, ab 0.7).")
        return
    dims, system, trace = st.tabs(["Abmessungen", "Systemdaten", "Raytrace"])
    with dims:
        _dimensions(ctx)
    with system:
        _system(ctx)
    with trace:
        _raytrace(ctx)


def _dimensions(ctx: AppContext) -> None:
    comp = ctx.comp
    report = run("Abmessungen", rt.analysis.dimension_report, comp)
    if report is None:
        return
    table = _frame(report)
    if table.empty:
        st.info("Das System hat keine Linsen oder Platten.")
        return
    elements = rt.layout.elements(comp) if ctx.features.layout else []
    if "element" in table and elements:
        table["element"] = [elements[int(i)].name for i in table["element"]]
    if "first_surface" in table:
        table["first_surface"] = [comp.surface_ids[int(i)] for i in table["first_surface"]]
    st.dataframe(table, hide_index=True, **STRETCH)
    st.caption("Je Glassegment einer Linse oder Platte: Mittendicke, Halbdurchmesser und Apertur beider Flächen, "
               "Randdicke und Durchmesser in mm; leer, wo eine Größe nicht definiert ist (z. B. ohne Apertur).")
    _downloads(report, "abmessungen", "dims")


def _system(ctx: AppContext) -> None:
    w = st.selectbox("Wellenlänge", [None] + ctx.wl_ids, key="report_wl",
                     format_func=lambda i: "Referenz" if i is None else ctx.wl_label(i))
    report = run("Systemdaten", rt.analysis.system_report, ctx.comp, ctx.path_choice, w)
    if report is None:
        return
    for d in report.warnings:
        st.info(diagnostic_line(ctx.comp, d))
    table = _frame(report)
    st.dataframe(table, hide_index=True, **STRETCH)
    _downloads(report, "systemdaten", "system")


def _raytrace(ctx: AppContext) -> None:
    comp = ctx.comp
    c1, c2, c3 = st.columns(3)
    f = c1.selectbox("Feld", ctx.field_ids, format_func=ctx.field_label, key="report_field")
    w = c2.selectbox("Wellenlänge", ctx.wl_ids, index=ctx.ref_wl, format_func=ctx.wl_label, key="report_trace_wl")
    n = c3.slider("Strahlen im Fächer (y)", 1, 11, 3, step=2, key="report_rays")
    src = ctx.source_ui("reports")
    try:
        batch, _, _ = ctx.make_batch(src, "Fächer", n, "yz", f, w, rt.trace.Aiming.REAL)
    except (rt.RaytatouilleError, ValueError) as error:
        st.error(f"Startstrahlen: {error}")
        return
    report = run("Raytrace", rt.analysis.raytrace_report, comp, ctx.path_choice, start=batch)
    if report is None:
        return
    table = _frame(report)
    if "surface" in table:
        ids = list(comp.surface_ids)
        table["surface"] = [ids[int(s)] if pd.notna(s) and 0 <= int(s) < len(ids) else "Start"
                            for s in table["surface"]]
    st.dataframe(table, hide_index=True, **STRETCH)
    st.caption("Eine Zeile je Strahl und Ereignis: globale Koordinaten (x, y, z, dx, dy, dz), lokale im "
               "Flächensystem (local_*), optischer Weg in mm, Gewicht und Status. Zeile 0 ist der Start.")
    _downloads(report, "raytrace", "trace")
