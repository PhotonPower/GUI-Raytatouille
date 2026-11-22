"""View "Toleranzen": the tolerance set of the system, sensitivity and Monte Carlo of the library (0.9)."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import raytatouille as rt
import streamlit as st

from ..context import AppContext
from ..optim_table import operand_row
from ..progress_run import Progress, run_with_progress
from ..tolerance_table import (
    MAX_TRIALS,
    criterion_limit_text,
    item_rows,
    monte_carlo_rows,
    sensitivity_rows,
    yield_text,
)
from ..ui.common import STRETCH, diagnostic_line, fmt, show

TITLE = "Toleranzen"


def render(ctx: AppContext) -> None:
    """Render the view "Toleranzen"."""
    if not ctx.features.tolerance:
        st.info("Die installierte Bibliotheksversion hat keine Toleranzierung (`raytatouille.tolerance`, ab 0.9).")
        return
    try:
        expansion = rt.tolerance.expand(ctx.system, materials=ctx.lib)
    except (rt.RaytatouilleError, ValueError) as error:
        st.error(f"Toleranzsatz: {error}")
        return
    if not expansion.items:
        st.info("Dieses System hat keinen Toleranzsatz. Er steht im Abschnitt `tolerances` der Datei: eine Klasse "
                "(`coarse`, `normal`, `precise`), Überschreibungen, explizite Items, Kompensatoren und Kriterien "
                "(Beispiel: `m7/achromat_tolerances`).")
        return
    tolerances = ctx.system.tolerances
    st.caption(f"Klasse **{tolerances.tolerance_class.name.lower()}**, {len(expansion.items)} Items, "
               f"{len(tolerances.criteria)} Kriterien, {len(tolerances.compensators)} Kompensatoren. "
               "Klasse, Kriterien und Kompensatoren stehen in der Datei; der Explorer ändert sie nicht.")
    items_tab, sens_tab, mc_tab = st.tabs(["Items", "Sensitivität", "Monte Carlo"])
    with items_tab:
        _items(expansion)
    with sens_tab:
        _sensitivity(ctx, expansion)
    with mc_tab:
        _monte_carlo(ctx, expansion)


def _items(expansion) -> None:
    st.dataframe(pd.DataFrame(item_rows(expansion.items, expansion.origins)), hide_index=True, **STRETCH)
    st.caption("Grenze T in der Einheit der Art. Bei „normal“ ist T die doppelte Standardabweichung (abgeschnitten "
               "bei ±T), bei „gleichverteilt“ σ = T/√3, bei „Endpunkte“ σ = T. Die Klassenwerte kommen aus der "
               "Tabelle der Bibliothek, die Abbezahl relativ zu ν_d des Glases.")
    for d in expansion.warnings:
        st.warning(str(d.message))


def _criteria_table(ctx: AppContext, nominal, definitions) -> None:
    rows = []
    for definition, value in zip(definitions, nominal.criteria):
        rows.append({"Kriterium": definition.id, "Operand": operand_row(definition.operand)["Operand"],
                     "Grenze": criterion_limit_text(definition), "Nominal": value.value,
                     "erfüllt": "ja" if value.satisfied else "nein"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, **STRETCH)
    for c in nominal.compensators:
        st.caption(f"Kompensator nominal: {fmt(c.start, 5)} → {fmt(c.end, 5)}"
                   + (" (an der Grenze)" if c.at_bound else "") + (" (nicht erreichbar)" if c.infeasible else ""))


def _call(label: str, call):
    """Run ``call(progress)`` in a worker thread with a progress bar; None (and a message) on a library error."""
    bar = st.progress(0.0, text=f"{label} …")

    def tick(progress: Progress) -> None:
        done, total, _ = progress.snapshot()
        bar.progress(progress.fraction, text=f"{label}: {done} von {total}" if total else f"{label} …")

    try:
        return run_with_progress(call, tick)
    except rt.OptimError as error:
        st.error(f"{label} nicht möglich: {error} (Codes: {', '.join(error.codes)})")
    except (rt.RaytatouilleError, ValueError) as error:
        st.error(f"{label} nicht möglich: {error}")
    finally:
        bar.empty()
    return None


def _sensitivity(ctx: AppContext, expansion) -> None:
    ss = st.session_state
    definitions = list(ctx.system.tolerances.criteria)
    if not definitions:
        st.info("Der Toleranzsatz hat keine Kriterien (`tolerances.criteria`); ohne sie gibt es nichts zu bewerten.")
        return
    confirm = st.checkbox("Mit Bestätigung bei ±T′ (rechnet jedes Item ein zweites Mal)", value=True,
                          key="tol_confirm")
    key = (ctx.system_key, confirm)
    if st.button("Sensitivität rechnen", type="primary", key="tol_run_sens"):
        result = _call("Sensitivität", lambda progress: rt.tolerance.sensitivity(
            ctx.system, materials=ctx.lib, coatings=ctx.coatings, confirm=confirm, progress=progress))
        if result is not None:
            ss.tol_sens = (key, result)
    stored = ss.get("tol_sens")
    if stored is None or stored[0] != key:
        st.caption("Jedes Item wird bei +T und −T gerechnet, alle anderen bei 0, nach dem Lauf der Kompensatoren. "
                   "Das braucht je Item zwei Prüflinge.")
        return
    result = stored[1]
    if result.status.name != "COMPLETED":
        st.warning(f"Die Rechnung ist nicht vollständig durchgelaufen (Status {result.status.name}).")
    for d in result.warnings:
        st.warning(diagnostic_line(ctx.comp, d))
    st.markdown("**Nominalsystem**")
    _criteria_table(ctx, result.nominal, definitions)
    st.markdown("**Wirkung der Items**")
    ids = [c.id for c in result.criteria]
    if not ids:
        return
    chosen = st.selectbox("Kriterium", ids, key="tol_crit")
    crit = result.criteria[ids.index(chosen)]
    m = st.columns(3)
    m[0].metric("Nominal", fmt(crit.nominal, 5))
    m[1].metric("RSS", fmt(crit.rss, 5) if crit.rss is not None else "–",
                help="Wurzel der Summe der Einzelbeiträge nach Burge (lineare Kriterien: Σδ², quadratische: "
                     "Φ₀² + Σq).")
    if crit.predicted_sigma is not None:
        m[2].metric("vorhergesagte Streuung σ", fmt(crit.predicted_sigma, 5))
    elif crit.predicted_mean_square is not None:
        m[2].metric("vorhergesagter Mittelwert von Φ", fmt(math.sqrt(crit.predicted_mean_square), 5))
    rows = sensitivity_rows(crit, result.expansion.items)
    table = pd.DataFrame(rows)
    st.dataframe(table, hide_index=True, **STRETCH)
    _share_chart(rows)
    st.caption("Φ(±T): Wert des Kriteriums, wenn nur dieses Item auf ±T steht. Anteil: Beitrag zur Streuung "
               "(Quadrat der Änderung bzw. q). T′: Grenze, bei der das Item allein den Spielraum des Kriteriums "
               "gleichmäßig auf alle Items verteilt ausschöpft (inverse Sensitivität); leer heißt unbegrenzt.")
    st.download_button("Ergebnis als JSON", result.to_json(indent=1).encode(), file_name="sensitivitaet.result.json",
                       mime="application/json", key="tol_sens_json")


def _share_chart(rows: list[dict], top: int = 15) -> None:
    shown = sorted((r for r in rows if r["Anteil (%)"] is not None), key=lambda r: r["Anteil (%)"], reverse=True)[:top]
    if not shown or max(r["Anteil (%)"] for r in shown) <= 0:
        return
    fig, ax = plt.subplots(figsize=(6, 0.3 * len(shown) + 1.0))
    labels = [r["Id"] for r in shown][::-1]
    ax.barh(labels, [r["Anteil (%)"] for r in shown][::-1], color="tab:blue")
    ax.set_xlabel("Anteil an der Streuung (%)")
    ax.set_title(f"Größte Beiträge (bis zu {top})")
    ax.grid(alpha=0.3, axis="x")
    show(fig)


def _monte_carlo(ctx: AppContext, expansion) -> None:
    ss = st.session_state
    defaults = ctx.system.tolerances.monte_carlo
    definitions = list(ctx.system.tolerances.criteria)
    if not definitions:
        st.info("Der Toleranzsatz hat keine Kriterien (`tolerances.criteria`); ohne sie gibt es nichts zu bewerten.")
        return
    a, b = st.columns(2)
    start = min(int(defaults.trials), MAX_TRIALS) if defaults.trials else 200
    trials = int(a.number_input(f"Prüflinge (höchstens {MAX_TRIALS})", 1, MAX_TRIALS, start, key="tol_trials",
                                help="Die Zeit wächst linear mit der Zahl; ein Prüfling braucht bei kleinen Systemen "
                                     "einige Millisekunden, bei großen mit Kompensatoren Sekunden."))
    max_seed = 2**53 - 1  # the widget works with JavaScript numbers
    seed = int(b.number_input("Seed", 0, max_seed, min(int(defaults.seed or 0), max_seed), key="tol_seed",
                              help="Gleicher Seed, gleiche Ziehung, auf jeder Thread-Zahl."))
    key = (ctx.system_key, trials, seed)
    if st.button("Monte Carlo rechnen", type="primary", key="tol_run_mc"):
        result = _call("Monte Carlo", lambda progress: rt.tolerance.monte_carlo(
            ctx.system, materials=ctx.lib, coatings=ctx.coatings, trials=trials, seed=seed, progress=progress))
        if result is not None:
            ss.tol_mc = (key, result)
    stored = ss.get("tol_mc")
    if stored is None or stored[0] != key:
        st.caption("Jeder Prüfling zieht für alle Items Störwerte aus ihrer Verteilung, lässt die Kompensatoren "
                   "laufen und wertet die Kriterien aus. Die Ausbeute ist der Anteil der Prüflinge, die alle "
                   "Kriterien erfüllen.")
        return
    mc = stored[1]
    if mc.status.name != "COMPLETED":
        st.warning(f"Die Rechnung ist nicht vollständig durchgelaufen (Status {mc.status.name}).")
    for d in mc.warnings:
        st.warning(diagnostic_line(ctx.comp, d))
    valid = int((np.asarray(mc.trials.status) == rt.tolerance.TrialStatus.VALID.value).sum())
    m = st.columns(3)
    m[0].metric("Prüflinge gültig", f"{valid} von {mc.requested}")
    m[1].metric("Seed", mc.seed)
    m[2].metric("Ausbeute (alle Kriterien)", yield_text(mc.yield_).split(", ")[0])
    st.caption(f"Gesamtausbeute: {yield_text(mc.yield_)}")
    st.dataframe(pd.DataFrame(monte_carlo_rows(mc.criteria, definitions)), hide_index=True, **STRETCH)
    _histogram(mc, definitions)
    c1, c2 = st.columns(2)
    c1.download_button("Prüflinge als CSV", _trials_frame(mc, definitions).to_csv(index=False).encode(),
                       file_name="monte_carlo_prueflinge.csv", mime="text/csv", key="tol_mc_csv")
    c2.download_button("Ergebnis als JSON", mc.to_json(indent=1).encode(), file_name="monte_carlo.result.json",
                       mime="application/json", key="tol_mc_json")


def _histogram(mc, definitions) -> None:
    ids = [d.id for d in definitions]
    chosen = st.selectbox("Kriterium", ids, key="tol_mc_crit")
    k = ids.index(chosen)
    bins = int(st.slider("Klassen", 5, 80, 25, key="tol_mc_bins"))
    ok = np.asarray(mc.trials.status) == rt.tolerance.TrialStatus.VALID.value
    values = np.asarray(mc.trials.criteria)[ok, k]
    values = values[np.isfinite(values)]
    if not values.size:
        st.info("Kein Prüfling hat einen Wert für dieses Kriterium.")
        return
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.hist(values, bins=bins, color="tab:blue", alpha=0.8)
    nominal = mc.nominal.criteria[k].value
    ax.axvline(nominal, color="k", ls="--", lw=1, label="nominal")
    d = definitions[k]
    for bound, name in ((d.min, "min"), (d.max, "max")):
        if bound is not None:
            ax.axvline(bound, color="tab:red", lw=1.5, label=name)
    ax.set_xlabel(chosen)
    ax.set_ylabel("Prüflinge")
    ax.set_title("Verteilung des Kriteriums")
    ax.legend()
    ax.grid(alpha=0.3)
    show(fig)


def _trials_frame(mc, definitions) -> pd.DataFrame:
    """Trial table for the CSV: number, status, all-criteria flag, criteria values and the perturbations per item."""
    t = mc.trials
    frame = pd.DataFrame({"prueflinge": np.asarray(t.trial), "gueltig": np.asarray(t.status) == 0,
                          "alle_erfuellt": np.asarray(t.good)})
    for k, d in enumerate(definitions):
        frame[f"kriterium:{d.id}"] = np.asarray(t.criteria)[:, k]
    for k, it in enumerate(mc.expansion.items):
        frame[f"stoerung:{it.id}"] = np.asarray(t.values)[:, k]
    return frame
