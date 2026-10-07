"""The app explains what to do when ``raytatouille`` is not installed (needs no library)."""

from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

import rtt_explorer

SCRIPT = str(Path(rtt_explorer.__file__).with_name("streamlit_app.py"))


def test_missing_library_shows_install_hint_and_stops(monkeypatch):
    monkeypatch.setitem(sys.modules, "raytatouille", None)  # makes "import raytatouille" fail
    at = AppTest.from_file(SCRIPT, default_timeout=60).run()
    assert not at.exception
    assert len(at.error) == 1
    assert "raytatouille" in at.error[0].value
    assert "docs/installation.md" in at.error[0].value
    assert not at.metric  # nothing else was rendered
