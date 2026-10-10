"""View "Optimierung": merit function, variables and a Levenberg-Marquardt run of the library (M5)."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import raytatouille as rt
import streamlit as st

from ..builder import table_updates
from ..context import AppContext
from ..optim_table import generator_row, operand_row, status_text, variable_label
from ..ui.common import STRETCH, diagnostic_line, fmt, show

TITLE = "Optimierung"


def render(ctx: AppContext) -> None:
    """Render the view "Optimierung"."""
    if not ctx.features.optim:
        st.info("Die installierte Bibliotheksversion hat keine Optimierung (`raytatouille.optim`, ab 0.7).")
        return
    ss = st.session_state
    system = ctx.system
    config_names = [c.name for c in getattr(system, "configurations", [])]
    optimization = system.optimization
    operands, generators = list(optimization.operands), list(optimization.generators)
    try:
        variables = rt.optim.variables(system)
    except (rt.RaytatouilleError, ValueError) as error:
        st.error(f"Variablen: {error}")
        return
    if not variables or not (operands or generators):
        missing = [text for text, empty in (("Variablen", not variables),
                                            ("Operanden oder Generatoren", not (operands or generators)))
                   if empty]
        where = ("Im Baukasten: Häkchen „R var“, „k var“ oder „d var“ in der Flächentabelle setzen und rechts die "
                 "Merit-Funktion füllen." if ctx.builder_context is not None else
                 "Variablen markiert man in der Datei mit `\"variable\": true` an einem Wert oder einer Zeile der "
                 "Parametertabelle, die Merit-Funktion steht im Abschnitt `optimization` (Beispiele: "
                 "`m5/singlet_solve`, `m5/two_lens_gap`); oder das System im Baukasten aufbauen.")
        st.info(f"Dieses System hat keine {' und keine '.join(missing)}. {where}")
        return

    start_values = _start_evaluation(ctx, operands, generators)

    st.markdown("**Merit-Funktion**")
    if operands:
        table = pd.DataFrame([operand_row(op) for op in operands])
        if start_values is not None:
            table.insert(2, "Startwert", start_values[0])
        st.dataframe(table, hide_index=True, **STRETCH)
    if generators:
        table = pd.DataFrame([generator_row(g) for g in generators])
        if start_values is not None:
            table.insert(1, "Start-RMS", start_values[1])
        st.dataframe(table, hide_index=True, **STRETCH)
    st.markdown("**Variablen**")
    st.dataframe(pd.DataFrame([{
        "Variable": variable_label(v.pointer, v.row, v.configuration, config_names, *_surfaces(ctx)), "Start": v.start,
        "Min": v.min, "Max": v.max} for v in variables]), hide_index=True, **STRETCH)

    with st.expander("Optionen des Optimierers (Levenberg-Marquardt)"):
        a, b, c = st.columns(3)
        max_iterations = int(a.number_input("Max. Iterationen", 1, 10000, 100, key="optim_iter"))
        ftol = b.number_input("ftol (rel. Änderung der Merit-Funktion)", 0.0, 1.0, 1.4901161193847656e-8,
                              format="%.2e", key="optim_ftol")
        xtol = c.number_input("xtol (rel. Schrittweite)", 0.0, 1.0, 1.4901161193847656e-8, format="%.2e",
                              key="optim_xtol")
    key = (ctx.system_key, max_iterations, ftol, xtol)
    if st.button("Optimieren", type="primary", key="optim_run"):
        options = rt.optim.OptimizeOptions(max_iterations=max_iterations, ftol=ftol, xtol=xtol)
        with st.spinner("Optimiere …"):
            try:
                result = rt.optim.optimize(system, materials=ctx.lib, coatings=ctx.coatings, options=options)
            except rt.OptimError as error:
                st.error(f"Optimierung nicht möglich: {error} (Codes: {', '.join(error.codes)})")
                return
            except (rt.RaytatouilleError, ValueError) as error:
                st.error(f"Optimierung nicht möglich: {error}")
                return
        ss.optim_result = (key, result)
    stored = ss.get("optim_result")
    if stored is None or stored[0] != key:
        st.caption("Die Optimierung rechnet auf einer Kopie; das geladene System ändert sich erst mit "
                   "„Ergebnis übernehmen“.")
        return
    _show_result(ctx, stored[1], config_names)


def _surfaces(ctx: AppContext) -> tuple[list[str], list[str]]:
    """JSON pointers and ids of the surfaces, to name variables inside a surface."""
    return list(getattr(ctx.comp, "surface_locations", [])), list(ctx.comp.surface_ids)


def _start_evaluation(ctx: AppContext, operands, generators):
    """(operand values, generator RMS) at the start values, or None if the merit function fails."""
    try:
        merit = rt.optim.MeritFunction(ctx.system, ctx.lib, ctx.coatings)
        ev = merit.evaluate(merit.start())
    except (rt.RaytatouilleError, ValueError) as error:
        st.warning(f"Merit-Funktion am Startpunkt nicht auswertbar: {error}")
        return None
    values = [float(v) for v in np.asarray(ev.values)][:len(operands)]
    # mean_square is mm² (spot) or waves² (wavefront); its square root is the RMS of the generator
    rms = [_rms_text(type(g).__name__, math.sqrt(s.mean_square)) if math.isfinite(s.mean_square) else "–"
           for g, s in zip(generators, ev.generators)]
    for text in ev.undefined:
        st.warning(f"Am Startpunkt undefiniert: {text}")
    return values, rms


def _rms_text(kind: str, rms: float) -> str:
    return f"{rms:.4f} Wellen" if kind == "WavefrontGenerator" else f"{1000 * rms:.3f} µm"


def _show_result(ctx: AppContext, result, config_names: list[str]) -> None:
    ss = st.session_state
    m = st.columns(4)
    m[0].metric("Status", status_text(result.status.name))
    m[1].metric("Iterationen", result.iterations)
    m[2].metric("Auswertungen", result.evaluations)
    h = result.history
    m[3].metric("φ am Ende", fmt(float(h.phi[-1]), 6) if len(h) else "–",
                help="Normierte Merit-Funktion 2F/Σw der Bibliothek.")
    for d in result.diagnostics:
        st.warning(diagnostic_line(ctx.comp, d))

    left, right = st.columns([3, 2])
    with left:
        st.markdown("**Variablen**")
        st.dataframe(pd.DataFrame([{
            "Variable": variable_label(v.pointer, v.row, v.configuration, config_names, *_surfaces(ctx)),
            "Start": v.start, "Ende": v.end, "geändert": v.changed, "an der Grenze": v.at_bound}
            for v in result.variables]),
            hide_index=True, **STRETCH)
        if result.operands:
            st.markdown("**Operanden**")
            st.dataframe(pd.DataFrame([{
                "Operand": operand_row(op)["Operand"], "Wert": r.value, "Ziel": r.target, "Gewicht": r.weight,
                "Anteil (%)": r.contribution} for op, r in zip(ctx.system.optimization.operands, result.operands)]),
                hide_index=True, **STRETCH)
        if result.generators:
            st.markdown("**Generatoren**")
            st.dataframe(pd.DataFrame([{
                "Generator": generator_row(g)["Generator"], "RMS": _rms_text(type(g).__name__, r.rms),
                "Gewicht": r.weight, "Anteil (%)": r.contribution, "verlorene Strahlen": f"{r.rays_lost}/"
                f"{r.rays_launched}"} for g, r in zip(ctx.system.optimization.generators, result.generators)]),
                hide_index=True, **STRETCH)
    with right:
        if len(h):
            fig, ax = plt.subplots(figsize=(5, 3.6))
            k, phi, accepted = np.asarray(h.k), np.asarray(h.phi), np.asarray(h.accepted, dtype=bool)
            ax.semilogy(k, phi, "-", color="tab:blue")
            ax.semilogy(k[accepted], phi[accepted], "o", color="tab:blue", label="angenommen")
            if (~accepted).any():
                ax.semilogy(k[~accepted], phi[~accepted], "x", color="tab:red", label="verworfen")
            ax.set_xlabel("Schritt")
            ax.set_ylabel("φ")
            ax.set_title("Verlauf der Merit-Funktion")
            ax.grid(alpha=0.3, which="both")
            ax.legend()
            show(fig)

    a, b, c = st.columns(3)
    a.download_button("Optimiertes System (.rtt.json)", result.system.to_json().encode(),
                      file_name="optimiert.rtt.json", mime="application/json")
    b.download_button("Änderungen als JSON Patch", result.patch.encode(), file_name="optimierung.patch.json",
                      mime="application/json", help="RFC 6902; anwenden mit rt.apply_patch(system, patch).")
    if hasattr(result, "to_json"):
        c.download_button("Ergebnis als JSON", result.to_json(indent=1).encode(), file_name="optimierung.result.json",
                          mime="application/json")

    if ctx.builder_context is not None:
        # The builder names its variables R<n>, K<n>, D<n>: write the end values back into the table.
        updates = table_updates([(v.row, v.end) for v in result.variables])

        def adopt_into_table():
            df = ss.bedited.reset_index(drop=True).copy()
            for row, column, value in updates:
                if 0 <= row < len(df):
                    df.loc[row, column] = value
            ss.bdf = df
            ss.bver += 1
            ss.pop("optim_result", None)

        st.button("Ergebnis in die Flächentabelle übernehmen", on_click=adopt_into_table,
                  disabled=not updates or result.patch == "[]",
                  help="Schreibt die optimierten Radien, Koniken und Dicken in die Tabelle des Baukastens.")
    else:
        def adopt():
            ss.optim_override = {"source": ss.get("optim_source"), "base": ss.get("optim_base"),
                                 "json": result.system.to_json()}
            ss.pop("optim_result", None)

        st.button("Ergebnis übernehmen", on_click=adopt, disabled=result.patch == "[]",
                  help="Alle Ansichten zeigen danach das optimierte System, bis du es verwirfst oder die Quelle "
                       "wechselst.")
    if result.status.name == "CONVERGED_STEP" and any(op.weight >= 1e3 for op in ctx.system.optimization.operands):
        st.caption("Hinweis der Bibliothek (ADR 0030): Große Strafgewichte auf Gleichheitsbedingungen machen ein "
                   "enges, gekrümmtes Tal, in dem der Optimierer früh stehen bleibt. Besser die Bedingung über die "
                   "Parametertabelle exakt halten (siehe m5/singlet_solve).")
