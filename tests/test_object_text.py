"""Object distance and its reference surface in the model view (fakes, plus the real library)."""

from __future__ import annotations

from types import SimpleNamespace as NS

import pytest

from rtt_explorer.model_table import object_text


def P(value):  # noqa: N802 - mirrors model.Param
    return NS(value=value, variable=False, param=None, min=None, max=None)


def test_object_at_infinity():
    assert object_text(NS(at_infinity=True, distance=None, reference=None)) == ("unendlich", None)


def test_finite_object_measured_from_the_origin():
    value, help_text = object_text(NS(at_infinity=False, distance=P(75.0), reference=None))
    assert value == "75 mm"
    assert help_text == "Abstand vom globalen Ursprung längs −z"


def test_finite_object_measured_from_a_surface():
    value, help_text = object_text(NS(at_infinity=False, distance=P(75.0), reference=NS(surface="L1.S1")))
    assert value == "75 mm vor L1.S1"
    assert help_text == "Abstand vor dem nominalen Scheitel der Fläche L1.S1 längs −z"


def test_global_position_is_added_when_known():
    obj = NS(at_infinity=False, distance=P(75.0), reference=NS(surface="IL1"))
    assert object_text(obj, object_z=-55.0)[1].endswith("; das Objekt liegt bei z = -55 mm")


def test_old_library_without_reference_attribute():
    assert object_text(NS(at_infinity=False, distance=P(10.0)))[0] == "10 mm"


@pytest.mark.library
def test_real_library_reference(rtt_repo):
    import raytatouille as rt

    system = rt.load(str(rtt_repo / "tests" / "reference" / "r3" / "object_reference.rtt.json"))
    comp = rt.compile(system)
    value, help_text = object_text(system.object_space, comp.object_z)
    assert value == "75 mm vor IL1" or value.startswith("75 mm vor ")
    assert f"z = {comp.object_z:g} mm" in help_text
