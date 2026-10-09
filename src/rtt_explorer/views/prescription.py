"""View "Prescription": paraxial marginal and chief ray per surface event (library G5)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import raytatouille as rt
import streamlit as st

from ..context import AppContext
from ..ui.common import STRETCH, fmt, run, show

TITLE = "Prescription"

# Column of the library result -> (column title, description for the help text)
COLUMNS = {
    "z": ("z (mm)", "globale z-Position des Scheitels"),
    "n": ("n danach", "Brechzahl nach dem Ereignis, negativ in Richtung −z (nach Spiegeln)"),
    "y": ("y Rand (mm)", "Höhe des paraxialen Randstrahls"),
    "u": ("u Rand", "Steigung dy/dz des Randstrahls nach dem Ereignis"),
    "i": ("i Rand (rad)", "paraxialer Einfallswinkel i = u + y·c des Randstrahls"),
    "y_bar": ("ȳ Haupt (mm)", "Höhe des paraxialen Hauptstrahls"),
    "u_bar": ("ū Haupt", "Steigung des Hauptstrahls nach dem Ereignis"),
    "i_bar": ("ī Haupt (rad)", "Einfallswinkel des Hauptstrahls"),
    "lagrange": ("Lagrange (mm)", "n′(ū′·y − u′·ȳ) nach dem Ereignis"),
}


def render(ctx: AppContext) -> None:
    """Render the view "Prescription"."""
    if not ctx.features.prescription:
        st.info("Die installierte Bibliotheksversion hat kein `raytatouille.paraxial.prescription` (ab 0.5).")
        return
    comp = ctx.comp
    w = st.selectbox("Wellenlänge", [None] + ctx.wl_ids,
                     format_func=lambda i: "Referenz" if i is None else ctx.wl_label(i), key="presc_wl")
    p = run("Prescription", rt.paraxial.prescription, comp, path=ctx.path_choice, wavelength=w)
    if p is None:
        st.caption("Die Prescription gibt es nur für rotationssymmetrische Pfade (keine Faltung, keine "
                   "Beugungsordnung ≠ 0, kein Kristall).")
        return

    m = st.columns(5)
    m[0].metric("Baulänge", f"{fmt(p.total_track)} mm", help="Abgewickelt, Spiegel eingerechnet.")
    m[1].metric("Objektabstand", "∞" if p.object_distance is None else f"{fmt(p.object_distance)} mm")
    m[2].metric("Arbeitsblende (paraxial)", fmt(p.paraxial_working_f_number, 3), help="1 / (2·|n′u′|)")
    m[3].metric("Bild-NA (paraxial)", fmt(p.paraxial_image_na, 4), help="|n′u′|")
    m[4].metric("Lagrange-Invariante", f"{fmt(p.lagrange_invariant)} mm")

    q = p.surfaces
    table = pd.DataFrame({"Fläche": [comp.surface_ids[int(s)] for s in np.asarray(q.surface)]})
    for name, (title, _) in COLUMNS.items():
        table[title] = np.asarray(getattr(q, name), dtype=float)
    st.dataframe(table, hide_index=True, **STRETCH,
                 column_config={title: st.column_config.NumberColumn(title, help=text, format="%.6g")
                                for title, text in COLUMNS.values()})
    if np.isnan(table["y Rand (mm)"]).all():
        st.caption("Ohne Blende gibt es keinen Rand- und Hauptstrahl; die Spalten bleiben leer.")
    else:
        fig, ax = plt.subplots(figsize=(10, 3.6))
        ax.plot(table["z (mm)"], table["y Rand (mm)"], "o-", label="Randstrahl y")
        ax.plot(table["z (mm)"], table["ȳ Haupt (mm)"], "s-", label="Hauptstrahl ȳ")
        ax.axhline(0, color="gray", lw=0.5, ls="--")
        ax.set_xlabel("z / mm (Scheitel)")
        ax.set_ylabel("Höhe / mm")
        ax.set_title("Paraxiale Strahlhöhen an den Flächen")
        ax.grid(alpha=0.3)
        ax.legend()
        show(fig)

    a, b = st.columns(2)
    a.download_button("Tabelle als CSV", table.to_csv(index=False).encode(), file_name="prescription.csv",
                      mime="text/csv")
    if hasattr(p, "to_json"):
        b.download_button("Ergebnis als JSON", p.to_json(indent=1).encode(),
                          file_name="prescription.result.json", mime="application/json")
    st.caption("Paraxiale Daten der Bibliothek (rt.paraxial.prescription); Ereignisse in Pfadreihenfolge, "
               "Werte nach dem jeweiligen Ereignis. NaN, wo eine Größe nicht definiert ist.")
