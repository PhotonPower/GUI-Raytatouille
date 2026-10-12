"""Builder rows of type Ideallinse (pure logic): thin element with an ideal lens, schema 0.5.0."""

from __future__ import annotations

import pandas as pd
import pytest

from rtt_explorer.builder import BUILDER_COLUMNS, build_system_dict, surface_rows, table_updates

WL = pd.DataFrame({"um": [0.5876], "weight": [1.0], "Referenz": [True]})
FIELDS = pd.DataFrame({"x_deg": [0.0], "y_deg": [0.0], "weight": [1.0]})


def table(*rows, variables=None):
    df = pd.DataFrame(list(rows), columns=BUILDER_COLUMNS)
    for col, values in (variables or {}).items():
        df[col] = values
    return df


def build(df, merit=None):
    return build_system_dict("test", 10.0, WL, FIELDS, surface_rows(df), merit)


STOP = ["Blende", 0.0, 0.0, 1.0, "AIR", 5.0, ""]
IMAGE = ["Bild", 0.0, 0.0, 0.0, "AIR", 0.0, ""]


def test_ideal_lens_becomes_a_thin_element_with_schema_050():
    system = build(table(STOP, ["Ideallinse", 50.0, 0.0, 50.0, "AIR", 6.0, ""], IMAGE))
    assert system["schema_version"] == "0.5.0"
    stop, lens, image = system["root"]["children"]
    assert lens == {"type": "thin_element", "name": "IL1", "pose": {"position": [0.0, 0.0, 1.0]},
                    "surfaces": [{"id": "IL1", "aperture": {"type": "circular", "radius": 6.0},
                                  "interaction": {"type": "ideal_lens", "focal_length": 50.0}}]}
    assert image["pose"] == {"position": [0.0, 0.0, 51.0]}


def test_ideal_lens_without_aperture_and_negative_focal_length():
    system = build(table(STOP, ["Ideallinse", -25.0, 0.0, 10.0, "AIR", 0.0, ""], IMAGE))
    surface = system["root"]["children"][1]["surfaces"][0]
    assert "aperture" not in surface
    assert surface["interaction"]["focal_length"] == -25.0


def test_ideal_lenses_are_numbered_apart_from_glass_lenses():
    system = build(table(STOP, ["Ideallinse", 100.0, 0.0, 5.0, "AIR", 0.0, ""],
                         ["Fläche", 50.0, 0.0, 4.0, "CONST:1.5", 6.0, ""],
                         ["Fläche", 0.0, 0.0, 5.0, "AIR", 6.0, ""],
                         ["Ideallinse", 80.0, 0.0, 40.0, "AIR", 0.0, ""], IMAGE))
    names = [c["name"] for c in system["root"]["children"]]
    assert names == ["stop", "IL1", "L1", "IL2", "image"]


def test_variable_focal_length_uses_the_radius_column():
    df = table(STOP, ["Ideallinse", 50.0, 0.0, 50.0, "AIR", 0.0, ""], IMAGE,
               variables={"R_var": [False, True, False], "K_var": False, "D_var": False})
    system = build(df)
    assert system["schema_version"] == "0.5.0"
    assert system["root"]["children"][1]["surfaces"][0]["interaction"]["focal_length"] == {"param": "R2"}
    assert system["parameters"] == [{"name": "R2", "value": 50.0, "variable": True}]
    assert table_updates([("R2", 48.0)]) == [(1, "Radius_mm", 48.0)]  # written back into the radius column


@pytest.mark.parametrize(("row", "message"), [
    (["Ideallinse", 0.0, 0.0, 50.0, "AIR", 0.0, ""], "Brennweite"),
    (["Ideallinse", 50.0, 0.0, 50.0, "CONST:1.5", 0.0, ""], "Luft"),
    (["Ideallinse", 50.0, -1.0, 50.0, "AIR", 0.0, ""], "Konik"),
    (["Ideallinse", 50.0, 0.0, 50.0, "AIR", 0.0, "DEMO:AR"], "Coating"),
])
def test_invalid_ideal_lens_rows_give_german_errors(row, message):
    with pytest.raises(ValueError, match=message):
        build(table(STOP, row, IMAGE))


def test_conic_variable_on_an_ideal_lens_is_an_error():
    df = table(STOP, ["Ideallinse", 50.0, 0.0, 50.0, "AIR", 0.0, ""], IMAGE,
               variables={"R_var": False, "K_var": [False, True, False], "D_var": False})
    with pytest.raises(ValueError, match="Konik"):
        build(df)
