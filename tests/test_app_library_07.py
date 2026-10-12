"""Smoke tests of the functions of Raytatouille 0.7 (configurations, optimization, reports, Gauss
pupil). They need the library and a checkout, like ``test_app.py``."""

from __future__ import annotations

import pytest

from test_app import metric, pick_reference, start, widget
from test_app_library_06 import need, ok, ref, table, view

pytestmark = pytest.mark.library


def test_zoom_configurations_change_the_focal_length(rtt_repo, monkeypatch):
    need("configs")
    at = pick_reference(start(rtt_repo, monkeypatch), ref("m5/zoom.rtt.json"))
    ok(at)
    box = widget(at, "selectbox", "Konfiguration")
    assert box.options == ["wide", "tele"]
    efl_wide = metric(at, "Brennweite EFL")
    at = box.set_value("tele").run()
    ok(at)
    assert at.subheader[0].value.endswith("Konfiguration tele")
    assert metric(at, "Brennweite EFL") != pytest.approx(efl_wide, rel=1e-3)


def test_optimizing_two_lens_gap_reproduces_the_library_result(rtt_repo, monkeypatch):
    need("optim")
    # tests/reference/results/OptimResult.result.json of the library: default options give
    # CONVERGED_STEP with D = 19.564727703597345 mm.
    at = pick_reference(start(rtt_repo, monkeypatch), ref("m5/two_lens_gap.rtt.json"))
    at = view(at, "Optimierung")
    ok(at)
    at = widget(at, "button", "Optimieren").click().run()
    ok(at)
    assert next(m for m in at.metric if m.label == "Status").value == "konvergiert (Schrittweite)"
    variables = table(at, "Ende").set_index("Variable")
    assert variables.loc["D", "Ende"] == pytest.approx(19.564727703597345, rel=1e-6)

    at = widget(at, "button", "Ergebnis übernehmen").click().run()
    ok(at)
    assert any("optimierte System ist aktiv" in i.value for i in at.info)
    at = widget(at, "button", "Verwerfen").click().run()
    ok(at)
    assert not any("optimierte System ist aktiv" in i.value for i in at.info)


def test_optimization_view_explains_a_system_without_merit_function(rtt_repo, monkeypatch):
    need("optim")
    at = view(start(rtt_repo, monkeypatch), "Optimierung")
    ok(at)
    assert any("keine Variablen" in i.value for i in at.info)


def test_reports_of_the_cooke_triplet(rtt_repo, monkeypatch):
    need("reports")
    at = view(start(rtt_repo, monkeypatch), "Reports")
    ok(at)
    dims = table(at, "centre_thickness")
    assert len(dims) == 3  # three singlets
    assert set(dims["element"]) == {"L1", "L2", "L3"}
    trace = table(at, "local_x")
    assert "Start" in set(trace["surface"])


def test_bundle_with_gauss_pupil(rtt_repo, monkeypatch):
    need("gauss")
    at = view(start(rtt_repo, monkeypatch), "Strahlenbündel")
    at = widget(at, "selectbox", "Pupillenraster").set_value("Gauß-Quadratur (Ringe × 6 Arme)").run()
    ok(at)


def test_builder_variables_optimize_and_write_back_into_the_table(rtt_repo, monkeypatch):
    need("optim")
    import pandas as pd

    from rtt_explorer.builder import MERIT_COLUMNS, VARIABLE_COLUMNS

    at = start(rtt_repo, monkeypatch)
    at = widget(at, "radio", "System").set_value("System bauen").run()  # preset: plano-convex singlet
    ok(at)
    df = at.session_state["bdf"].copy()
    for col in VARIABLE_COLUMNS:
        df[col] = False
    df.loc[1, "R_var"] = True  # radius of L1.S1
    df.loc[2, "D_var"] = True  # distance L1.S2 -> image
    at.session_state["bdf"] = df
    at.session_state["bver"] = at.session_state["bver"] + 1
    at.session_state["bmerit"] = pd.DataFrame([["EFL", 80.0, 1.0], ["Randstrahl im Fokus", None, 1.0],
                                               ["RMS-Spot", None, 1.0]], columns=MERIT_COLUMNS)
    at = view(at.run(), "Optimierung")
    ok(at)
    at = widget(at, "button", "Optimieren").click().run()
    ok(at)
    assert {"R2", "D3"} <= set(table(at, "Ende")["Variable"])
    at = widget(at, "button", "Ergebnis in die Flächentabelle übernehmen").click().run()
    ok(at)
    # Plano-convex lens n = 1.5168 with f = 80 mm: R = f (n - 1) is about 41.3 mm
    assert at.session_state["bdf"].loc[1, "Radius_mm"] == pytest.approx(41.3, abs=0.2)
    assert metric(at, "Brennweite EFL") == pytest.approx(80.0, abs=0.01)


@pytest.mark.parametrize("name", ["m5/singlet_solve.rtt.json", "m5/singlet_optim.rtt.json", "m5/zoom.rtt.json"])
@pytest.mark.parametrize("view_name", ["Optimierung", "Reports", "Modell", "Layout"])
def test_m5_systems_render(rtt_repo, monkeypatch, name, view_name):
    at = pick_reference(start(rtt_repo, monkeypatch), ref(name))
    at = view(at, view_name)
    ok(at)
