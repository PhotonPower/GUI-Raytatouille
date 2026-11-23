"""Anamorphic systems: first-order data per section instead of the paraxial info message.

Needs the library; the systems are written to a stand-in checkout because AppTest cannot upload files."""

from __future__ import annotations

import json
import shutil

import pytest

from test_app import start, widget
from test_app_library_06 import need, ok, ref
from test_model_table_shapes import CASES, system_with

pytestmark = pytest.mark.library


@pytest.fixture
def anamorphic_repo(tmp_path, rtt_repo):
    reference = tmp_path / "tests" / "reference"
    (reference / "m1").mkdir(parents=True)
    shutil.copy(rtt_repo / "tests" / "reference" / "m1" / "singlet_const.rtt.json", reference / "m1")
    for name in ("biconic", "cylinder", "axicon"):
        (reference / "ana").mkdir(exist_ok=True)
        (reference / "ana" / f"{name}.rtt.json").write_text(json.dumps(system_with(CASES[name][0])),
                                                            encoding="utf-8")
    return tmp_path


def pick(at, name):
    return widget(at, "selectbox", "Beispielsystem").set_value(ref(f"ana/{name}.rtt.json")).run()


def metrics(at):
    return {m.label: m.value for m in at.metric}


def test_biconic_shows_efl_and_bfl_for_both_sections(anamorphic_repo, monkeypatch):
    import raytatouille as rt

    need("anamorphic_first_order")
    at = pick(start(anamorphic_repo, monkeypatch), "biconic")
    ok(at)
    comp = rt.compile(rt.load(str(anamorphic_repo / "tests" / "reference" / "ana" / "biconic.rtt.json")))
    fx = rt.paraxial.first_order_section(comp, path="main", section=rt.paraxial.Section.X)
    fy = rt.paraxial.first_order_section(comp, path="main", section=rt.paraxial.Section.Y)
    values = metrics(at)

    def pair(label):
        return [float(v) for v in values[label].removesuffix(" mm").split(" | ")]

    # The app compiles in air (Ciddor, n' about 1.00027), the check here in vacuum: 1e-3 relative.
    for label, getter in (("Brennweite EFL (x | y)", lambda f: f.efl),
                          ("Schnittweite BFL (x | y)", lambda f: f.bfl),
                          ("Paraxiale Bildebene z (x | y)", lambda f: f.rear_focal_z)):
        assert pair(label) == pytest.approx([getter(fx), getter(fy)], rel=1e-3)
    assert not any("Paraxiale Kenndaten nicht verfügbar" in i.value for i in at.info)


def test_cylinder_is_afocal_in_one_section(anamorphic_repo, monkeypatch):
    need("anamorphic_first_order")
    at = pick(start(anamorphic_repo, monkeypatch), "cylinder")
    ok(at)
    assert metrics(at)["Brennweite EFL (x | y)"].startswith("– | ")


def test_axicon_keeps_the_info_message(anamorphic_repo, monkeypatch):
    need("anamorphic_first_order")
    at = pick(start(anamorphic_repo, monkeypatch), "axicon")
    ok(at)
    assert any("Paraxiale Kenndaten nicht verfügbar" in i.value for i in at.info)
    assert "Brennweite EFL (x | y)" not in metrics(at)


def test_rotational_system_is_unchanged(anamorphic_repo, monkeypatch):
    need("anamorphic_first_order")
    at = widget(start(anamorphic_repo, monkeypatch), "selectbox", "Beispielsystem").set_value(
        ref("m1/singlet_const.rtt.json")).run()
    ok(at)
    assert "Brennweite EFL" in metrics(at)
    assert "Brennweite EFL (x | y)" not in metrics(at)
