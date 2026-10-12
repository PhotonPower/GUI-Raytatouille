"""Builder: variables and merit function for the optimization (pure Python)."""

from __future__ import annotations

import pandas as pd
import pytest

from rtt_explorer.builder import (
    BUILDER_COLUMNS,
    MERIT_COLUMNS,
    MERIT_OPERANDS,
    PRESETS,
    VARIABLE_COLUMNS,
    build_system_dict,
    surface_rows,
    table_updates,
)

WAVELENGTHS = pd.DataFrame({"um": [0.5876], "weight": [1.0], "Referenz": [True]})
FIELDS = pd.DataFrame({"x_deg": [0.0, 0.0], "y_deg": [0.0, 5.0], "weight": [1.0, 1.0]})
SINGLET = PRESETS["Plankonvex-Singlet f ≈ 100 mm (n = 1,5168)"]  # stop, L1.S1 (R 51.68), L1.S2 (plane), image


def table(rows: list[list], variables: dict[int, tuple[bool, bool, bool]] | None = None) -> pd.DataFrame:
    """Builder table; ``variables`` maps a row index to (R var, k var, d var)."""
    df = pd.DataFrame(rows, columns=BUILDER_COLUMNS)
    for col in VARIABLE_COLUMNS:
        df[col] = False
    for i, flags in (variables or {}).items():
        df.loc[i, VARIABLE_COLUMNS] = list(flags)
    return df


def merit(*rows) -> pd.DataFrame:
    return pd.DataFrame(list(rows), columns=MERIT_COLUMNS)


def build(df: pd.DataFrame, merit_df: pd.DataFrame | None = None) -> dict:
    return build_system_dict("test", 20.0, WAVELENGTHS, FIELDS, surface_rows(df), merit_df)


def params(system: dict) -> dict[str, dict]:
    return {p["name"]: p for p in system.get("parameters", [])}


def children(system: dict) -> dict[str, dict]:
    return {c["name"]: c for c in system["root"]["children"]}


def test_without_variables_and_merit_the_output_stays_schema_0_2():
    system = build(table(SINGLET), merit())
    assert system["schema_version"] == "0.2.0"
    assert "parameters" not in system and "optimization" not in system


def test_variable_radius_becomes_a_bound_parameter_row():
    system = build(table(SINGLET, {1: (True, False, False)}))
    assert system["schema_version"] == "0.4.0"
    assert params(system)["R2"] == {"name": "R2", "value": 51.68, "variable": True}
    s1 = children(system)["L1"]["surfaces"][0]
    assert s1["shape"]["base"]["radius"] == {"param": "R2"}


def test_variable_conic_is_written_even_when_zero():
    system = build(table(SINGLET, {1: (False, True, False)}))
    assert params(system)["K2"] == {"name": "K2", "value": 0.0, "variable": True}
    assert children(system)["L1"]["surfaces"][0]["shape"]["base"]["conic"] == {"param": "K2"}


def test_plane_surface_cannot_have_a_variable_radius():
    with pytest.raises(ValueError, match="Zeile 3: Eine plane Fläche"):
        build(table(SINGLET, {2: (True, False, False)}))


def test_variable_thickness_moves_everything_behind_it():
    # row 3 (L1.S2) has thickness 97.363 to the image: the image position becomes 5 + 4 + D3
    system = build(table(SINGLET, {2: (False, False, True)}))
    p = params(system)
    assert p["D3"] == {"name": "D3", "value": 97.363, "variable": True, "min": 0.01}
    image_z = children(system)["image"]["pose"]["position"][2]
    assert image_z == {"param": "Z4"}
    assert p["Z4"] == {"name": "Z4", "expression": "5.0 + 4.0 + D3"}
    names = [q["name"] for q in system["parameters"]]
    assert names.index("D3") < names.index("Z4")  # expressions only use rows above them
    # positions not depending on a variable stay plain numbers
    assert children(system)["L1"]["pose"]["position"][2] == 5.0


def test_variable_lens_thickness_is_relative_to_the_lens():
    system = build(table(SINGLET, {1: (False, False, True)}))
    s2 = children(system)["L1"]["surfaces"][1]
    assert s2["pose"]["position"][2] == {"param": "Z3REL"}
    assert params(system)["Z3REL"] == {"name": "Z3REL", "expression": "D2"}
    assert params(system)["Z4"]["expression"] == "5.0 + D2 + 97.363"


def test_merit_rows_become_operands_and_generators():
    system = build(table(SINGLET, {1: (True, False, False)}),
                   merit(["EFL", 80.0, 1.0], ["Randstrahl im Fokus", None, 2.0], ["RMS-Spot", None, 1.0],
                         ["", None, None]))
    assert system["optimization"] == {
        "operands": [{"type": "efl", "path": "main", "target": 80.0},
                     {"type": "ray_y", "path": "main", "surface": "IMG", "py": 1.0, "target": 0.0, "weight": 2.0}],
        "generators": [{"type": "rms_spot", "path": "main"}],
    }


def test_operand_without_target_is_rejected():
    with pytest.raises(ValueError, match="Merit-Funktion Zeile 1: EFL braucht einen Zielwert"):
        build(table(SINGLET, {1: (True, False, False)}), merit(["EFL", None, 1.0]))


def test_every_merit_operand_is_known():
    assert set(MERIT_OPERANDS) >= {"EFL", "BFL", "Blendenzahl bildseitig", "Randstrahl im Fokus", "RMS-Spot",
                                   "RMS-Wellenfront"}


def test_table_updates_map_row_names_back_to_cells():
    updates = table_updates([("R2", 41.3), ("D3", 85.0), ("K2", -0.5), ("TOTAL", 1.0), ("", 3.0)])
    assert updates == [(1, "Radius_mm", 41.3), (2, "Dicke_mm", 85.0), (1, "Konik", -0.5)]
