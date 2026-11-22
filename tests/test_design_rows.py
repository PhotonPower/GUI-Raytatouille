"""Design helper -> builder table (pure logic; the system dicts mimic what rt.design builds)."""

from __future__ import annotations

import pytest

from rtt_explorer.design_rows import parse_materials, parse_numbers, radii_for_library, rows_from_system_dict


def lens(name, z, material, surfaces):
    node = {"type": "lens", "name": name, "material": material, "surfaces": surfaces}
    if z:
        node["pose"] = {"position": [0.0, 0.0, z]}
    return node


def surface(sid, radius, z=0.0, sd=None):
    s = {"id": sid}
    if z:
        s["pose"] = {"position": [0.0, 0.0, z]}
    if radius is not None:
        s["shape"] = {"base": {"type": "conic", "radius": radius}}
    if sd is not None:
        s["aperture"] = {"type": "circular", "radius": sd}
    return s


def system(children, stop=None):
    data = {"aperture": {"type": "epd", "value": 20.0}, "root": {"type": "assembly", "children": children}}
    if stop:
        data["aperture"]["stop"] = {"surface": stop}
    return data


STOP = {"type": "stop", "name": "stop", "surfaces": [{"id": "STO", "aperture": {"type": "circular", "radius": 10.0}}]}
IMAGE = {"type": "detector", "name": "image", "pose": {"position": [0.0, 0.0, 110.5]}, "surfaces": [{"id": "IMG"}]}


def test_cemented_doublet_gives_one_glass_per_segment_and_air_after_the_last_surface():
    data = system([
        STOP,
        lens("L1", 5.0, ["CONST:1.5168", "CONST:1.62"],
             [surface("L1.S1", 62.0, sd=12.7), surface("L1.S2", -44.0, 4.0, 12.7),
              surface("L1.S3", -130.0, 6.5, 12.7)]),
        IMAGE,
    ])
    rows = rows_from_system_dict(data)
    assert [r[0] for r in rows] == ["Blende", "Fläche", "Fläche", "Fläche", "Bild"]
    assert [r[1] for r in rows] == [0.0, 62.0, -44.0, -130.0, 0.0]
    assert [r[3] for r in rows[:4]] == [5.0, 4.0, 2.5, 99.0]  # stop->L1, 4.0, 2.5, last vertex 5+6.5=11.5 -> 110.5
    assert [r[4] for r in rows] == ["AIR", "CONST:1.5168", "CONST:1.62", "AIR", "AIR"]
    assert [r[5] for r in rows] == [10.0, 12.7, 12.7, 12.7, 0.0]


def test_singlet_with_a_plano_surface_has_radius_zero():
    data = system([STOP, lens("L1", 5.0, "CONST:1.5", [surface("L1.S1", 51.68), surface("L1.S2", None, 4.0)]), IMAGE])
    rows = rows_from_system_dict(data)
    assert rows[2][1] == 0.0
    assert rows[1][4] == "CONST:1.5" and rows[2][4] == "AIR"
    assert rows[1][5] == 0.0  # no aperture: free


def test_triplet_gaps_become_the_thickness_after_the_rear_surface():
    data = system([
        STOP,
        lens("L1", 5.0, "CONST:1.5", [surface("L1.S1", 20.0), surface("L1.S2", -50.0, 3.0)]),
        lens("L2", 12.0, "CONST:1.6", [surface("L2.S1", -30.0), surface("L2.S2", 25.0, 1.0)]),
        lens("L3", 20.0, "CONST:1.5", [surface("L3.S1", 90.0), surface("L3.S2", -20.0, 3.0)]),
        IMAGE,
    ])
    rows = rows_from_system_dict(data)
    # L1 rear vertex at 8, L2 front at 12: gap 4; L2 rear at 13, L3 front at 20: gap 7; L3 rear at 23 -> image 110.5
    assert [r[3] for r in rows[:-1]] == pytest.approx([5.0, 3.0, 4.0, 1.0, 7.0, 3.0, 87.5])
    assert [r[4] for r in rows] == ["AIR", "CONST:1.5", "AIR", "CONST:1.6", "AIR", "CONST:1.5", "AIR", "AIR"]


def test_a_stop_on_a_surface_is_not_supported_in_the_table():
    data = system([lens("L1", 0.0, "CONST:1.5", [surface("L1.S1", 20.0, sd=5.0), surface("L1.S2", -50.0, 3.0)]), IMAGE],
                  stop="L1.S1")
    with pytest.raises(ValueError, match="Blende"):
        rows_from_system_dict(data)


def test_rows_fit_the_builder_columns():
    from rtt_explorer.builder import BUILDER_COLUMNS

    data = system([STOP, lens("L1", 5.0, "CONST:1.5", [surface("L1.S1", 20.0), surface("L1.S2", -50.0, 3.0)]), IMAGE])
    assert all(len(r) == len(BUILDER_COLUMNS) for r in rows_from_system_dict(data))


def test_parse_numbers_accepts_comma_semicolon_and_blanks_with_a_decimal_point():
    assert parse_numbers("62, -44; -130", 3, "Radien") == [62.0, -44.0, -130.0]
    assert parse_numbers("4.5 2.5", 2, "Dicken") == [4.5, 2.5]
    assert parse_numbers("4,5", 2, "Dicken") == [4.0, 5.0]  # a comma separates values, it is no decimal comma


def test_parse_numbers_reports_count_and_garbage_in_german():
    with pytest.raises(ValueError, match="Radien: 3 Werte erwartet, 2 gefunden"):
        parse_numbers("1, 2", 3, "Radien")
    with pytest.raises(ValueError, match="Radien: „abc“ ist keine Zahl"):
        parse_numbers("1, abc", 2, "Radien")


def test_parse_materials_splits_on_comma_and_semicolon_and_counts():
    assert parse_materials("SCHOTT:N-BK7, CONST:1.62", 2, "Gläser") == ["SCHOTT:N-BK7", "CONST:1.62"]
    with pytest.raises(ValueError, match="Gläser: 2 Werte erwartet, 1 gefunden"):
        parse_materials("SCHOTT:N-BK7", 2, "Gläser")


def test_radii_for_library_turns_zero_into_plano():
    assert radii_for_library([51.68, 0.0]) == [51.68, None]
