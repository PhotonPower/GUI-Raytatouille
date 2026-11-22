"""View Bestrahlungsstärke (needs the library and a checkout, like ``test_app.py``)."""

from __future__ import annotations

import pytest

from test_app import pick_reference, start
from test_app_library_06 import need, ok, ref, table, view

pytestmark = pytest.mark.library


def irradiance_view(rtt_repo, monkeypatch, name="m1/singlet_const.rtt.json"):
    need("irradiance")
    at = pick_reference(start(rtt_repo, monkeypatch), ref(name))
    at = view(at, "Bestrahlungsstärke")
    ok(at)
    return at


def metric_text(at, label):
    return next(m for m in at.metric if m.label == label).value


def test_default_is_the_last_surface_with_many_rays_counted(rtt_repo, monkeypatch):
    at = irradiance_view(rtt_repo, monkeypatch)
    assert not at.error
    assert next(s for s in at.selectbox if s.key == "irr_surface").value == 3  # IMG, the last event
    counted, launched = metric_text(at, "Strahlen gezählt").split("/")
    assert int(launched) > 0 and 0 < int(counted) <= int(launched)


def test_choosing_a_lens_surface_counts_all_launched_rays_there(rtt_repo, monkeypatch):
    at = irradiance_view(rtt_repo, monkeypatch)
    box = next(s for s in at.selectbox if s.key == "irr_surface")
    at = box.set_value(1).run()  # L1.S1
    ok(at)
    assert not at.error
    counted, launched = metric_text(at, "Strahlen gezählt").split("/")
    assert counted == launched  # every ray reaches the first lens surface


def test_a_large_number_of_rays_is_only_offered_for_the_last_surface(rtt_repo, monkeypatch):
    from rtt_explorer.irradiance_logic import MAX_BATCH_RAYS, MAX_PATH_RAYS

    at = irradiance_view(rtt_repo, monkeypatch)
    def largest(at):
        slider = next(s for s in at.select_slider if s.key == "irr_rays")
        return max(int(o.replace(" ", "")) for o in slider.options)

    assert largest(at) == MAX_BATCH_RAYS
    at = next(s for s in at.selectbox if s.key == "irr_surface").set_value(1).run()
    assert largest(at) == MAX_PATH_RAYS


def test_aperture_area_on_a_surface_without_aperture_is_a_message(rtt_repo, monkeypatch):
    at = irradiance_view(rtt_repo, monkeypatch)
    radio = next(r for r in at.radio if r.key == "irr_extent")
    at = radio.set_value("Apertur der Fläche").run()
    assert not at.exception
    assert any("keine Apertur" in e.value for e in at.error)


def test_manual_area_with_a_swapped_range_is_a_message_not_a_traceback(rtt_repo, monkeypatch):
    at = irradiance_view(rtt_repo, monkeypatch)
    at = next(r for r in at.radio if r.key == "irr_extent").set_value("Frei").run()
    ok(at)
    next(n for n in at.number_input if n.key == "irr_x0").set_value(5.0)
    next(n for n in at.number_input if n.key == "irr_x1").set_value(1.0)
    at = at.run()
    assert not at.exception
    assert any("Bereich leer" in e.value for e in at.error)


def test_double_pass_surface_offers_its_visits(rtt_repo, monkeypatch):
    need("irradiance")
    at = irradiance_view(rtt_repo, monkeypatch, "m7/double_pass.rtt.json")
    surfaces = next(s for s in at.selectbox if s.key == "irr_surface")
    # P.S2 (index 3 in the surface list) is visited twice
    at = surfaces.set_value(3).run()
    ok(at)
    visit = next(s for s in at.selectbox if s.key == "irr_event")
    assert len(visit.options) == 3  # all visits plus two single ones
    both = metric_text(at, "Leistung gezählt")
    at = visit.set_value(2).run()
    ok(at)
    one = metric_text(at, "Leistung gezählt")
    assert float(one) < float(both)


def test_loss_table_names_the_reasons(rtt_repo, monkeypatch):
    at = irradiance_view(rtt_repo, monkeypatch)
    losses = table(at, "Grund")
    assert list(losses["Grund"]) == ["außerhalb des Rasters", "an einer Apertur abgeschattet", "Fläche nicht erreicht"]
