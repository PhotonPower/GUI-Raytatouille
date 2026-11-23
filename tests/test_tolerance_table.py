"""Tolerance items, sensitivity and Monte Carlo as table rows (pure logic; fakes stand in for rt objects)."""

from __future__ import annotations

from types import SimpleNamespace as NS

import pytest

from rtt_explorer.tolerance_table import (
    contribution_shares,
    criterion_limit_text,
    item_rows,
    item_target,
    kind_unit,
    monte_carlo_rows,
    percentile_columns,
    sensitivity_rows,
    yield_text,
)


def enum(name):
    return NS(name=name)


def item(id_, kind="THICKNESS", limit=0.1, distribution="NORMAL", **target):
    base = {"surface": None, "node": None, "parameter": None, "param": None, "segment": None, "term": None}
    return NS(id=id_, kind=enum(kind), limit=limit, distribution=enum(distribution), **{**base, **target})


def test_kind_unit_follows_the_library_docstring():
    assert kind_unit("THICKNESS") == "mm"
    assert kind_unit("TILT_X_DEG") == "°"
    assert kind_unit("CONIC") == "–"
    assert kind_unit("ABBE") == "–"
    assert kind_unit("PARAM") == "Einheit des Parameters"
    assert kind_unit("UNKNOWN") == ""


def test_item_target_names_what_the_item_hits():
    assert item_target(item("a", surface="L1.S1")) == "Fläche L1.S1"
    assert item_target(item("b", node="stop")) == "Knoten stop"
    assert item_target(item("c", parameter="D", param="/value")) == "Parameter D"
    assert item_target(item("d", node="L1", segment=1)) == "Knoten L1, Segment 1"
    assert item_target(item("e", surface="M", term=4)) == "Fläche M, Term 4"
    assert item_target(item("f")) == ""


def test_item_rows_show_kind_limit_distribution_and_origin():
    items = [item("class:node:stop:thickness", node="stop"),
             item("explicit:1", "TILT_Y_DEG", 0.02, "UNIFORM", node="L1")]
    origins = [NS(source=enum("CLASS")), NS(source=enum("EXPLICIT"))]
    rows = item_rows(items, origins)
    assert [r["Nr"] for r in rows] == [1, 2]
    assert rows[0]["Art"] == "Dicke" and rows[0]["Einheit"] == "mm" and rows[0]["Grenze T"] == 0.1
    assert rows[0]["Herkunft"] == "Klasse"
    assert rows[1]["Art"] == "Kippung y" and rows[1]["Verteilung"] == "gleichverteilt"
    assert rows[1]["Herkunft"] == "explizit"


def test_item_rows_without_origins_leave_the_column_empty():
    assert item_rows([item("x", node="n")], None)[0]["Herkunft"] == ""


def test_shares_for_a_linear_criterion_use_the_squared_effect():
    # delta 3 and 4: squares 9 and 16 of 25
    assert contribution_shares("LINEAR", [3.0, -4.0], [None, None]) == pytest.approx([0.36, 0.64])


def test_shares_for_a_quadratic_criterion_use_q_and_ignore_negative_terms():
    assert contribution_shares("QUADRATIC", [None, None, None], [2.0, -1.0, 6.0]) == pytest.approx([0.25, 0.0, 0.75])


def test_shares_are_none_for_missing_values_and_zero_when_nothing_contributes():
    assert contribution_shares("LINEAR", [None, 2.0], [None, None]) == [None, 1.0]
    assert contribution_shares("QUADRATIC", [None], [0.0]) == [0.0]


def criterion(kind="LINEAR", items=(), inverse_limits=None):
    return NS(id="efl", kind=enum(kind), nominal=100.0, rss=0.3, predicted_sigma=0.1, predicted_mean_square=None,
              items=list(items), inverse=NS(limits=inverse_limits, allowance=0.5, share=0.0, unlimited=[], note=""))


def crit_item(plus, minus, worst, delta=None, q=None, excluded=""):
    return NS(plus=plus, minus=minus, worst=worst, delta=delta, shift=None, q=q, excluded=excluded)


