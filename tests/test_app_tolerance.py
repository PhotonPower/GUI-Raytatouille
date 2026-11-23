"""View Toleranzen (needs the library and a checkout, like ``test_app.py``)."""

from __future__ import annotations

import pytest

from test_app import pick_reference, start
from test_app_library_06 import need, ok, ref, table, view

pytestmark = pytest.mark.library

SYSTEM = "m7/achromat_tolerances.rtt.json"


def tolerance_view(rtt_repo, monkeypatch, name=SYSTEM):
    need("tolerance")
    at = pick_reference(start(rtt_repo, monkeypatch), ref(name))
    at = view(at, "Toleranzen")
    ok(at)
    return at


def click(at, key):
    return next(b for b in at.button if b.key == key).click().run()


def test_items_tab_lists_the_expanded_tolerance_set(rtt_repo, monkeypatch):
    import raytatouille as rt

    at = tolerance_view(rtt_repo, monkeypatch)
    items = table(at, "Grenze T")
    system = rt.load(str(rtt_repo / "tests" / "reference" / "m7" / "achromat_tolerances.rtt.json"))
    materials = rt.MaterialLibrary()
    materials.add_catalog(str(rtt_repo / "tests" / "catalogs" / "schott.agf"))
    expected = rt.tolerance.expand(system, materials=materials)
    assert len(items) == len(expected.items)
    assert list(items["Id"]) == [i.id for i in expected.items]
    assert {"Art", "Ziel", "Grenze T", "Einheit", "Verteilung", "Herkunft"} <= set(items.columns)


def test_system_without_tolerances_explains_where_they_come_from(rtt_repo, monkeypatch):
    at = tolerance_view(rtt_repo, monkeypatch, "m1/singlet_const.rtt.json")
    assert any("keinen Toleranzsatz" in i.value for i in at.info)


def test_sensitivity_matches_the_library_and_shares_add_up(rtt_repo, monkeypatch):
    import raytatouille as rt

    at = tolerance_view(rtt_repo, monkeypatch)
    at = click(at, "tol_run_sens")
    ok(at)
    assert not at.error
    shown = table(at, "Φ(+T)")
    assert len(shown) == 26
    assert shown["Anteil (%)"].dropna().sum() == pytest.approx(100.0, abs=1e-6)
    system = rt.load(str(rtt_repo / "tests" / "reference" / "m7" / "achromat_tolerances.rtt.json"))
    materials = rt.MaterialLibrary()
    materials.add_catalog(str(rtt_repo / "tests" / "catalogs" / "schott.agf"))
    crit = rt.tolerance.sensitivity(system, materials=materials, confirm=True).criteria[0]
    assert list(shown["Φ(+T)"]) == pytest.approx([i.plus for i in crit.items], nan_ok=True)


def test_monte_carlo_with_a_small_number_of_trials_shows_yield_and_statistics(rtt_repo, monkeypatch):
    at = tolerance_view(rtt_repo, monkeypatch)
    trials = next(n for n in at.number_input if n.key == "tol_trials")
    trials.set_value(30).run()
    at = click(at, "tol_run_mc")
    ok(at)
    assert not at.error
    assert next(m for m in at.metric if m.label == "Prüflinge gültig").value == "30 von 30"
    stats = table(at, "Ausbeute")
    assert len(stats) == 3 and {"Kriterium", "Grenze", "Mittel", "σ", "50 %"} <= set(stats.columns)


def test_trials_are_capped_in_the_widget(rtt_repo, monkeypatch):
    from rtt_explorer.tolerance_table import MAX_TRIALS

    at = tolerance_view(rtt_repo, monkeypatch)
    trials = next(n for n in at.number_input if n.key == "tol_trials")
    assert trials.max == MAX_TRIALS


def test_same_seed_gives_the_same_result_through_the_view(rtt_repo, monkeypatch):
    def run_once():
        at = tolerance_view(rtt_repo, monkeypatch)
        next(n for n in at.number_input if n.key == "tol_trials").set_value(20)
        next(n for n in at.number_input if n.key == "tol_seed").set_value(7)
        at = at.run()
        at = click(at, "tol_run_mc")
        return table(at, "Ausbeute")[["Mittel", "σ", "Min", "Max"]].to_numpy()

    assert (run_once() == run_once()).all()


def test_view_is_in_the_registry_after_the_optimization():
    from rtt_explorer.views import VIEWS

    names = list(VIEWS)
    assert names.index("Toleranzen") == names.index("Optimierung") + 1


def test_progress_of_a_real_monte_carlo_reaches_the_calling_thread(rtt_repo):
    import threading

    import raytatouille as rt

    from rtt_explorer.progress_run import run_with_progress

    need("tolerance")
    system = rt.load(str(rtt_repo / "tests" / "reference" / "m7" / "achromat_tolerances.rtt.json"))
    materials = rt.MaterialLibrary()
    materials.add_catalog(str(rtt_repo / "tests" / "catalogs" / "schott.agf"))
    ticks, threads = [], set()

    def on_tick(progress):
        ticks.append(progress.snapshot())
        threads.add(threading.get_ident())

    result = run_with_progress(
        lambda progress: rt.tolerance.monte_carlo(system, materials=materials, trials=150, seed=3, progress=progress),
        on_tick, interval=0.02)
    assert result.status.name == "COMPLETED"
    assert threads == {threading.get_ident()}
    assert ticks[-1][:2] == (150, 150) and ticks[-1][2] == "monte_carlo"
    assert [d for d, _, _ in ticks] == sorted(d for d, _, _ in ticks)
