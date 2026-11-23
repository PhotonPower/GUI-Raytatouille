"""The model view explains stop surface and NA reading (needs the library, like ``test_app.py``)."""

from __future__ import annotations

import pytest

from test_app import pick_reference, start
from test_app_library_06 import need, ok, ref, view

pytestmark = pytest.mark.library


def model(rtt_repo, monkeypatch, name):
    return view(pick_reference(start(rtt_repo, monkeypatch), ref(name)), "Modell")


def test_stop_on_a_surface_is_shown(rtt_repo, monkeypatch):
    need("stop_on_surface")
    at = model(rtt_repo, monkeypatch, "m2/cooke_triplet_surface_stop.rtt.json")
    ok(at)
    assert any("aperture.stop" in c.value and "L2.S1" in c.value for c in at.caption)


def test_real_na_reading_is_shown(rtt_repo, monkeypatch):
    need("object_reference")
    at = model(rtt_repo, monkeypatch, "r3/immersion_real_na.rtt.json")
    ok(at)
    assert any("NA real gelesen" in c.value for c in at.caption)


def test_plain_system_has_no_aperture_note(rtt_repo, monkeypatch):
    at = view(start(rtt_repo, monkeypatch), "Modell")
    ok(at)
    assert not any("aperture.stop" in c.value or "gelesen" in c.value for c in at.caption)
