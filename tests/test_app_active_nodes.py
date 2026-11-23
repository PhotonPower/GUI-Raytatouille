"""Switching components off in the running app (needs the library; systems come from a stand-in checkout)."""

from __future__ import annotations

import copy
import json
import shutil

import pytest

from test_app import metric, start, widget
from test_app_library_06 import need, ok, ref

pytestmark = pytest.mark.library

BASE = {
    "schema_version": "0.2.0", "name": "plate", "units": {"length": "mm", "wavelength": "um"},
    "wavelengths": [{"um": 0.5876, "reference": True}], "aperture": {"type": "epd", "value": 10.0},
    "fields": {"type": "angle_deg", "points": [{}]},
    "root": {"type": "assembly", "name": "system", "children": [
        {"type": "stop", "name": "stop", "surfaces": [{"id": "STO", "aperture": {"type": "circular", "radius": 5.0}}]},
        {"type": "lens", "name": "L1", "pose": {"position": [0, 0, 5.0]}, "material": "CONST:1.5168", "surfaces": [
            {"id": "L1.S1", "shape": {"base": {"type": "conic", "radius": 51.68}},
             "aperture": {"type": "circular", "radius": 12.7}},
            {"id": "L1.S2", "pose": {"position": [0, 0, 4.0]}, "aperture": {"type": "circular", "radius": 12.7}}]},
        {"type": "plate", "name": "Filter", "pose": {"position": [0, 0, 30.0]}, "material": "CONST:1.5", "surfaces": [
            {"id": "F.S1", "aperture": {"type": "circular", "radius": 12.7}},
            {"id": "F.S2", "pose": {"position": [0, 0, 10.0]}, "aperture": {"type": "circular", "radius": 12.7}}]},
        {"type": "detector", "name": "image", "pose": {"position": [0, 0, 100.0]}, "surfaces": [{"id": "IMG"}]}]},
    "paths": [{"name": "main", "events": "auto"}],
}


@pytest.fixture
def repo(tmp_path, rtt_repo):
    reference = tmp_path / "tests" / "reference"
    (reference / "m1").mkdir(parents=True)
    shutil.copy(rtt_repo / "tests" / "reference" / "m1" / "singlet_const.rtt.json", reference / "m1")
    (reference / "act").mkdir()
    without = copy.deepcopy(BASE)
    del without["root"]["children"][2]
    for name, data in (("with_filter", BASE), ("without_filter", without)):
        (reference / "act" / f"{name}.rtt.json").write_text(json.dumps(data), encoding="utf-8")
    return tmp_path


def pick(at, name):
    return widget(at, "selectbox", "Beispielsystem").set_value(ref(f"act/{name}.rtt.json")).run()


def switches(at):
    return {c.label: c for c in at.checkbox if c.key and c.key.startswith("act_")}


def test_switching_the_filter_off_equals_the_system_without_it(repo, monkeypatch):
    need("inactive")
    at = pick(start(repo, monkeypatch), "with_filter")
    ok(at)
    bfl_with = metric(at, "Schnittweite BFL")
    box = switches(at)["Filter (Platte)"]
    assert box.value is True
    at = box.uncheck().run()
    ok(at)
    assert any("ausgeschaltet" in i.value for i in at.info)
    reference = metric(pick(start(repo, monkeypatch), "without_filter"), "Schnittweite BFL")
    assert metric(at, "Schnittweite BFL") == pytest.approx(reference, rel=1e-12)
    assert bfl_with != pytest.approx(reference, rel=1e-6)  # the glass plate shifts the focus
    at = switches(at)["Filter (Platte)"].check().run()
    assert metric(at, "Schnittweite BFL") == pytest.approx(bfl_with, rel=1e-12)


def test_expander_lists_the_nodes_of_a_system(repo, monkeypatch):
    need("inactive")
    at = widget(start(repo, monkeypatch), "selectbox", "Beispielsystem").set_value(
        ref("m1/singlet_const.rtt.json")).run()
    ok(at)
    assert sorted(switches(at)) == sorted([c.label for c in switches(at).values()])
    assert len(switches(at)) == 3  # stop, lens and image


def test_switching_off_the_stop_is_a_message_not_a_traceback(repo, monkeypatch):
    need("inactive")
    at = pick(start(repo, monkeypatch), "with_filter")
    at = switches(at)["stop (Blende)"].uncheck().run()
    assert not at.exception
    assert at.error or at.warning
    assert any("Blende" in m.value or "stop" in m.value.lower() for m in list(at.error) + list(at.warning))
