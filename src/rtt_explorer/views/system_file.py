"""View "System-Datei"."""

from __future__ import annotations

import streamlit as st

from ..context import AppContext

TITLE = "System-Datei"


def render(ctx: AppContext) -> None:
    """Render the view "System-Datei"."""
    system = ctx.system
    text = system.to_json()
    st.download_button("Als .rtt.json speichern", text.encode(), file_name="system.rtt.json",
                       mime="application/json")
    st.code(text, language="json")
