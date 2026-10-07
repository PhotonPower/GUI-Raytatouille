"""Entry point of the Streamlit app (guards against a missing ``raytatouille`` package)."""

from __future__ import annotations

import streamlit as st


def main() -> None:
    """Configure the page, check the dependency, then run the explorer."""
    st.set_page_config(page_title="Raytatouille Explorer", page_icon="🔬", layout="wide")
    try:
        import raytatouille  # noqa: F401
    except ImportError:
        st.error(
            "Das Paket `raytatouille` ist nicht installiert. Im Repo-Ordner der Bibliothek "
            "ausführen: `pip install .[plot]` (siehe docs/installation.md)."
        )
        st.stop()
    from .explorer import run

    run()
