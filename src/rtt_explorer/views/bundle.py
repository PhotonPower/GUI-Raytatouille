"""View "Strahlenbündel"."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import raytatouille as rt
import streamlit as st

from ..context import AppContext
from ..ui.common import run, show

TITLE = "Strahlenbündel"


def render(ctx: AppContext) -> None:
    """Render the view "Strahlenbündel"."""
    comp = ctx.comp
    path_choice = ctx.path_choice
    field_ids = ctx.field_ids
    wl_ids = ctx.wl_ids
    can_aim = ctx.can_aim
    field_label = ctx.field_label
    wl_label = ctx.wl_label
    aim_map = ctx.aim_map
    if not can_aim:
        st.info("Dieses System hat keine Blende. Strahlen lassen sich im Layout- und im "
                "Polarisations-Tab mit einem freien kollimierten Bündel erzeugen.")
    c1, c2, c3, c4 = st.columns(4)
    f = c1.selectbox("Feld", field_ids, format_func=field_label)
    w = c2.selectbox("Wellenlänge", [None] + wl_ids,
                     format_func=lambda i: "Referenz" if i is None else wl_label(i))
    kinds = ["Hexapolar (Ringe)", "Gitter (n × n)", "Zufall (Anzahl)"]
    if ctx.features.gauss:
        kinds.append("Gauß-Quadratur (Ringe × 6 Arme)")
    kind = c3.selectbox("Pupillenraster", kinds)
    n = c4.slider("Größe", 1, 40 if kind != "Zufall (Anzahl)" else 2000, 8 if kind != "Zufall (Anzahl)" else 300)
    aim = aim_map[st.radio("Aiming", list(aim_map), horizontal=True, key="aim_trace")]
    sampling = {"Hexapolar (Ringe)": lambda: rt.trace.HexapolarPupil(rings=n),
                "Gitter (n × n)": lambda: rt.trace.GridPupil(n=n),
                "Zufall (Anzahl)": lambda: rt.trace.RandomPupil(count=n, seed=1),
                "Gauß-Quadratur (Ringe × 6 Arme)": lambda: rt.trace.GaussPupil(rings=n, arms=6)}[kind]()
    rays = run("Strahlen erzeugen", rt.trace.make_rays, comp, sampling, path=path_choice,
               fields=[f], wavelength=w, aiming=aim)
    if rays is not None:
        stats = run("Strahlverfolgung", rt.trace.trace, comp, rays, path=path_choice)
        if stats is not None:
            counts = {name: stats.count(member) for name, member in rt.trace.RayStatus.__members__.items()}
            st.dataframe(pd.DataFrame({"Status": list(counts), "Strahlen": list(counts.values())}),
                         hide_index=True)
            status = np.asarray(rays.status)
            alive = status == int(rt.trace.RayStatus.ALIVE)
            a, b = st.columns(2)
            with a:
                fig, ax = plt.subplots(figsize=(5.5, 5))
                colours = np.where(alive, "tab:green", "tab:red")
                ax.scatter(np.asarray(rays.pupil_x), np.asarray(rays.pupil_y), c=colours, s=14)
                ax.set_aspect("equal")
                ax.set_xlabel("px")
                ax.set_ylabel("py")
                ax.set_title("Pupille: grün = angekommen, rot = verloren")
                show(fig)
            with b:
                fig, ax = plt.subplots(figsize=(5.5, 5))
                sc = ax.scatter(np.asarray(rays.pos_x)[alive], np.asarray(rays.pos_y)[alive],
                                c=np.asarray(rays.pupil_y)[alive], s=14)
                fig.colorbar(sc, ax=ax, label="py (Pupille)")
                ax.set_aspect("equal", adjustable="datalim")
                ax.set_xlabel("x / mm (global)")
                ax.set_ylabel("y / mm (global)")
                ax.set_title("Auftreffpunkte auf der Bildfläche")
                show(fig)
            table = pd.DataFrame({
                "pupil_x": np.asarray(rays.pupil_x), "pupil_y": np.asarray(rays.pupil_y),
                "x_mm": np.asarray(rays.pos_x), "y_mm": np.asarray(rays.pos_y),
                "z_mm": np.asarray(rays.pos_z), "dir_x": np.asarray(rays.dir_x),
                "dir_y": np.asarray(rays.dir_y), "dir_z": np.asarray(rays.dir_z),
                "opl_mm": np.asarray(rays.opl), "status": status})
            if kind.startswith("Gauß"):
                # Quadrature weights of the library (sum 1 per field and wavelength), not ray powers
                q = np.asarray(rt.trace.gauss_pupil_weights(sampling), dtype=float)
                table["gauss_weight"] = np.tile(q, len(table) // len(q)) if len(table) % len(q) == 0 else np.nan
                st.caption("Gauß-Legendre-Ringe in ρ² (DLMF 3.5): Σ Gewicht · Größe ist der Pupillenmittelwert. "
                           "Die Gewichte stehen in der Spalte gauss_weight der CSV.")
            st.download_button("Strahltabelle als CSV", table.to_csv(index=False).encode(),
                               file_name="strahlen.csv", mime="text/csv")
