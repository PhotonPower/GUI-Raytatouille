"""Surface forms of the builder table (pure logic: no Streamlit, no library)."""

from __future__ import annotations

import pytest

from rtt_explorer.surface_shapes import FORMS, parse_extra, shape_base


def test_forms_start_with_the_plain_conic():
    assert FORMS[0] == "" and "Biconic" in FORMS and "Forbes Q-bfs" in FORMS


def test_parse_extra_reads_numbers_and_lists():
    assert parse_extra("radius_y=-60; conic_y=0.5", "Biconic", 3) == {"radius_y": -60.0, "conic_y": 0.5}
    assert parse_extra("coefficients=1e-4, 2e-6 ; radius_of_rotation=55", "Toroid", 2) == \
        {"coefficients": [1e-4, 2e-6], "radius_of_rotation": 55.0}
    assert parse_extra("", "Zylinder", 2) == {}
    assert parse_extra(None, "Zylinder", 2) == {}
    assert parse_extra(float("nan"), "Zylinder", 2) == {}


@pytest.mark.parametrize("text, message", [
    ("radius_z=3", "Zeile 4: Form Biconic kennt den Schlüssel 'radius_z' nicht (erlaubt: radius_y, conic_y)"),
    ("radius_y", "Zeile 4: 'radius_y' braucht die Form schlüssel=wert"),
    ("radius_y=abc", "Zeile 4: 'radius_y' ist keine Zahl: abc"),
    ("radius_y=1; radius_y=2", "Zeile 4: 'radius_y' steht doppelt"),
    ("radius_y=inf", "Zeile 4: 'radius_y' muss endlich sein"),
])
def test_parse_extra_errors_are_german_and_name_the_row(text, message):
    with pytest.raises(ValueError) as error:
        parse_extra(text, "Biconic", 4)
    assert str(error.value) == message


def test_list_key_must_be_a_list_and_scalar_key_a_number():
    with pytest.raises(ValueError, match="'coefficients' ist keine Zahl: x"):
        parse_extra("coefficients=1,x", "Toroid", 1)
    assert parse_extra("coefficients=2", "Toroid", 1) == {"coefficients": [2.0]}
    with pytest.raises(ValueError, match="'radius_of_rotation' erwartet genau eine Zahl"):
        parse_extra("radius_of_rotation=1,2", "Toroid", 1)


def test_biconic_base():
    assert shape_base("Biconic", 40.0, -0.5, {"radius_y": -60.0}, 1) == \
        {"type": "biconic", "radius_x": 40.0, "radius_y": -60.0, "conic_x": -0.5}
    assert shape_base("Biconic", 40.0, 0.0, {"radius_y": -60.0, "conic_y": 0.2}, 1) == \
        {"type": "biconic", "radius_x": 40.0, "radius_y": -60.0, "conic_y": 0.2}
    with pytest.raises(ValueError, match="Zeile 2: Biconic braucht radius_y"):
        shape_base("Biconic", 40.0, 0.0, {}, 2)
    with pytest.raises(ValueError, match="Zeile 2: Biconic braucht einen Radius ≠ 0"):
        shape_base("Biconic", 0.0, 0.0, {"radius_y": 5.0}, 2)


def test_toroid_and_cylinder_base():
    assert shape_base("Toroid", 48.0, 0.0, {"radius_of_rotation": 55.0, "coefficients": [2e-6]}, 1) == \
        {"type": "toroid", "radius": 48.0, "radius_of_rotation": 55.0, "coefficients": [2e-6]}
    assert shape_base("Zylinder", -75.0, -1.0, {}, 1) == {"type": "cylinder", "radius": -75.0, "conic": -1.0}
    with pytest.raises(ValueError, match="Zeile 1: Toroid braucht radius_of_rotation"):
        shape_base("Toroid", 48.0, 0.0, {}, 1)
    with pytest.raises(ValueError, match="Zeile 1: Zylinder braucht einen Radius ≠ 0"):
        shape_base("Zylinder", 0.0, 0.0, {}, 1)


def test_curvature_forms_use_one_over_radius():
    assert shape_base("Odd Asphere", 50.0, -0.5, {"coefficients": [0.0, 1e-4]}, 1) == \
        {"type": "odd_asphere", "curvature": 0.02, "conic": -0.5, "coefficients": [0.0, 1e-4]}
    assert shape_base("Odd Asphere", 0.0, 0.0, {"coefficients": [1e-3]}, 1)["curvature"] == 0.0
    assert shape_base("Forbes Q-con", 64.0, -0.8, {"normalization_radius": 12.7, "coefficients": [0.01]}, 1) == \
        {"type": "qcon", "curvature": 1 / 64.0, "conic": -0.8, "normalization_radius": 12.7, "coefficients": [0.01]}
    assert shape_base("Forbes Q-bfs", -60.0, 0.0, {"normalization_radius": 10.0}, 1) == \
        {"type": "qbfs", "curvature": -1 / 60.0, "normalization_radius": 10.0, "coefficients": []}
    with pytest.raises(ValueError, match="Zeile 5: Odd Asphere braucht mindestens einen Koeffizienten"):
        shape_base("Odd Asphere", 50.0, 0.0, {}, 5)
    with pytest.raises(ValueError, match="Zeile 5: Forbes Q-con braucht normalization_radius"):
        shape_base("Forbes Q-con", 50.0, 0.0, {}, 5)
    with pytest.raises(ValueError, match="Zeile 5: normalization_radius muss > 0 sein"):
        shape_base("Forbes Q-con", 50.0, 0.0, {"normalization_radius": -1.0}, 5)


def test_axicon_base():
    assert shape_base("Axicon", 0.0, 0.0, {"angle_deg": -5.0}, 1) == {"type": "axicon", "angle_deg": -5.0}
    with pytest.raises(ValueError, match="Zeile 1: Axicon braucht angle_deg"):
        shape_base("Axicon", 0.0, 0.0, {}, 1)
    with pytest.raises(ValueError, match="Zeile 1: Ein Axicon hat keinen Radius und keine Konik"):
        shape_base("Axicon", 10.0, 0.0, {"angle_deg": 5.0}, 1)
    with pytest.raises(ValueError, match="Zeile 1: Der Winkel eines Axicons muss zwischen −90° und 90° liegen"):
        shape_base("Axicon", 0.0, 0.0, {"angle_deg": 90.0}, 1)


def test_variable_radius_and_conic_values_are_passed_through():
    base = shape_base("Biconic", {"param": "R2"}, {"param": "K2"}, {"radius_y": -60.0}, 2)
    assert base["radius_x"] == {"param": "R2"} and base["conic_x"] == {"param": "K2"}
    assert shape_base("Zylinder", {"param": "R2"}, 0.0, {}, 2)["radius"] == {"param": "R2"}
