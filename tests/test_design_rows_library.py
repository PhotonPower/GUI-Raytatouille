"""The builder table made from rt.design reproduces the optics of the library system (needs the library)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from rtt_explorer.builder import BUILDER_COLUMNS, build_system_dict, surface_rows
from rtt_explorer.design_rows import rows_from_system_dict

pytestmark = pytest.mark.library

WL = pd.DataFrame({"um": [0.4861, 0.5876, 0.6563], "weight": [1.0, 1.0, 1.0], "Referenz": [False, True, False]})
FIELDS = pd.DataFrame({"x_deg": [0.0], "y_deg": [0.0], "weight": [1.0]})


def need_design() -> None:
    from rtt_explorer.compat import FEATURES

    if not FEATURES.design:
        pytest.skip("Bibliotheksfunktion fehlt: design")


def first_order(system):
    import raytatouille as rt

    fo = rt.paraxial.first_order(rt.compile(system, rt.MaterialLibrary()))
    return fo.efl, fo.bfl


def through_table(system):
    """The system the builder makes from the rows of the design system."""
    import raytatouille as rt

    rows = rows_from_system_dict(json.loads(system.to_json()))
    table = surface_rows(pd.DataFrame(rows, columns=BUILDER_COLUMNS))
    return rt.System.from_json(json.dumps(build_system_dict("t", 20.0, WL, FIELDS, table)))


COMMON = {"epd": 20.0, "stop_distance": 5.0, "semi_diameter": 12.7}


def cases():
    import raytatouille as rt

    d = rt.design
    return {
        "singlet": d.singlet((100.0, -100.0), 5.0, "CONST:1.5168", image_distance=94.0, **COMMON),
        "plano": d.singlet((51.68, None), 4.0, "CONST:1.5168", image_distance=97.363, **COMMON),
        "doublet": d.doublet((62.0, -44.0, -130.0), (4.0, 2.5), ("CONST:1.5168", "CONST:1.62"),
                             image_distance=96.0, **COMMON),
        "triplet": d.triplet((30.0, -200.0, -40.0, 35.0, 80.0, -30.0), (4.0, 1.5, 4.0), (6.0, 7.0),
                             ("CONST:1.62", "CONST:1.7", "CONST:1.62"), image_distance=50.0, **COMMON),
    }


@pytest.mark.parametrize("kind", ["singlet", "plano", "doublet", "triplet"])
def test_table_system_has_the_focal_length_and_back_focus_of_the_library_system(kind):
    need_design()
    system = cases()[kind]
    efl, bfl = first_order(system)
    efl_table, bfl_table = first_order(through_table(system))
    assert efl_table == pytest.approx(efl, rel=1e-12)
    assert bfl_table == pytest.approx(bfl, rel=1e-12)


def test_catalog_entry_gives_rows_like_its_helper():
    need_design()
    import raytatouille as rt

    text = json.dumps({"format": "raytatouille-lenses", "schema_version": "0.1.0", "catalog": "T", "lenses": [
        {"name": "PCX", "kind": "singlet", "radii": [51.68, None], "thicknesses": [4.0],
         "materials": ["CONST:1.5168"], "diameter": 25.4}]})
    entry = rt.design.parse_lens_catalog(text)["PCX"]
    via_catalog = rt.design.from_catalog(entry, epd=20.0, stop_distance=5.0, image_distance=97.363)
    direct = rt.design.singlet((51.68, None), 4.0, "CONST:1.5168", epd=20.0, stop_distance=5.0,
                               image_distance=97.363, semi_diameter=12.7, name="PCX")
    rows = [rows_from_system_dict(json.loads(s.to_json())) for s in (via_catalog, direct)]
    assert rows[0] == rows[1]
