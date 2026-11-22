"""Design helper in the builder (needs the library and a checkout, like ``test_app.py``)."""

from __future__ import annotations

import json

import pytest

from test_app import metric, start, widget
from test_app_library_06 import need, ok

pytestmark = pytest.mark.library


def builder(rtt_repo, monkeypatch):
    need("design")
    at = start(rtt_repo, monkeypatch)
    at = widget(at, "radio", "System").set_value("System bauen").run()
    ok(at)
    return at


def test_helper_is_offered_in_the_builder(rtt_repo, monkeypatch):
    at = builder(rtt_repo, monkeypatch)
    assert any(b.key == "design_apply" for b in at.button)
    assert {s.key for s in at.selectbox if s.key} >= {"design_kind"}


def test_doublet_replaces_the_table_and_the_header_shows_its_focal_length(rtt_repo, monkeypatch):
    import raytatouille as rt

    at = builder(rtt_repo, monkeypatch)
    at = at.selectbox(key="design_kind").set_value("doublet").run()
    at = next(b for b in at.button if b.key == "design_apply").click().run()
    ok(at)
    df = at.session_state["bdf"]
    assert list(df["Typ"]) == ["Blende", "Fläche", "Fläche", "Fläche", "Bild"]
    assert list(df["Radius_mm"][1:4]) == [62.0, -44.0, -130.0]
    assert list(df["Material_danach"][1:4]) == ["CONST:1.5168", "CONST:1.62", "AIR"]
    expected = rt.paraxial.first_order(rt.compile(
        rt.design.doublet((62.0, -44.0, -130.0), (4.0, 2.5), ("CONST:1.5168", "CONST:1.62"), epd=20.0,
                          stop_distance=5.0, image_distance=96.0, semi_diameter=12.7),
        rt.MaterialLibrary())).efl
    assert metric(at, "Brennweite EFL") == pytest.approx(expected, rel=1e-6)


def test_wrong_number_of_radii_is_a_message_not_a_traceback(rtt_repo, monkeypatch):
    at = builder(rtt_repo, monkeypatch)
    before = at.session_state["bdf"].copy()
    at.text_input(key="design_radii_singlet").set_value("100")
    at = next(b for b in at.button if b.key == "design_apply").click().run()
    assert not at.exception
    assert any("Radien: 2 Werte erwartet, 1 gefunden" in e.value for e in at.error)
    assert at.session_state["bdf"].equals(before)


def test_library_error_is_shown_as_a_message(rtt_repo, monkeypatch):
    at = builder(rtt_repo, monkeypatch)
    at.text_input(key="design_materials_singlet").set_value("")
    at = next(b for b in at.button if b.key == "design_apply").click().run()
    assert not at.exception
    assert any("Konstruktionshelfer" in e.value or "Gläser" in e.value for e in at.error)


def test_catalog_upload_lists_the_lenses(rtt_repo, monkeypatch):
    # AppTest has no file_uploader support in every Streamlit version: test the reader directly.
    import raytatouille as rt

    from rtt_explorer.ui.design_helper import _read_catalog

    need("design")
    text = json.dumps({"format": "raytatouille-lenses", "schema_version": "0.1.0", "catalog": "T", "lenses": [
        {"name": "PCX", "kind": "singlet", "radii": [51.68, None], "thicknesses": [4.0],
         "materials": ["CONST:1.5168"], "diameter": 25.4}]})

    class Upload:
        def getvalue(self):
            return text.encode()

    assert list(_read_catalog(Upload())) == ["PCX"]
    assert _read_catalog(None) == {}
    assert rt.design.parse_lens_catalog(text)["PCX"].kind == "singlet"
