"""Builder table with the surface forms of library 0.10 (column Form and Form_Parameter)."""

from __future__ import annotations

import pandas as pd
import pytest

from rtt_explorer.builder import (
    BUILDER_COLUMNS,
    PRESETS,
    SHAPE_COLUMNS,
    VARIABLE_COLUMNS,
    build_system_dict,
    surface_rows,
)

WAVELENGTHS = pd.DataFrame({"um": [0.5876], "weight": [1.0], "Referenz": [True]})
FIELDS = pd.DataFrame({"x_deg": [0.0], "y_deg": [0.0], "weight": [1.0]})


def singlet(form="", extra="", radius=51.68, conic=0.0, variables=(False, False, False), second=None):
    """Stop, L1.S1 with the given form, plane L1.S2, image."""
    rows = [["Blende", 0.0, 0.0, 5.0, "AIR", 10.0, ""],
            ["Fläche", radius, conic, 4.0, "CONST:1.5168", 12.7, ""],
            ["Fläche", 0.0, 0.0, 90.0, "AIR", 12.7, ""],
            ["Bild", 0.0, 0.0, 0.0, "AIR", 0.0, ""]]
    df = pd.DataFrame(rows, columns=BUILDER_COLUMNS)
    for col in VARIABLE_COLUMNS:
        df[col] = False
    df.loc[1, VARIABLE_COLUMNS] = list(variables)
    df["Form"] = ""
    df["Form_Parameter"] = ""
    df.loc[1, "Form"], df.loc[1, "Form_Parameter"] = form, extra
    if second:
        df.loc[2, "Form"], df.loc[2, "Form_Parameter"] = second
    return df


def build(df):
    return build_system_dict("test", 20.0, WAVELENGTHS, FIELDS, surface_rows(df))


def first_base(system):
    return system["root"]["children"][1]["surfaces"][0]["shape"]["base"]


def test_shape_columns_are_optional_extras():
    assert SHAPE_COLUMNS == ["Form", "Form_Parameter"]
    assert not set(SHAPE_COLUMNS) & set(BUILDER_COLUMNS)
    plain = pd.DataFrame(PRESETS["Bikonvexes Singlet (n = 1,5168)"], columns=BUILDER_COLUMNS)
    system = build_system_dict("t", 20.0, WAVELENGTHS, FIELDS, surface_rows(plain))
    assert first_base(system)["type"] == "conic"
    assert system["schema_version"] == "0.2.0"


def test_plain_conic_is_unchanged_with_empty_form():
    system = build(singlet())
    assert first_base(system) == {"type": "conic", "radius": 51.68}
    assert system["schema_version"] == "0.2.0"


@pytest.mark.parametrize("form, extra, radius, conic, expected", [
    ("Biconic", "radius_y=-60", 40.0, -0.5,
     {"type": "biconic", "radius_x": 40.0, "radius_y": -60.0, "conic_x": -0.5}),
    ("Toroid", "radius_of_rotation=55; coefficients=2e-6", 48.0, 0.0,
     {"type": "toroid", "radius": 48.0, "radius_of_rotation": 55.0, "coefficients": [2e-6]}),
    ("Zylinder", "", -75.0, 0.0, {"type": "cylinder", "radius": -75.0}),
    ("Odd Asphere", "coefficients=0, 1e-4", 50.0, 0.0,
     {"type": "odd_asphere", "curvature": 0.02, "coefficients": [0.0, 1e-4]}),
    ("Axicon", "angle_deg=-5", 0.0, 0.0, {"type": "axicon", "angle_deg": -5.0}),
    ("Forbes Q-con", "normalization_radius=12.7; coefficients=0.01", 64.0, -0.8,
     {"type": "qcon", "curvature": 1 / 64.0, "conic": -0.8, "normalization_radius": 12.7, "coefficients": [0.01]}),
])
def test_form_writes_its_base_and_raises_the_schema_version(form, extra, radius, conic, expected):
    system = build(singlet(form, extra, radius, conic))
    assert first_base(system) == expected
    assert system["schema_version"] == "0.9.0"


def test_variable_radius_and_conic_of_a_biconic_become_parameter_rows():
    system = build(singlet("Biconic", "radius_y=-60", 40.0, -0.5, variables=(True, True, False)))
    base = first_base(system)
    assert base["radius_x"] == {"param": "R2"} and base["conic_x"] == {"param": "K2"}
    assert {r["name"] for r in system["parameters"]} == {"R2", "K2"}


