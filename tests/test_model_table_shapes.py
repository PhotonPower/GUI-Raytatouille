"""The model table for the surface shapes of library 0.10 (pure logic with fakes, plus the real library)."""

from __future__ import annotations

import json
from types import SimpleNamespace as NS

import pytest

from rtt_explorer.model_table import shape_text, surface_rows


def P(value=None, variable=False, param=None):  # noqa: N802 - mirrors model.Param
    return NS(value=value, variable=variable, param=param, min=None, max=None)


# Fakes named like the library classes: the table reads the active variant from the type name.
class Biconic:
    def __init__(self, radius_x, radius_y, conic_x, conic_y):
        self.radius_x, self.radius_y, self.conic_x, self.conic_y = radius_x, radius_y, conic_x, conic_y


class Toroid:
    def __init__(self, radius, conic, coefficients, radius_of_rotation):
        self.radius, self.conic, self.coefficients = radius, conic, coefficients
        self.radius_of_rotation = radius_of_rotation


class Cylinder:
    def __init__(self, radius, conic, coefficients):
        self.radius, self.conic, self.coefficients = radius, conic, coefficients


class OddAsphere:
    def __init__(self, curvature, conic, coefficients):
        self.curvature, self.conic, self.coefficients = curvature, conic, coefficients


class QCon(OddAsphere):
    pass


class QBfs(OddAsphere):
    pass


class Axicon:
    def __init__(self, angle_deg):
        self.angle_deg = angle_deg


class XyPolynomial:
    pass


class GridSag:
    pass


def stack(base, terms=()):
    return NS(base=base, terms=list(terms))


def test_biconic_shows_both_radii_and_conics():
    form, radius, conic = shape_text(stack(Biconic(P(40.0), P(-60.0), P(-0.5), P(0.0))))
    assert (form, radius, conic) == ("anamorph (Biconic)", "40 / -60", "-0.5 / 0")


def test_toroid_and_cylinder():
    assert shape_text(stack(Toroid(P(48.0), P(0.0), [P(2e-6)], P(55.0)))) == \
        ("Toroid (Rotationsradius 55, 1 Koeff.)", "48", "0")
    assert shape_text(stack(Cylinder(P(-75.0), P(0.0), []))) == ("Zylinder", "-75", "0")
    assert shape_text(stack(Cylinder(P(-75.0), P(-1.0), [P(1e-6), P(1e-9)])))[0] == "Zylinder (2 Koeff.)"


def test_curvature_shapes_are_shown_with_their_radius():
    form, radius, conic = shape_text(stack(OddAsphere(P(0.02), P(-0.5), [P(0.0), P(1e-4)])))
    assert (form, radius, conic) == ("Odd Asphere (2 Koeff.)", "50", "-0.5")
    assert shape_text(stack(OddAsphere(P(0.0), P(0.0), [])))[1] == "∞"
    assert shape_text(stack(QCon(P(0.025), P(-0.8), [P(0.0)])))[:2] == ("Forbes Q-con (1 Koeff.)", "40")
    assert shape_text(stack(QBfs(P(-0.02), P(0.0), [])))[:2] == ("Forbes Q-bfs (0 Koeff.)", "-50")


def test_curvature_that_is_a_variable_or_bound_is_marked():
    assert shape_text(stack(OddAsphere(P(0.02, variable=True), P(0.0), [])))[1] == "50 V"
    assert shape_text(stack(OddAsphere(P(None, param="C1"), P(0.0), [])))[1] == "c → C1"


def test_axicon_shows_the_base_angle():
    assert shape_text(stack(Axicon(P(-5.0)))) == ("Axicon (-5°)", "", "")


def test_freeform_terms_are_named():
    form = shape_text(stack(OddAsphere(P(0.02), P(0.0), []), terms=[XyPolynomial(), GridSag()]))[0]
    assert form == "Odd Asphere (0 Koeff.) + 2 Zusatzterme (XY-Polynom, Gitter)"


def test_unknown_shape_still_gets_a_row():
    class Spline:
        pass

    assert shape_text(stack(Spline())) == ("Spline", "", "")


