"""Check of a system file against the JSON schema of the library (needs ``jsonschema``, else skipped)."""

from __future__ import annotations

import pytest

from rtt_explorer.schema_check import MAX_ROWS, pointer, schema_rows

jsonschema = pytest.importorskip("jsonschema")

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
    "required": ["name", "wavelengths"],
    "properties": {
        "name": {"type": "string"},
        "wavelengths": {"type": "array", "items": {"type": "object", "required": ["um"],
                                                    "properties": {"um": {"type": "number"}}}},
    },
}


def test_pointer_of_a_path():
    assert pointer([]) == "/"
    assert pointer(["root", "children", 1, "id"]) == "/root/children/1/id"


def test_valid_document_has_no_rows():
    assert schema_rows(SCHEMA, {"name": "s", "wavelengths": [{"um": 0.5}]}) == []


def test_errors_name_the_pointer_and_are_sorted():
    rows = schema_rows(SCHEMA, {"wavelengths": [{"um": "x"}, {}]})
    assert [r["Stelle"] for r in rows] == ["/", "/wavelengths/0/um", "/wavelengths/1"]
    assert "name" in rows[0]["Meldung"]
    assert "'x'" in rows[1]["Meldung"]


def test_rows_are_limited():
    document = {"name": "s", "wavelengths": [{"um": "x"}] * (MAX_ROWS + 20)}
    assert len(schema_rows(SCHEMA, document)) == MAX_ROWS


@pytest.mark.library
def test_reference_files_of_the_library_pass_their_own_schema(rtt_repo):
    import json

    import raytatouille as rt

    schema = rt.schema("system")
    for name in ("m2/cooke_triplet.rtt.json", "m8/xy_mirror.rtt.json", "r3/object_reference.rtt.json",
                 "m7/achromat_tolerances.rtt.json"):
        document = json.loads((rtt_repo / "tests" / "reference" / name).read_text(encoding="utf-8"))
        assert schema_rows(schema, document) == [], name


@pytest.mark.library
def test_broken_system_is_found_with_its_location(rtt_repo):
    import json

    import raytatouille as rt

    document = json.loads((rtt_repo / "tests" / "reference" / "m2" / "cooke_triplet.rtt.json")
                          .read_text(encoding="utf-8"))
    document["wavelengths"][0]["um"] = "rot"
    rows = schema_rows(rt.schema("system"), document)
    assert any(r["Stelle"] == "/wavelengths/0/um" for r in rows)
