"""Expander to switch assemblies and elements on and off (schema 0.10, ``active`` flag)."""

from __future__ import annotations

import hashlib
import json

import streamlit as st

from ..active_nodes import node_rows, with_active
from ..compat import FEATURES


def active_nodes(json_text: str) -> str:
    """Show a check box per assembly and element; return the system text with the switched-off ones.

    The text is returned unchanged while nothing differs from the source. The widget keys carry a hash of the
    text, so the choice starts over when the source (or an adopted optimization result) changes.
    """
    if not FEATURES.inactive:
        return json_text
    data = json.loads(json_text)
    rows = node_rows(data)
    if len(rows) < 2:
        return json_text
    tag = hashlib.md5(json_text.encode("utf-8")).hexdigest()[:10]
    wanted: dict[str, bool] = {}
    with st.expander("Bauteile ein- und ausschalten"):
        st.caption("Ein ausgeschaltetes Bauteil bleibt im Modell und im Layout, aber kein Pfad besucht es "
                   "(`active: false`, Schema 0.10). Eine ausgeschaltete Baugruppe schaltet ihre Kinder mit aus. "
                   "Die Quelle bleibt unverändert; ein Wechsel der Quelle setzt die Auswahl zurück.")
        for row in rows:
            indent = " " * row["depth"]
            note = " (durch die Baugruppe aus)" if row["by_parent"] else ""
            wanted[row["pointer"]] = st.checkbox(
                f"{indent}{row['name']} ({row['kind']}){note}", value=row["active"],
                key=f"act_{tag}_{row['pointer']}", disabled=row["by_parent"])
    changed = {row["pointer"]: wanted[row["pointer"]] for row in rows if wanted[row["pointer"]] != row["active"]}
    if not changed:
        return json_text
    st.info(f"{sum(1 for v in changed.values() if not v)} Bauteil(e) ausgeschaltet; alle Ansichten rechnen ohne sie.")
    return json.dumps(with_active(data, changed))