def test_variable_radius_of_a_curvature_form_is_refused():
    with pytest.raises(ValueError, match="Zeile 2: Odd Asphere trägt eine Krümmung"):
        build(singlet("Odd Asphere", "coefficients=1e-4", 50.0, variables=(True, False, False)))


def test_variable_conic_of_a_curvature_form_is_allowed():
    system = build(singlet("Odd Asphere", "coefficients=1e-4", 50.0, -0.5, variables=(False, True, False)))
    assert first_base(system)["conic"] == {"param": "K2"}


def test_axicon_cannot_be_a_variable_row():
    with pytest.raises(ValueError, match="Zeile 2: Ein Axicon hat keinen Radius und keine Konik"):
        build(singlet("Axicon", "angle_deg=5", 0.0, variables=(True, False, False)).assign(
            Radius_mm=[0.0, 5.0, 0.0, 0.0]))


def test_two_forms_in_one_lens():
    system = build(singlet("Zylinder", "", 50.0, second=("Zylinder", "")).assign(
        Radius_mm=[0.0, 50.0, -50.0, 0.0]))
    surfaces = system["root"]["children"][1]["surfaces"]
    assert [s["shape"]["base"]["type"] for s in surfaces] == ["cylinder", "cylinder"]


def test_unknown_form_and_form_on_a_stop_row_are_refused():
    with pytest.raises(ValueError, match="Zeile 2: Form muss"):
        surface_rows(singlet("Spline"))
    df = singlet()
    df.loc[0, "Form"] = "Biconic"
    with pytest.raises(ValueError, match="Zeile 1: Die Form gilt nur für Zeilen vom Typ Fläche"):
        surface_rows(df)


def test_missing_form_columns_mean_a_plain_conic():
    df = singlet().drop(columns=SHAPE_COLUMNS)
    assert first_base(build(df)) == {"type": "conic", "radius": 51.68}


@pytest.mark.library
@pytest.mark.parametrize("form, extra", [
    ("Biconic", "radius_y=-60"), ("Toroid", "radius_of_rotation=55"), ("Zylinder", ""),
    ("Odd Asphere", "coefficients=0, 1e-6"), ("Forbes Q-con", "normalization_radius=12.7; coefficients=0.01"),
    ("Forbes Q-bfs", "normalization_radius=12.7"),
])
def test_library_reads_and_compiles_every_form(tmp_path, form, extra):
    import json

    import raytatouille as rt

    radius = 48.0
    path = tmp_path / "s.rtt.json"
    path.write_text(json.dumps(build(singlet(form, extra, radius))), encoding="utf-8")
    comp = rt.compile(rt.load(path))
    assert "L1.S1" in comp.surface_ids


@pytest.mark.library
def test_odd_asphere_with_a_zero_term_equals_the_plain_conic(tmp_path):
    """curvature = 1/R with A2 = 0 is the sphere again: same effective focal length as the plain row."""
    import json

    import raytatouille as rt

    efl = {}
    for name, df in {"plain": singlet(radius=51.68, conic=-0.5),
                     "odd": singlet("Odd Asphere", "coefficients=0, 0", 51.68, -0.5)}.items():
        path = tmp_path / f"{name}.rtt.json"
        path.write_text(json.dumps(build(df)), encoding="utf-8")
        efl[name] = rt.paraxial.first_order(rt.compile(rt.load(path)), path="main").efl
    assert efl["odd"] == pytest.approx(efl["plain"], rel=1e-12)


@pytest.mark.library
def test_biconic_sections_match_the_library_file(tmp_path):
    import json

    import raytatouille as rt

    path = tmp_path / "s.rtt.json"
    path.write_text(json.dumps(build(singlet("Biconic", "radius_y=-60", 40.0, -0.5))), encoding="utf-8")
    comp = rt.compile(rt.load(path))
    fx = rt.paraxial.first_order_section(comp, path="main", section=rt.paraxial.Section.X)
    fy = rt.paraxial.first_order_section(comp, path="main", section=rt.paraxial.Section.Y)
    # thick plano lens: the x section has radius 40, the y section radius -60 (thin lens estimate)
    assert fx.efl > 0 > fy.efl
