"""System source: reference system, upload or the surface-table builder."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from ..builder import BUILDER_COLUMNS, PRESETS, build_system_dict, surface_rows
from .common import STRETCH


def system_source(mode: str, repo: Path | None) -> tuple[str, str, dict | None]:
    """Return ``(json_text, source_key, builder_context)`` for the chosen mode.

    ``builder_context`` is only set in mode "System bauen" (surface rows and EPD). The function
    stops the script (``st.stop``) when there is nothing to show yet or the table is invalid.
    """
    ss = st.session_state
    json_text: str | None = None
    source_key = mode
    builder_context: dict | None = None

    if mode == "Beispielsystem":
        files = sorted((repo / "tests" / "reference").rglob("*.rtt.json"))
        labels = [str(p.relative_to(repo / "tests" / "reference")) for p in files]
        default_index = labels.index("m2/cooke_triplet.rtt.json") if "m2/cooke_triplet.rtt.json" in labels else 0
        choice = st.sidebar.selectbox("Beispielsystem", labels, index=default_index)
        json_text = files[labels.index(choice)].read_text(encoding="utf-8")
        source_key = choice
    elif mode == "Datei hochladen":
        up = st.sidebar.file_uploader("System (.rtt.json)", type=["json"])
        if up is None:
            st.info("Lade links eine `.rtt.json`-Datei hoch oder wähle ein Beispielsystem.")
            st.stop()
        json_text = up.getvalue().decode("utf-8")
        source_key = up.name
    else:
        st.subheader("System bauen")
        preset = st.selectbox("Vorlage", list(PRESETS), key="preset")
        if ss.get("loaded_preset") != preset:
            ss.loaded_preset = preset
            ss.bdf = pd.DataFrame(PRESETS[preset], columns=BUILDER_COLUMNS)
            ss.bver = ss.get("bver", 0) + 1
            ss.bedited = ss.bdf.copy()
        left, right = st.columns([3, 2])
        with left:
            name = st.text_input("Name", value=preset)
            epd = st.number_input("Eintrittspupillendurchmesser EPD (mm)", value=20.0, min_value=0.01)
            st.markdown("**Flächentabelle** (z-Position ergibt sich aus der Summe der Dicken)")
            edited = st.data_editor(
                ss.bdf, key=f"bed_{ss.bver}", num_rows="dynamic", **STRETCH,
                column_config={
                    "Typ": st.column_config.SelectboxColumn("Typ", options=["Fläche", "Blende", "Bild"],
                                                            required=True),
                    "Radius_mm": st.column_config.NumberColumn("Radius (mm, 0 = plan)", format="%.4f"),
                    "Konik": st.column_config.NumberColumn("Konik k", format="%.4f"),
                    "Dicke_mm": st.column_config.NumberColumn("Dicke bis nächste Zeile (mm)", format="%.4f"),
                    "Material_danach": st.column_config.TextColumn(
                        "Material danach", help="AIR, CONST:1.5168 oder KATALOG:GLAS (z. B. SCHOTT:N-BK7)"),
                    "Halbdurchm_mm": st.column_config.NumberColumn("Halbdurchm. (mm, 0 = frei)", format="%.3f"),
                    "Coating": st.column_config.TextColumn(
                        "Coating", help="Optional, KATALOG:NAME, z. B. DEMO:AR_MGF2 (Coating-Katalog "
                                        "in der Seitenleiste aktivieren)"),
                })
            ss.bedited = edited
            st.caption("Radiusvorzeichen: positiv, wenn der Krümmungsmittelpunkt bei +z liegt. "
                       "Glas steht in der Zeile der ersten Linsenfläche; die Fläche, die wieder in "
                       "Luft führt, schließt die Linse ab. Aufeinanderfolgende Gläser ergeben ein "
                       "verkittetes Element.")
            glass_options = ss.get("glass_options", [])
            if glass_options:
                with st.expander("Glas aus einem aktiven Katalog in die Tabelle eintragen"):
                    g1, g2 = st.columns([1, 3])
                    g1.number_input("Zeile", min_value=1, max_value=max(len(edited), 1), value=2,
                                    key="picker_row")
                    g2.selectbox("Glas", glass_options, key="picker_glass")

                    def put_glass():
                        df = ss.bedited.reset_index(drop=True).copy()
                        row = int(ss.picker_row) - 1
                        if 0 <= row < len(df):
                            df.loc[row, "Material_danach"] = ss.picker_glass
                            ss.bdf = df
                            ss.bver += 1

                    st.button("Eintragen", on_click=put_glass)
        with right:
            st.markdown("**Wellenlängen** (µm)")
            wl_df = st.data_editor(
                pd.DataFrame({"um": [0.4861, 0.5876, 0.6563], "weight": [1.0, 1.0, 1.0],
                              "Referenz": [False, True, False]}),
                key="wl_editor", num_rows="dynamic", **STRETCH)
            st.markdown("**Feldpunkte** (Grad, unendlich entferntes Objekt)")
            field_df = st.data_editor(
                pd.DataFrame({"x_deg": [0.0, 0.0, 0.0], "y_deg": [0.0, 3.5, 5.0], "weight": [1.0, 1.0, 1.0]}),
                key="field_editor", num_rows="dynamic", **STRETCH)

        try:
            rows = surface_rows(edited.reset_index(drop=True))
            system_dict = build_system_dict(name, epd, wl_df, field_df, rows)
        except ValueError as error:
            st.error(str(error))
            st.stop()
        json_text = json.dumps(system_dict)
        source_key = "builder"
        builder_context = {"rows": rows, "epd": epd}
    return json_text, source_key, builder_context
