"""View "System-Datei"."""

from __future__ import annotations

import json

import pandas as pd
import raytatouille as rt
import streamlit as st

from ..context import AppContext
from ..schema_check import MAX_ROWS, schema_rows
from ..ui.common import STRETCH

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
    if ctx.features.schemas:
        _schema_expander(ctx)
    st.code(text, language="json")


SCHEMAS = {"system": "System (.rtt.json)", "result": "Ergebnis", "coatings": "Coating-Katalog",
           "lenses": "Linsenkatalog"}


def _schema_expander(ctx: AppContext) -> None:
    """Schema downloads and the check of the file against the JSON schema (``rt.schema``, library 0.10)."""
    with st.expander("JSON-Schema des Dateiformats"):
        st.caption("`rt.schema()` liefert das JSON-Schema (Draft 2020-12), etwa für Editoren mit Auswahllisten. "
                   "Die Prüfung unten vergleicht die Datei, wie sie geladen wurde, mit dem Schema; die "
                   "inhaltliche Prüfung (Konsistenz, Glas, Pfade) macht die Bibliothek beim Laden.")
        columns = st.columns(len(SCHEMAS))
        for column, (name, label) in zip(columns, SCHEMAS.items(), strict=True):
            try:
                body = json.dumps(rt.schema(name), indent=1)
            except ValueError:  # an older library without this schema
                continue
            column.download_button(f"Schema: {label}", body.encode(), file_name=f"{name}.schema.json",
                                   mime="application/json", key=f"schema_dl_{name}")
        if st.button("Datei gegen das Schema prüfen", key="schema_check"):
            try:
                rows = schema_rows(rt.schema("system"), ctx.system_dict)
            except ImportError:
                st.info("Für die Prüfung muss das Paket `jsonschema` installiert sein (`pip install jsonschema`).")
                return
            if not rows:
                st.success("Die Datei entspricht dem Schema.")
            else:
                st.warning(f"{len(rows)} Abweichung(en)" + (f" (höchstens {MAX_ROWS} angezeigt)"
                                                           if len(rows) == MAX_ROWS else ""))
                st.dataframe(pd.DataFrame(rows), hide_index=True, **STRETCH)
