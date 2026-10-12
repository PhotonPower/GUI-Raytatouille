"""Ideal lenses of the model tree (pure logic; fakes stand in for raytatouille.model objects)."""

from __future__ import annotations

from types import SimpleNamespace as NS

import pytest

from rtt_explorer.model_table import ideal_lenses, interaction_text, power_in_plane


def P(value=None, variable=False, param=None):  # noqa: N802 - mirrors model.Param
    return NS(value=value, variable=variable, param=param, min=None, max=None)


# Fakes named like the library classes: the table reads the active variant from the type name.
class IdealLens:
    def __init__(self, focal_length, object_distance=None):
        self.focal_length, self.object_distance = focal_length, object_distance


class IdealCylinderLens(IdealLens):
    def __init__(self, focal_length, axis_deg=0.0, object_distance=None):
        super().__init__(focal_length, object_distance)
        self.axis_deg = axis_deg


class Fresnel:
    pass


def test_interaction_text_of_ideal_lenses():
    assert interaction_text(IdealLens(P(50.0))) == "ideale Linse f = 50"
    assert interaction_text(IdealLens(P(50.0), P(75.0))) == "ideale Linse f = 50, Objekt 75"
    assert interaction_text(IdealLens(P(-20.0, variable=True))) == "ideale Linse f = -20 V"
    assert interaction_text(IdealCylinderLens(P(50.0), 90.0)) == "ideale Zylinderlinse f = 50, Achse 90°"


def element(name, *surfaces):
    return NS(name=name, surfaces=list(surfaces))


def test_ideal_lenses_maps_surface_ids_to_kind_focal_length_and_axis():
    root = NS(name="root", children=[
        element("stop", NS(id="STO", interaction=Fresnel())),
        NS(name="group", children=[element("il", NS(id="IL", interaction=IdealLens(P(50.0), P(75.0))))]),
        element("cl", NS(id="CL", interaction=IdealCylinderLens(P(-40.0), 30.0))),
    ])
    assert ideal_lenses(root) == {
        "IL": {"cylinder": False, "f": 50.0, "axis_deg": 0.0},
        "CL": {"cylinder": True, "f": -40.0, "axis_deg": 30.0},
    }


def test_ideal_lenses_skips_bound_focal_lengths_without_value():
    root = NS(name="root", children=[element("il", NS(id="IL", interaction=IdealLens(P(None, param="F"))))])
    assert ideal_lenses(root) == {"IL": {"cylinder": False, "f": None, "axis_deg": 0.0}}


@pytest.mark.parametrize(("cylinder", "axis", "plane", "power"), [
    (False, 0.0, "yz", True), (False, 0.0, "xz", True),
    # power along (-sin psi, cos psi): axis 0 deg acts in y, axis 90 deg in x
    (True, 0.0, "yz", True), (True, 0.0, "xz", False),
    (True, 90.0, "yz", False), (True, 90.0, "xz", True),
    (True, 45.0, "yz", True), (True, 45.0, "xz", True),
])
def test_power_in_the_drawing_plane(cylinder, axis, plane, power):
    assert power_in_plane({"cylinder": cylinder, "f": 50.0, "axis_deg": axis}, plane) is power
