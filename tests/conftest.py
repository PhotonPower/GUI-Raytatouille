"""Shared fixtures. Tests marked ``library`` need ``raytatouille`` and a Raytatouille checkout."""

from __future__ import annotations

from pathlib import Path

import pytest

from rtt_explorer.repo import find_repo


def pytest_collection_modifyitems(config, items):
    """Skip ``library`` tests when the package or the repo with reference systems is missing."""
    reason = None
    try:
        import raytatouille  # noqa: F401
    except ImportError:
        reason = "raytatouille ist nicht installiert"
    else:
        if not find_repo():
            reason = "kein Raytatouille-Repo gefunden (Umgebungsvariable RTT_REPO setzen)"
    if reason is None:
        return
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if "library" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def rtt_repo() -> Path:
    return Path(find_repo())


@pytest.fixture
def agf_ansi() -> bytes:
    return (
        b"CC test catalogue\r\n"
        b"NM N-BK7 2 517642.251 1.5168 64.17 0 1\r\n"
        b"ED 7.1 8.3 2.51 -0.0009 0\r\n"
        b"NM F2 2 620364.360 1.62004 36.37 0 1\r\n"
    )


@pytest.fixture
def agf_utf16(agf_ansi: bytes) -> bytes:
    return agf_ansi.decode("utf-8").encode("utf-16")  # with byte order mark