def test_sensitivity_rows_combine_item_effect_share_and_inverse_limit():
    items = [item("a", node="stop", limit=0.1), item("b", node="L1", limit=0.2)]
    crit = criterion(items=[crit_item(101.0, 99.0, 1.0, delta=1.0), crit_item(103.0, 97.0, 3.0, delta=3.0)],
                     inverse_limits=[0.5, None])
    rows = sensitivity_rows(crit, items)
    assert [r["Id"] for r in rows] == ["a", "b"]
    assert [r["Φ(+T)"] for r in rows] == [101.0, 103.0]
    assert [r["Φ(−T)"] for r in rows] == [99.0, 97.0]
    assert [r["größte Änderung"] for r in rows] == [1.0, 3.0]
    assert [r["Anteil (%)"] for r in rows] == pytest.approx([10.0, 90.0])
    assert [r["T′ (inverse Sensitivität)"] for r in rows] == [0.5, None]


def test_sensitivity_rows_mark_excluded_items_without_a_share():
    items = [item("a", node="stop"), item("b", node="L1")]
    crit = criterion(items=[crit_item(None, None, None, excluded="ungültig bei +T"),
                            crit_item(2.0, 1.0, 1.0, delta=1.0)])
    rows = sensitivity_rows(crit, items)
    assert rows[0]["Anteil (%)"] is None
    assert rows[0]["Hinweis"] == "ungültig bei +T"
    assert rows[1]["Anteil (%)"] == pytest.approx(100.0)
    assert rows[1]["Hinweis"] == ""


def test_criterion_limit_text():
    assert criterion_limit_text(NS(min=None, max=0.02, max_change=None)) == "≤ 0.02"
    assert criterion_limit_text(NS(min=90.0, max=110.0, max_change=None)) == "90 … 110"
    assert criterion_limit_text(NS(min=1.5, max=None, max_change=None)) == "≥ 1.5"
    assert criterion_limit_text(NS(min=None, max=None, max_change=0.5)) == "Änderung ≤ 0.5"
    assert criterion_limit_text(NS(min=None, max=0.03, max_change=0.5)) == "≤ 0.03; Änderung ≤ 0.5"
    assert criterion_limit_text(NS(min=None, max=None, max_change=None)) == "–"


def test_yield_text_gives_count_percentage_and_interval():
    y = NS(good=63, total=200, fraction=0.315, lower=0.2516, upper=0.3854)
    assert yield_text(y) == "63 von 200 (31.5 %), Intervall 25.2 bis 38.5 %"
    assert yield_text(NS(good=0, total=0, fraction=float("nan"), lower=0.0, upper=1.0)) == "–"


def test_percentile_columns_are_labelled_with_the_percent():
    ps = [NS(p=0.5, value=1.0, rank=10), NS(p=0.95, value=2.0, rank=19), NS(p=0.99, value=3.0, rank=20)]
    assert percentile_columns(ps) == {"50 %": 1.0, "95 %": 2.0, "99 %": 3.0}


def test_monte_carlo_rows_list_statistics_limit_and_yield_per_criterion():
    stats = [NS(id="spot", count=198, with_value=198, without_value=0, mean=0.011, standard_deviation=0.001,
                min=0.009, max=0.015, percentiles=[NS(p=0.5, value=0.0108, rank=99)],
                yield_=NS(good=190, total=198, fraction=0.9596, lower=0.92, upper=0.98), note="")]
    defs = [NS(id="spot", min=None, max=0.02, max_change=None)]
    rows = monte_carlo_rows(stats, defs)
    assert rows[0]["Kriterium"] == "spot"
    assert rows[0]["Grenze"] == "≤ 0.02"
    assert rows[0]["Mittel"] == 0.011 and rows[0]["σ"] == 0.001
    assert rows[0]["50 %"] == 0.0108
    assert rows[0]["Ausbeute"] == "190 von 198 (96.0 %), Intervall 92.0 bis 98.0 %"


def test_monte_carlo_rows_without_a_matching_definition_leave_the_limit_empty():
    stats = [NS(id="zz", count=1, with_value=1, without_value=0, mean=1.0, standard_deviation=0.0, min=1.0, max=1.0,
                percentiles=[], yield_=NS(good=1, total=1, fraction=1.0, lower=0.2, upper=1.0), note="")]
    assert monte_carlo_rows(stats, [])[0]["Grenze"] == ""
