"""System builder: surface table to .rtt.json (pure Python)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from rtt_explorer.builder import BUILDER_COLUMNS, PRESETS, build_system_dict, is_air, num, surface_rows

WAVELENGTHS = pd.DataFrame({"um": [0.4861, 0.5876, 0.6563], "weight": [1.0, 1.0, 1.0],
                            "Referenz": [False, True, False]})
FIELDS = pd.DataFrame({"x_deg": [0.0, 0.0], "y_deg": [0.0, 5.0], "weight": [1.0, 1.0]})


def build(table: list[list], epd: float = 20.0, wl: pd.DataFrame = WAVELENGTHS,
          fields: pd.DataFrame = FIELDS) -> dict:
    rows = surface_rows(pd.DataFrame(table, columns=BUILDER_COLUMNS))
    return build_system_dict("test", epd, wl, fields, rows)


def lens_children(system: dict) -> list[dict]:
    return [c for c in system["root"]["children"] if c["type"] == "lens"]


class TestHelpers:
    def test_num_defaults_on_garbage_and_nan(self):
        assert num("3.5") == 3.5
        assert num(None, 7.0) == 7.0
        assert num("abc") == 0.0
        assert num(float("nan"), 2.0) == 2.0

    @pytest.mark.parametrize("material", ["", "AIR", "air", " Vacuum ", None])
    def test_air_words(self, material):
        assert is_air(material)

    def test_glass_is_not_air(self):
        assert not is_air("CONST:1.5168")


class TestSurfaceRows:
    def test_z_is_cumulative_sum_of_thicknesses(self):
        rows = surface_rows(pd.DataFrame(PRESETS["Bikonvexes Singlet (n = 1,5168)"],
                                         columns=BUILDER_COLUMNS))
        assert [r["z"] for r in rows] == [0.0, 5.0, 10.0, 104.0]

    def test_unknown_type_is_rejected_with_row_number(self):
        table = [["Blende", 0, 0, 5, "AIR", 10, ""], ["Quatsch", 0, 0, 1, "AIR", 0, ""]]
        with pytest.raises(ValueError, match="Zeile 2: Typ muss"):
            surface_rows(pd.DataFrame(table, columns=BUILDER_COLUMNS))

    def test_non_positive_thickness_is_rejected(self):
        table = [["Blende", 0, 0, 0, "AIR", 10, ""], ["Bild", 0, 0, 0, "AIR", 0, ""]]
        with pytest.raises(ValueError, match="Zeile 1: Dicke muss > 0"):
            surface_rows(pd.DataFrame(table, columns=BUILDER_COLUMNS))

    def test_image_row_needs_no_thickness(self):
        rows = surface_rows(pd.DataFrame([["Bild", 0, 0, None, "AIR", 0, ""]], columns=BUILDER_COLUMNS))
        assert rows[0]["typ"] == "Bild"


class TestPresets:
    @pytest.mark.parametrize("name", list(PRESETS))
    def test_every_preset_builds_valid_json(self, name):
        system = build(PRESETS[name])
        json.dumps(system)  # serialisable
        assert system["schema_version"] == "0.2.0"
        assert system["aperture"] == {"type": "epd", "value": 20.0}
        types = [c["type"] for c in system["root"]["children"]]
        assert types[0] == "stop" and types[-1] == "detector"

    def test_singlet_has_one_lens_with_two_surfaces(self):
        lens, = lens_children(build(PRESETS["Plankonvex-Singlet f ≈ 100 mm (n = 1,5168)"]))
        assert lens["material"] == "CONST:1.5168"
        assert [s["id"] for s in lens["surfaces"]] == ["L1.S1", "L1.S2"]
        assert lens["surfaces"][0]["shape"]["base"] == {"type": "conic", "radius": 51.68}
        assert "shape" not in lens["surfaces"][1]  # radius 0 means plane

    def test_doublet_is_one_cemented_element_with_two_materials(self):
        lens, = lens_children(build(PRESETS["Verkittetes Dublett (nur Demo, nicht optimiert)"]))
        assert lens["material"] == ["CONST:1.5168", "CONST:1.62"]
        assert len(lens["surfaces"]) == 3

    def test_conic_constant_is_written_only_when_nonzero(self):
        asphere = build(PRESETS["Parabolische Asphäre-Demo: Konik −1 (Plankonvex)"])
        base = lens_children(asphere)[0]["surfaces"][0]["shape"]["base"]
        assert base["conic"] == -1.0

    def test_coating_becomes_interaction(self):
        system = build(PRESETS["Singlet mit AR-Coating (braucht Coating-Katalog DEMO)"])
        surface = lens_children(system)[0]["surfaces"][0]
        assert surface["interaction"] == {"type": "coating", "name": "DEMO:AR_MGF2"}

    def test_surface_poses_are_relative_to_the_lens(self):
        lens, = lens_children(build(PRESETS["Bikonvexes Singlet (n = 1,5168)"]))
        assert lens["pose"]["position"] == [0.0, 0.0, 5.0]
        assert "pose" not in lens["surfaces"][0]
        assert lens["surfaces"][1]["pose"]["position"] == [0.0, 0.0, 5.0]


class TestBuildErrors:
    def test_last_row_must_be_the_image(self):
        table = PRESETS["Bikonvexes Singlet (n = 1,5168)"][:-1]
        with pytest.raises(ValueError, match="Bildzeile"):
            build(table)

    def test_stop_is_required(self):
        table = PRESETS["Bikonvexes Singlet (n = 1,5168)"][1:]
        with pytest.raises(ValueError, match="Blendenzeile"):
            build(table)

    def test_only_one_stop(self):
        table = [PRESETS["Bikonvexes Singlet (n = 1,5168)"][0], *PRESETS["Bikonvexes Singlet (n = 1,5168)"]]
        with pytest.raises(ValueError, match="höchstens eine Blende"):
            build(table)

    def test_epd_must_be_positive(self):
        with pytest.raises(ValueError, match="Eintrittspupillendurchmesser"):
            build(PRESETS["Bikonvexes Singlet (n = 1,5168)"], epd=0.0)

    def test_exactly_one_reference_wavelength(self):
        wl = WAVELENGTHS.assign(Referenz=[True, True, False])
        with pytest.raises(ValueError, match="Genau eine Wellenlänge"):
            build(PRESETS["Bikonvexes Singlet (n = 1,5168)"], wl=wl)

    def test_air_to_air_surface_explains_where_the_glass_goes(self):
        table = [["Blende", 0, 0, 5, "AIR", 10, ""], ["Fläche", 50, 0, 4, "AIR", 12, ""],
                 ["Bild", 0, 0, 0, "AIR", 0, ""]]
        with pytest.raises(ValueError, match="Luft und Luft"):
            build(table)

    def test_glass_must_end_on_a_surface(self):
        table = [["Blende", 0, 0, 5, "AIR", 10, ""], ["Fläche", 50, 0, 4, "CONST:1.5", 12, ""],
                 ["Bild", 0, 0, 0, "AIR", 0, ""]]
        with pytest.raises(ValueError, match="Das Glas muss auf einer Fläche enden"):
            build(table)

    def test_stop_directly_behind_glass_is_reported_as_unfinished_lens(self):
        table = [["Fläche", 50, 0, 4, "CONST:1.5", 12, ""], ["Blende", 0, 0, 4, "AIR", 10, ""],
                 ["Fläche", -50, 0, 90, "AIR", 12, ""], ["Bild", 0, 0, 0, "AIR", 0, ""]]
        with pytest.raises(ValueError, match="Das Glas muss auf einer Fläche enden"):
            build(table)

    def test_coating_needs_catalogue_prefix(self):
        table = [["Blende", 0, 0, 5, "AIR", 10, ""], ["Fläche", 50, 0, 4, "CONST:1.5", 12, "AR"],
                 ["Fläche", 0, 0, 90, "AIR", 12, ""], ["Bild", 0, 0, 0, "AIR", 0, ""]]
        with pytest.raises(ValueError, match="KATALOG:NAME"):
            build(table)
