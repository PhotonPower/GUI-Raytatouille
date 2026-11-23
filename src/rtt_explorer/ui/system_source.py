"""System source: reference system, upload or the surface-table builder."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from ..builder import (
    BUILDER_COLUMNS,
    MERIT_COLUMNS,
    MERIT_OPERANDS,
    MIN_THICKNESS,
    PRESETS,
    ROW_TYPES,
    SHAPE_COLUMNS,
    VARIABLE_COLUMNS,
    build_system_dict,
    surface_rows,
)
from ..compat import FEATURES
from ..surface_shapes import FORMS
from .common import STRETCH
from .design_helper import design_helper


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
        # Compared as paths: the labels use the platform separator (backslash on Windows).
        default = Path("m2/cooke_triplet.rtt.json")
        default_index = next((i for i, label in enumerate(labels) if Path(label) == default), 0)
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
        for col in VARIABLE_COLUMNS:  # also for tables of sessions from before the variable columns
            if col not in ss.bdf:
                ss.bdf[col] = False
        for col in SHAPE_COLUMNS:  # the same for the surface forms
            if col not in ss.bdf:
                ss.bdf[col] = ""
        left, right = st.columns([3, 2])
        with left:
            name = st.text_input("Name", value=preset)
            epd = st.number_input("Eintrittspupillendurchmesser EPD (mm)", value=20.0, min_value=0.01)
            design_helper(epd)
            st.markdown("**Flächentabelle** (z-Position ergibt sich aus der Summe der Dicken)")
            row_types = [t for t in ROW_TYPES if t != "Ideallinse" or FEATURES.ideal_lens]
            edited = st.data_editor(
                ss.bdf, key=f"bed_{ss.bver}", num_rows="dynamic", **STRETCH,
                column_order=BUILDER_COLUMNS + VARIABLE_COLUMNS + (SHAPE_COLUMNS if FEATURES.surface_types else []),
                column_config={
                    "Typ": st.column_config.SelectboxColumn("Typ", options=row_types, required=True),
                    "Radius_mm": st.column_config.NumberColumn(
                        "Radius (mm, 0 = plan)", format="%.4f", help="Bei einer Ideallinse die Brennweite f (mm)."),
                    "Konik": st.column_config.NumberColumn("Konik k", format="%.4f"),
                    "Dicke_mm": st.column_config.NumberColumn("Dicke bis nächste Zeile (mm)", format="%.4f"),
                    "Material_danach": st.column_config.TextColumn(
                        "Material danach", help="AIR, CONST:1.5168 oder KATALOG:GLAS (z. B. SCHOTT:N-BK7)"),
                    "Halbdurchm_mm": st.column_config.NumberColumn("Halbdurchm. (mm, 0 = frei)", format="%.3f"),
                    "Coating": st.column_config.TextColumn(
                        "Coating", help="Optional, KATALOG:NAME, z. B. DEMO:AR_MGF2 (Coating-Katalog "
                                        "in der Seitenleiste aktivieren)"),
                    "Form": st.column_config.SelectboxColumn(
                        "Form", options=list(FORMS[1:]), required=False,
                        help="Leer: Kugel oder Konik. Sonst Biconic, Toroid, Zylinder, Odd Asphere, Axicon oder "
                             "Forbes Q-con/Q-bfs (Schema 0.9); die weiteren Werte stehen in Form-Parameter."),
                    "Form_Parameter": st.column_config.TextColumn(
                        "Form-Parameter", help="schlüssel=wert, getrennt durch Semikolon, Listen mit Komma. "
                                               "Biconic: radius_y, conic_y. Toroid: radius_of_rotation, "
                                               "coefficients. Zylinder: coefficients. Odd Asphere: coefficients "
                                               "(A1, A2, …). Axicon: angle_deg. Q-con, Q-bfs: "
                                               "normalization_radius, coefficients."),
                    "R_var": st.column_config.CheckboxColumn("R var", help="Radius ist Optimierungsvariable"),
                    "K_var": st.column_config.CheckboxColumn("k var", help="Konik ist Optimierungsvariable"),
                    "D_var": st.column_config.CheckboxColumn(
                        "d var", help=f"Dicke ist Optimierungsvariable (mindestens {MIN_THICKNESS} mm)"),
                })
            ss.bedited = edited
            st.caption("Radiusvorzeichen: positiv, wenn der Krümmungsmittelpunkt bei +z liegt. "
                       "Glas steht in der Zeile der ersten Linsenfläche; die Fläche, die wieder in "
                       "Luft führt, schließt die Linse ab. Aufeinanderfolgende Gläser ergeben ein "
                       "verkittetes Element." + (" Eine Zeile vom Typ Ideallinse ist eine dünne ideale Linse in "
                                                  "Luft mit der Brennweite in der Radius-Spalte."
                                                  if FEATURES.ideal_lens else ""))
            if FEATURES.surface_types:
                st.caption("Spalte Form: Bei Biconic gelten Radius und Konik für den x-Schnitt, radius_y und conic_y "
                           "stehen in den Form-Parametern. Toroid und Zylinder: Radius im y-z-Schnitt. Odd Asphere, "
                           "Q-con und Q-bfs tragen die Krümmung 1/Radius (Radius 0 = plane Basis). Beispiel "
                           "Form-Parameter: `radius_y=-60` oder `coefficients=0, 1e-4`.")
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
            merit_df = None
            if FEATURES.optim:
                st.markdown("**Merit-Funktion** (für die Ansicht Optimierung)")
                # Start content from session_state like the surface table (empty by default).
                merit_start = ss.get("bmerit")
                if merit_start is None:
                    merit_start = pd.DataFrame({"Operand": pd.Series([], dtype="object"),
                                                "Ziel": pd.Series([], dtype=float),
                                                "Gewicht": pd.Series([], dtype=float)})
                merit_df = st.data_editor(
                    merit_start[MERIT_COLUMNS],
                    key="merit_editor", num_rows="dynamic", **STRETCH,
                    column_config={
                        "Operand": st.column_config.SelectboxColumn("Operand", options=list(MERIT_OPERANDS)),
                        "Ziel": st.column_config.NumberColumn(
                            "Ziel", help="Zielwert für EFL, BFL (mm) und Blendenzahl; die übrigen haben Ziel 0."),
                        "Gewicht": st.column_config.NumberColumn("Gewicht", help="leer = 1"),
                    })
                st.caption("Variablen: Häkchen „R var“, „k var“, „d var“ in der Flächentabelle. „Randstrahl im "
                           "Fokus“ hält die Bildebene im paraxialen Fokus, RMS-Spot und RMS-Wellenfront bewerten "
                           "die Abbildung über alle Felder und Wellenlängen.")

        try:
            rows = surface_rows(edited.reset_index(drop=True))
            system_dict = build_system_dict(name, epd, wl_df, field_df, rows, merit_df)
        except ValueError as error:
            st.error(str(error))
            st.stop()
        json_text = json.dumps(system_dict)
        source_key = "builder"
        builder_context = {"rows": rows, "epd": epd}
    return json_text, source_key, builder_context
