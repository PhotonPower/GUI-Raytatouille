"""View "System-Datei"."""

from __future__ import annotations

import raytatouille as rt
import streamlit as st

from ..context import AppContext

TITLE = "System-Datei"


def render(ctx: AppContext) -> None:
    """Render the view "System-Datei"."""
    system = ctx.system
    text = system.to_json()
    st.download_button("Als .rtt.json speichern", text.encode(), file_name="system.rtt.json",
                       mime="application/json")
    if ctx.features.configs and ctx.configuration is not None:
        name = getattr(ctx.comp, "configuration_name", "") or str(ctx.configuration)
        try:
            resolved = system.resolved(ctx.configuration).to_json()
        except (rt.RaytatouilleError, ValueError) as error:
            st.caption(f"Konfiguration {name} lässt sich nicht auflösen: {error}")
        else:
            st.download_button(f"Konfiguration {name} mit festen Werten speichern", resolved.encode(),
                               file_name=f"system-{name}.rtt.json", mime="application/json",
                               help="System.resolved: jeder gebundene Wert wird zur Zahl dieser Konfiguration; "
                                    "Parametertabelle und Konfigurationen bleiben in der Datei.")
    st.code(text, language="json")