CASES = {
    "biconic": ({"type": "biconic", "radius_x": 40.0, "radius_y": -60.0, "conic_x": -0.5}, "anamorph (Biconic)"),
    "toroid": ({"type": "toroid", "radius": 48.0, "coefficients": [2e-6], "radius_of_rotation": 55.0},
               "Toroid (Rotationsradius 55, 1 Koeff.)"),
    "cylinder": ({"type": "cylinder", "radius": -75.0}, "Zylinder"),
    "odd": ({"type": "odd_asphere", "curvature": 0.02, "conic": -0.5, "coefficients": [0.0, 1e-4, 2e-6]},
            "Odd Asphere (3 Koeff.)"),
    "axicon": ({"type": "axicon", "angle_deg": -5.0}, "Axicon (-5°)"),
    "qcon": ({"type": "qcon", "curvature": 0.015625, "conic": -0.8, "normalization_radius": 12.7,
              "coefficients": [0.0, 0.01]}, "Forbes Q-con (2 Koeff.)"),
    "qbfs": ({"type": "qbfs", "curvature": 0.0166667, "conic": -0.3, "normalization_radius": 12.7,
              "coefficients": [0.0, 0.01]}, "Forbes Q-bfs (2 Koeff.)"),
}


def system_with(base: dict, terms: list | None = None) -> dict:
    shape = {"base": base}
    if terms:
        shape["terms"] = terms
    return {
        "schema_version": "0.11.0", "name": "s", "units": {"length": "mm", "wavelength": "um"},
        "wavelengths": [{"um": 0.5876, "reference": True}], "aperture": {"type": "epd", "value": 10.0},
        "fields": {"type": "angle_deg", "points": [{}]},
        "root": {"type": "assembly", "name": "system", "children": [
            {"type": "stop", "name": "stop",
             "surfaces": [{"id": "STO", "aperture": {"type": "circular", "radius": 5.0}}]},
            {"type": "lens", "name": "L1", "pose": {"position": [0, 0, 5.0]}, "material": "CONST:1.5168", "surfaces": [
                {"id": "L1.S1", "shape": shape, "aperture": {"type": "circular", "radius": 8.0}},
                {"id": "L1.S2", "pose": {"position": [0, 0, 4.0]}, "aperture": {"type": "circular", "radius": 8.0}}]},
            {"type": "detector", "name": "image", "pose": {"position": [0, 0, 90.0]}, "surfaces": [{"id": "IMG"}]}]},
        "paths": [{"name": "main", "events": [{"surface": "STO"}, {"surface": "L1.S1"}, {"surface": "L1.S2"},
                                              {"surface": "IMG"}]}],
    }


@pytest.mark.library
@pytest.mark.parametrize("name", list(CASES))
def test_real_library_shapes_make_table_rows_and_a_layout(tmp_path, name):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import raytatouille as rt

    from rtt_explorer.drawing import draw_geometry_api

    base, form = CASES[name]
    path = tmp_path / "s.rtt.json"
    path.write_text(json.dumps(system_with(base)), encoding="utf-8")
    system = rt.load(path)
    assert surface_rows(system.root)[1]["Form"] == form
    comp = rt.compile(system)
    for plane in ("yz", "xz"):
        fig, ax = plt.subplots()
        draw_geometry_api(ax, comp, plane, {}, 10.0, False)
        plt.close(fig)


@pytest.mark.library
def test_real_library_freeform_terms_are_named(tmp_path):
    import raytatouille as rt

    terms = [{"type": "zernike_fringe_sag", "normalization_radius": 8.0, "coefficients": [0, 0, 0, 1e-4]},
             {"type": "xy_polynomial", "normalization_radius": 8.0, "coefficients": [0, 0, 1e-4]}]
    path = tmp_path / "s.rtt.json"
    path.write_text(json.dumps(system_with({"type": "conic", "radius": 50.0}, terms)), encoding="utf-8")
    form = surface_rows(rt.load(path).root)[1]["Form"]
    assert form == "sphärisch/konisch + 2 Zusatzterme (Zernike-Fringe, XY-Polynom)"
