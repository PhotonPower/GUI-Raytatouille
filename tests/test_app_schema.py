"""View System-Datei: schema downloads and the check against the JSON schema (needs the library)."""

from __future__ import annotations

import pytest

from test_app import start
from test_app_library_06 import need, ok, view

pytestmark = pytest.mark.library


def test_schema_downloads_are_offered(rtt_repo, monkeypatch):
    need("schemas")
    at = view(start(rtt_repo, monkeypatch), "System-Datei")
    ok(at)
    assert any(e.label == "JSON-Schema des Dateiformats" for e in at.expander)


def test_valid_file_matches_the_schema(rtt_repo, monkeypatch):
    need("schemas")
    pytest.importorskip("jsonschema")
    at = view(start(rtt_repo, monkeypatch), "System-Datei")
    at = next(b for b in at.button if b.key == "schema_check").click().run()
    ok(at)
    assert any("entspricht dem Schema" in s.value for s in at.success)


def test_missing_jsonschema_package_is_explained(rtt_repo, monkeypatch):
    import sys

    need("schemas")
    monkeypatch.setitem(sys.modules, "jsonschema", None)  # makes the import raise ImportError
    at = view(start(rtt_repo, monkeypatch), "System-Datei")
    at = next(b for b in at.button if b.key == "schema_check").click().run()
    assert not at.exception
    assert any("pip install jsonschema" in i.value for i in at.info)
