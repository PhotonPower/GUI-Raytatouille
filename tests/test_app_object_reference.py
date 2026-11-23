"""The model view shows the reference surface of the object (needs the library, like ``test_app.py``)."""

from __future__ import annotations

import pytest

from test_app import pick_reference, start
from test_app_library_06 import need, ok, ref, view

pytestmark = pytest.mark.library


def object_metric(at):
    return next(m for m in at.metric if m.label == "Objekt")


def test_object_with_a_reference_surface(rtt_repo, monkeypatch):
    need("object_reference")
    import raytatouille as rt

    name = "r3/object_reference.rtt.json"
    at = view(pick_reference(start(rtt_repo, monkeypatch), ref(name)), "Modell")
    ok(at)
    system = rt.load(str(rtt_repo / "tests" / "reference" / name))
    surface = system.object_space.reference.surface
    metric = object_metric(at)
    assert metric.value == f"75 mm vor {surface}"
    assert "nominalen Scheitel" in metric.help


def test_object_without_reference_and_at_infinity(rtt_repo, monkeypatch):
    at = view(start(rtt_repo, monkeypatch), "Modell")
    ok(at)
    assert object_metric(at).value == "unendlich"
