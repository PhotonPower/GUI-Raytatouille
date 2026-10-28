"""View "Detektorbild". They need the library and a checkout, like ``test_app.py``."""

from __future__ import annotations

import pytest

from test_app import start, widget
from test_app_library_06 import need, ok, view

pytestmark = pytest.mark.library


def detector_image(rtt_repo, monkeypatch):
    need("paths")
    at = view(start(rtt_repo, monkeypatch), "Detektorbild")
    ok(at)
    return at


def metric_text(at, label: str) -> str:
    return next(m for m in at.metric if m.label == label).value


def test_the_view_shows_an_image_with_the_defaults(rtt_repo, monkeypatch):
    at = detector_image(rtt_repo, monkeypatch)
    arrived, launched = metric_text(at, "Strahlen angekommen").split("/")
    assert 0 < int(arrived) <= int(launched)
    assert "µm" in metric_text(at, "Pixelgröße")
    assert any("Pixeln beleuchtet" in c.value for c in at.caption)


def test_more_pixels_make_smaller_pixels_and_do_not_trace_again(rtt_repo, monkeypatch):
    at = detector_image(rtt_repo, monkeypatch)
    before = metric_text(at, "Pixelgröße")
    at = widget(at, "number_input", "Pixel x").set_value(512).run()
    ok(at)
    after = metric_text(at, "Pixelgröße")
    assert float(after.split()[0]) == pytest.approx(float(before.split()[0]) / 2.0, rel=1e-3)


def test_log_scale_colour_map_and_square_field_of_view_work(rtt_repo, monkeypatch):
    at = detector_image(rtt_repo, monkeypatch)
    at = widget(at, "radio", "Skala").set_value("logarithmisch").run()
    ok(at)
    at = widget(at, "selectbox", "Farbtabelle").set_value("inferno").run()
    ok(at)
    at = widget(at, "checkbox", "Quadratisches Bildfeld").check().run()
    ok(at)
    x, y = (float(t) for t in metric_text(at, "Pixelgröße").replace("µm", "").split("×"))
    assert x == pytest.approx(y, rel=1e-3)  # 256 x 256 pixels on a square field of view


def test_a_manual_field_of_view_and_an_empty_one(rtt_repo, monkeypatch):
    at = detector_image(rtt_repo, monkeypatch)
    at = widget(at, "checkbox", "Bildfeld festlegen").check().run()
    ok(at)
    at = widget(at, "number_input", "x von (mm)").set_value(-1.0).run()
    at = widget(at, "number_input", "x bis (mm)").set_value(1.0).run()
    ok(at)  # a valid field of view: no message
    x_pitch = float(metric_text(at, "Pixelgröße").split()[0])
    assert x_pitch == pytest.approx(2000.0 / 256, rel=1e-3)  # 2 mm on 256 pixels
    at = widget(at, "number_input", "x bis (mm)").set_value(-2.0).run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("Bildfeld leer" in e.value for e in at.error)


def test_the_isotropic_source_is_offered_and_explained_for_an_object_at_infinity(rtt_repo, monkeypatch):
    at = detector_image(rtt_repo, monkeypatch)  # the start system has its object at infinity
    at = widget(at, "radio", "Quelle").set_value("isotrop (je Raumwinkel)").run()
    ok(at)
    assert any("nur bei einer Punktquelle" in c.value for c in at.caption)


def test_few_rays_for_many_pixels_warn_about_noise(rtt_repo, monkeypatch):
    at = detector_image(rtt_repo, monkeypatch)
    at = widget(at, "number_input", "Pixel x").set_value(4096).run()
    at = widget(at, "number_input", "Pixel y").set_value(4096).run()
    ok(at)
    assert any("rauscht" in w.value for w in at.warning)
