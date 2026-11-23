"""Builder with surface forms in the running app (needs the library, like ``test_app.py``)."""

from __future__ import annotations

import pandas as pd
import pytest

from test_app import metric, start, widget
from test_app_library_06 import need, ok, table, view

pytestmark = pytest.mark.library


def builder_with(rtt_repo, monkeypatch, form, extra, radius=48.0, conic=0.0):
    from rtt_explorer.builder import BUILDER_COLUMNS, SHAPE_COLUMNS, VARIABLE_COLUMNS

    need("surface_types")
    at = widget(start(rtt_repo, monkeypatch), "radio", "System").set_value("System bauen").run()
    df = pd.DataFrame([["Blende", 0.0, 0.0, 5.0, "AIR", 10.0, ""],
                       ["Fläche", radius, conic, 4.0, "CONST:1.5168", 12.7, ""],
                       ["Fläche", 0.0, 0.0, 90.0, "AIR", 12.7, ""],
                       ["Bild", 0.0, 0.0, 0.0, "AIR", 0.0, ""]], columns=BUILDER_COLUMNS)
    for col in VARIABLE_COLUMNS:
        df[col] = False
    for col in SHAPE_COLUMNS:
        df[col] = ""
    df.loc[1, "Form"], df.loc[1, "Form_Parameter"] = form, extra
    at.session_state["bdf"] = df
    at.session_state["bver"] = at.session_state["bver"] + 1
    return at.run()


def test_biconic_in_the_builder_shows_the_sections_the_model_and_the_layout(rtt_repo, monkeypatch):
    at = builder_with(rtt_repo, monkeypatch, "Biconic", "radius_y=-60", 40.0, -0.5)
    ok(at)
    values = {m.label: m.value for m in at.metric}
    assert "Brennweite EFL (x | y)" in values
    model = view(at, "Modell")
    ok(model)
    surfaces = table(model, "Fläche")
    assert surfaces.loc[surfaces["Fläche"] == "L1.S1", "Form"].iloc[0] == "anamorph (Biconic)"
    ok(view(at, "Layout"))


def test_odd_asphere_zero_terms_keeps_the_plain_focal_length(rtt_repo, monkeypatch):
    plain = metric(builder_with(rtt_repo, monkeypatch, "", "", 51.68, -0.5), "Brennweite EFL")
    odd = builder_with(rtt_repo, monkeypatch, "Odd Asphere", "coefficients=0, 0", 51.68, -0.5)
    ok(odd)
    assert metric(odd, "Brennweite EFL") == pytest.approx(plain, rel=1e-9)


def test_wrong_form_parameter_is_a_message_not_a_traceback(rtt_repo, monkeypatch):
    at = builder_with(rtt_repo, monkeypatch, "Biconic", "radius_z=3", 40.0)
    assert not at.exception
    assert any("Form Biconic kennt den Schlüssel 'radius_z' nicht" in e.value for e in at.error)
