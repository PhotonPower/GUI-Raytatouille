"""Catalogue parsing and automatic selection (pure Python)."""

from __future__ import annotations

import json

from rtt_explorer.catalogs import (
    agf_names,
    assign_names,
    auto_catalogs,
    auto_coatings,
    coating_info,
    coating_refs,
    material_refs,
)

SYSTEM = {
    "root": {"type": "assembly", "children": [
        {"type": "lens", "material": "SCHOTT:N-BK7", "surfaces": [{"id": "a"}]},
        {"type": "lens", "material": ["SCHOTT:N-BK7", "OHARA:S-LAH58"], "surfaces": [
            {"id": "b", "interaction": {"type": "coating", "name": "demo:AR_MGF2"}}]},
        {"type": "lens", "material": "CONST:1.5", "surfaces": []},
        {"type": "lens", "material": "AIR", "surfaces": []},
    ]},
}

COATING_JSON = json.dumps({"catalog": "demo", "coatings": [{"name": "AR_MGF2"}, {"name": "V_AR"}]}).encode()


class TestAgfNames:
    def test_ansi(self, agf_ansi):
        assert agf_names(agf_ansi) == ["N-BK7", "F2"]

    def test_utf16_with_bom(self, agf_utf16):
        assert agf_names(agf_utf16) == ["N-BK7", "F2"]

    def test_garbage_gives_empty_list(self):
        assert agf_names(b"\xff\xfe\x00") == []
        assert agf_names(b"") == []


class TestReferences:
    def test_material_refs_find_catalogue_glasses_only(self):
        assert material_refs(SYSTEM) == {("SCHOTT", "N-BK7"), ("OHARA", "S-LAH58")}

    def test_coating_refs_uppercase_the_catalogue(self):
        assert coating_refs(SYSTEM) == {("DEMO", "AR_MGF2")}

    def test_system_without_references(self):
        assert material_refs({"root": {}}) == set()
        assert coating_refs({"root": {}}) == set()


class TestCoatingInfo:
    def test_name_is_uppercase_and_coatings_are_collected(self):
        assert coating_info(COATING_JSON) == ("DEMO", {"AR_MGF2", "V_AR"})

    def test_not_a_coating_catalogue(self):
        assert coating_info(b"{}") == ("", set())
        assert coating_info(b"not json") == ("", set())
        assert coating_info(b"\xff\xfe") == ("", set())


class TestAssignNames:
    def test_file_stem_uppercase_and_duplicates_numbered(self):
        candidates = {"schott.agf": ("schott.agf", b""), "m2/schott.agf": ("schott.agf", b""),
                      "Upload: nikon.agf": ("nikon.agf", b"")}
        named = assign_names(["schott.agf", "m2/schott.agf", "Upload: nikon.agf"], candidates)
        assert named == [("schott.agf", "SCHOTT"), ("m2/schott.agf", "SCHOTT_2"),
                         ("Upload: nikon.agf", "NIKON")]


class TestAutoSelection:
    def test_picks_the_file_that_contains_the_glass(self, agf_ansi):
        other = b"NM N-SK16 2 620603.358 1.62 60.3 0 1\r\n"
        candidates = {"a/schott.agf": ("schott.agf", other), "b/schott.agf": ("schott.agf", agf_ansi)}
        assert auto_catalogs({("SCHOTT", "N-BK7")}, candidates) == ["b/schott.agf"]

    def test_one_file_per_catalogue_name(self, agf_ansi):
        candidates = {"a/schott.agf": ("schott.agf", agf_ansi), "b/schott.agf": ("schott.agf", agf_ansi)}
        assert auto_catalogs({("SCHOTT", "N-BK7"), ("SCHOTT", "F2")}, candidates) == ["a/schott.agf"]

    def test_no_match_gives_empty_list(self, agf_ansi):
        assert auto_catalogs({("OHARA", "S-LAH58")}, {"schott.agf": ("schott.agf", agf_ansi)}) == []

    def test_auto_coatings(self):
        cands = {"demo.json": ("demo.json", COATING_JSON)}
        assert auto_coatings({("DEMO", "V_AR")}, cands) == ["demo.json"]
        assert auto_coatings({("DEMO", "UNBEKANNT")}, cands) == []
