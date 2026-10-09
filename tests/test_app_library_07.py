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


@pytest.mark.parametrize("name", ["m5/singlet_solve.rtt.json", "m5/singlet_optim.rtt.json", "m5/zoom.rtt.json"])
@pytest.mark.parametrize("view_name", ["Optimierung", "Reports", "Modell", "Layout"])
def test_m5_systems_render(rtt_repo, monkeypatch, name, view_name):
    at = pick_reference(start(rtt_repo, monkeypatch), ref(name))
    at = view(at, view_name)
    ok(at)
