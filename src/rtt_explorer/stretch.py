"""Streamlit version switch for the width of tables and charts (no library needed)."""

from __future__ import annotations


def stretch_kwargs(version: str) -> dict:
    """Streamlit >= 1.49 uses ``width='stretch'``; older versions use ``use_container_width``."""
    try:
        major, minor = (int(x) for x in version.split(".")[:2])
    except ValueError:
        return {"use_container_width": True}
    return {"width": "stretch"} if (major, minor) >= (1, 49) else {"use_container_width": True}
