"""Switching components on and off through the ``active`` flag (pure logic: dictionaries only)."""

from __future__ import annotations

import copy

import pytest

from rtt_explorer.active_nodes import node_rows, with_active

SYSTEM = {
    "schema_version": "0.11.0", "name": "s",
    "root": {"type": "assembly", "name": "system", "children": [
        {"type": "stop", "name": "stop", "surfaces": [{"id": "STO"}]},
        {"type": "assembly", "name": "relay", "children": [
            {"type": "lens", "name": "L1", "surfaces": [{"id": "L1.S1"}]},
            {"type": "plate", "name": "Filter", "active": False, "surfaces": [{"id": "F.S1"}]}]},
        {"type": "detector", "name": "image", "surfaces": [{"id": "IMG"}]}]},
}


def test_node_rows_walk_the_tree_without_the_root():
    rows = node_rows(SYSTEM)
    assert [(r["pointer"], r["name"], r["kind"], r["depth"], r["active"]) for r in rows] == [
        ("/root/children/0", "stop", "Blende", 0, True),
        ("/root/children/1", "relay", "Baugruppe", 0, True),
        ("/root/children/1/children/0", "L1", "Linse", 1, True),
        ("/root/children/1/children/1", "Filter", "Platte", 1, False),
        ("/root/children/2", "image", "Detektor", 0, True),
    ]


def test_rows_know_whether_a_parent_switches_them_off():
    data = copy.deepcopy(SYSTEM)
    data["root"]["children"][1]["active"] = False
    rows = {r["name"]: r for r in node_rows(data)}
    assert rows["relay"]["by_parent"] is False
    assert rows["L1"]["by_parent"] is True and rows["L1"]["active"] is True
    assert rows["stop"]["by_parent"] is False


def test_unknown_element_kind_is_shown_as_it_is():
    data = {"root": {"children": [{"type": "freeform_thing", "name": "X"}]}}
    assert node_rows(data)[0]["kind"] == "freeform_thing"
    assert node_rows({"root": {}}) == []
    assert node_rows({}) == []


def test_with_active_writes_false_only_and_keeps_the_input():
    before = copy.deepcopy(SYSTEM)
    out = with_active(SYSTEM, {"/root/children/0": False, "/root/children/1/children/1": True})
    assert SYSTEM == before
    assert out["root"]["children"][0]["active"] is False
    assert "active" not in out["root"]["children"][1]["children"][1]  # back to the default: key removed
    assert "active" not in out["root"]["children"][2]


def test_with_active_without_changes_returns_an_equal_dictionary():
    assert with_active(SYSTEM, {}) == SYSTEM
    assert with_active(SYSTEM, {"/root/children/2": True}) == SYSTEM


@pytest.mark.parametrize("version, expected", [("0.2.0", "0.10.0"), ("0.9.0", "0.10.0"), ("0.10.0", "0.10.0"),
                                              ("0.11.0", "0.11.0")])
def test_switching_off_raises_an_old_schema_version(version, expected):
    data = copy.deepcopy(SYSTEM)
    data["schema_version"] = version
    del data["root"]["children"][1]["children"][1]["active"]
    assert with_active(data, {"/root/children/0": False})["schema_version"] == expected


def test_version_is_kept_when_nothing_is_switched_off():
    data = copy.deepcopy(SYSTEM)
    data["schema_version"] = "0.2.0"
    del data["root"]["children"][1]["children"][1]["active"]
    assert with_active(data, {"/root/children/0": True})["schema_version"] == "0.2.0"


def test_root_and_bad_pointers_are_refused():
    with pytest.raises(ValueError, match="Wurzel"):
        with_active(SYSTEM, {"/root": False})
    with pytest.raises(ValueError, match="/root/children/9"):
        with_active(SYSTEM, {"/root/children/9": False})
