"""Model tree to table rows (pure logic; fakes stand in for raytatouille.model objects)."""

from __future__ import annotations

import math
from types import SimpleNamespace as NS

from rtt_explorer.model_table import aperture_text, param_text, phase_text, shape_text, surface_rows


def P(value=None, variable=False, param=None):  # noqa: N802 - mirrors model.Param
    return NS(value=value, variable=variable, param=param, min=None, max=None)


# Fakes named like the library classes: the table reads the active variant from the type name.
class Plane:
    pass


class Conic:
    def __init__(self, radius, conic):
        self.radius, self.conic = radius, conic


class EvenAsphere(Conic):
    def __init__(self, radius, conic, coefficients):
        super().__init__(radius, conic)
        self.coefficients = coefficients


class CircularAperture:
    def __init__(self, radius, inner_radius=0.0):
        self.radius, self.inner_radius = radius, inner_radius


class RectangularAperture:
    def __init__(self, half_width_x, half_width_y):
        self.half_width_x, self.half_width_y = half_width_x, half_width_y


class Fresnel:
    pass


class CoatingRef:
    def __init__(self, name):
        self.name = name


class LinearGrating:
    def __init__(self, lines_per_mm, orientation_deg=0.0):
        self.lines_per_mm, self.orientation_deg = lines_per_mm, orientation_deg


def stack(base, terms=()):
    return NS(base=base, terms=list(terms))


def pose(z, reference="ABSOLUTE"):
    return NS(position=[P(0.0), P(0.0), z], rotation_deg=[P(0.0), P(0.0), P(0.0)], reference=NS(name=reference))


def surface(sid, base, aperture=None, interaction=None, phases=()):
    return NS(id=sid, shape=stack(base), aperture=aperture, interaction=interaction or Fresnel(),
              phases=list(phases))


def test_param_text_value_variable_and_bound():
    assert param_text(P(50.0)) == "50"
    assert param_text(P(-12.5, variable=True)) == "-12.5 V"
    assert param_text(P(None, param="FOCUS")) == "→ FOCUS"
    assert param_text(None) == ""


def test_shape_text_for_plane_conic_and_asphere():
    assert shape_text(stack(Plane())) == ("plan", "∞", "")
    assert shape_text(stack(Conic(P(40.0), P(-1.0)))) == ("sphärisch/konisch", "40", "-1")
    assert shape_text(stack(Conic(P(math.inf), P(0.0)))) == ("sphärisch/konisch", "∞", "0")
    form, radius, conic = shape_text(stack(EvenAsphere(P(30.0), P(0.0), [1e-5, 2e-8]), terms=[object()]))
    assert form == "Asphäre (2 Koeff.) + 1 Zusatzterm"
    assert (radius, conic) == ("30", "0")


def test_grating_and_aperture_values_may_be_params():
    # In the library LinearGrating.lines_per_mm and aperture sizes are model.Param objects as well.
    assert phase_text([LinearGrating(P(300.0))]) == "Gitter 300 /mm"
    assert aperture_text(CircularAperture(P(12.5), P(0.0))) == "r 12.5"


def test_aperture_text():
    assert aperture_text(None) == "frei"
    assert aperture_text(CircularAperture(12.5)) == "r 12.5"
    assert aperture_text(CircularAperture(12.5, 3.0)) == "r 3 … 12.5"
    assert aperture_text(RectangularAperture(5.0, 2.0)) == "±5 × ±2"


def test_surface_rows_walk_assemblies_in_tree_order():
    lens = NS(name="L1", kind=NS(name="LENS"), pose=pose(P(10.0)), material="SCHOTT:N-BK7",
              segment_materials=[], crystal=None,
              surfaces=[surface("L1.S1", Conic(P(50.0), P(0.0)), CircularAperture(10.0), CoatingRef("AR")),
                        surface("L1.S2", Plane())])
    grating = NS(name="G", kind=NS(name="THIN_ELEMENT"), pose=pose(P(None, param="B"), "RELATIVE_TO_SIBLING"),
                 material=None, segment_materials=[], crystal=None,
                 surfaces=[surface("G", Plane(), phases=[LinearGrating(300.0)])])
    crystal = NS(name="P", kind=NS(name="PLATE"), pose=pose(P(30.0)), material=None, segment_materials=[],
                 crystal=NS(ordinary="BIREFRINGENT:CALCITE", extraordinary="BIREFRINGENT:CALCITE-E"),
                 surfaces=[surface("P.S1", Plane())])
    root = NS(name="root", children=[lens, NS(name="group", children=[grating, crystal])])

    rows = surface_rows(root)

    assert [r["Fläche"] for r in rows] == ["L1.S1", "L1.S2", "G", "P.S1"]
    first = rows[0]
    assert first["Baugruppe"] == ""
    assert first["Element"] == "L1"
    assert first["Art"] == "Linse"
    assert first["Material"] == "SCHOTT:N-BK7"
    assert first["Element-z (mm)"] == "10"
    assert (first["Form"], first["Radius (mm)"], first["Konik"]) == ("sphärisch/konisch", "50", "0")
    assert first["Apertur (mm)"] == "r 10"
    assert first["Wechselwirkung"] == "Coating AR"
    assert rows[1]["Wechselwirkung"] == "Fresnel"
    assert rows[2]["Baugruppe"] == "group"
    assert rows[2]["Art"] == "dünnes Element"
    assert rows[2]["Element-z (mm)"] == "→ B (relativ)"
    assert rows[2]["Phase"] == "Gitter 300 /mm"
    assert rows[3]["Material"] == "BIREFRINGENT:CALCITE / BIREFRINGENT:CALCITE-E"
