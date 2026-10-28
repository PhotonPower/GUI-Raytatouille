"""Smoke tests of the zoom controls of the view "Layout". They need the library and a checkout,
like ``test_app.py``."""

from __future__ import annotations

import pytest

from test_app import start, widget
from test_app_library_06 import need, ok, view

pytestmark = pytest.mark.library


def layout(rtt_repo, monkeypatch):
    need("paths")
    at = view(start(rtt_repo, monkeypatch), "Layout")
    ok(at)
    return at


def test_buttons_start_with_the_whole_system(rtt_repo, monkeypatch):
    at = layout(rtt_repo, monkeypatch)
    assert at.session_state["layout_view_mode"] == "all"
    assert not widget(at, "button", "Auf Quelle zoomen").disabled


def test_source_button_sets_a_window_around_the_start_of_the_rays(rtt_repo, monkeypatch):
    at = layout(rtt_repo, monkeypatch)
    at = widget(at, "button", "Auf Quelle zoomen").click().run()
    ok(at)
    assert at.session_state["layout_view_mode"] == "source"
    z0, z1, l0, l1 = at.session_state["layout_view_box"]
    assert z1 - z0 == pytest.approx(6.0)  # default half width 3 mm
    assert (z1 - z0) / (l1 - l0) == pytest.approx(0.775 * 11.0 / (0.77 * 4.8))  # aspect of the axes box
    at = widget(at, "number_input", "Quellfenster ± mm").set_value(1.0).run()
    ok(at)
    assert at.session_state["layout_view_mode"] == "source"  # the window follows the field


def test_whole_system_button_returns_from_a_window(rtt_repo, monkeypatch):
    at = layout(rtt_repo, monkeypatch)
    at = widget(at, "button", "Auf Quelle zoomen").click().run()
    at = widget(at, "button", "Gesamtes System").click().run()
    ok(at)
    assert at.session_state["layout_view_mode"] == "all"


def test_chosen_window_is_applied_and_kept(rtt_repo, monkeypatch):
    at = layout(rtt_repo, monkeypatch)
    for label, value in [("z von (mm)", 5.0), ("z bis (mm)", 20.0), ("y von (mm)", -3.0), ("y bis (mm)", 3.0)]:
        widget(at, "number_input", label).set_value(value)
    at = widget(at.run(), "button", "Ausschnitt übernehmen").click().run()
    ok(at)
    assert at.session_state["layout_view_mode"] == "box"
    assert at.session_state["layout_view_box"] == (5.0, 20.0, -3.0, 3.0)
    at = widget(at, "checkbox", "Gleiche Achsenskalierung").uncheck().run()
    ok(at)
    assert at.session_state["layout_view_mode"] == "box"  # survives a change of another setting


def test_empty_window_is_refused_with_a_message(rtt_repo, monkeypatch):
    at = layout(rtt_repo, monkeypatch)
    for label, value in [("z von (mm)", 20.0), ("z bis (mm)", 5.0)]:
        widget(at, "number_input", label).set_value(value)
    at = widget(at.run(), "button", "Ausschnitt übernehmen").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert [e.value for e in at.error] == ["Ausschnitt leer: es muss z von < z bis und unten < oben gelten"]
    assert at.session_state["layout_view_mode"] == "all"


def test_image_button_sets_a_window_in_front_of_the_image_plane(rtt_repo, monkeypatch):
    at = layout(rtt_repo, monkeypatch)
    assert not widget(at, "button", "Auf Bildebene zoomen").disabled
    at = widget(at, "button", "Auf Bildebene zoomen").click().run()
    ok(at)
    assert at.session_state["layout_view_mode"] == "image"
    z0, z1, l0, l1 = at.session_state["layout_view_box"]
    assert z1 - z0 == pytest.approx(22.0)  # default width 20 mm in front, a tenth of it behind
    assert l1 > 0.0 and l0 == pytest.approx(-l1)
    at = widget(at, "number_input", "Bildfenster vor der Bildebene (mm)").set_value(5.0).run()
    ok(at)
    assert at.session_state["layout_view_mode"] == "image"  # the window follows the field


def test_there_is_no_checkbox_for_the_image_plane_any_more(rtt_repo, monkeypatch):
    at = layout(rtt_repo, monkeypatch)
    assert "Auf die Bildebene zoomen" not in [c.label for c in at.checkbox]


def lost_rays_script():
    """Controls with a bundle in which every ray is lost: positions after the start are NaN."""
    from types import SimpleNamespace

    import matplotlib.pyplot as plt
    import numpy as np
    import streamlit as st

    from rtt_explorer.views.layout import _zoom_controls

    position = np.full((3, 2, 3), np.nan)
    position[:, 0, :] = 0.0
    recorded = SimpleNamespace(position=position, lost_at=np.array([0, 0, 0]))
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.plot([0.0, 100.0], [0.0, 0.0])
    st.session_state["window"] = _zoom_controls(ax, fig, [(recorded,)], 1, "y", [np.array([0.0])],
                                                [np.array([0.0])])


def test_image_button_is_off_and_nothing_fails_if_every_ray_is_lost():
    # Regression: "Axis limits cannot be NaN or Inf" when no ray reaches the image plane
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(lost_rays_script, default_timeout=60).run()
    assert not at.exception, [e.value for e in at.exception]
    assert widget(at, "button", "Auf Bildebene zoomen").disabled
    assert not widget(at, "button", "Auf Quelle zoomen").disabled  # the rays do have a start
    at.session_state["layout_view_mode"] = "image"  # a window chosen earlier, then the rays get lost
    at = at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state["window"] is None  # whole system instead of NaN limits
    assert "Kein Strahl erreicht die Bildebene" in at.caption[0].value
