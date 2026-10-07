"""View "Materialien"."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import raytatouille as rt
import streamlit as st

from ..catalogs import agf_names
from ..context import AppContext
from ..ui.common import STRETCH, show

TITLE = "Materialien"


def render(ctx: AppContext) -> None:
    """Render the view "Materialien"."""
    features = ctx.features
    system = ctx.system
    lib = ctx.lib
    candidates = ctx.candidates
    named = ctx.named
    env_t = system.environment.temperature_c
    env_p = system.environment.pressure_atm

    def index_curve(ref: str, lam: np.ndarray) -> np.ndarray:
        try:
            return np.asarray(lib.index(ref, lam, env_t, env_p), dtype=complex)
        except TypeError:  # older library: scalar index only
            return np.array([lib.index(ref, float(x), env_t, env_p) for x in lam], dtype=complex)

    picked: list[str] = []
    if features.glasses and lib.catalogs():
        cat = st.selectbox("Katalog", lib.catalogs())
        infos = lib.glasses(cat)
        status_names = list(getattr(rt.materials, "STATUS_NAMES", ()))
        df_all = pd.DataFrame({
            "Referenz": [g.reference for g in infos], "n_d": [g.nd for g in infos],
            "ν_d": [g.vd for g in infos], "Formel": [g.formula for g in infos],
            "Status": [status_names[g.status] if g.status is not None and 0 <= g.status < len(status_names)
                       else "–" for g in infos],
            "λ-Bereich (µm)": [f"{g.wavelength_range_um[0]:.2f}–{g.wavelength_range_um[1]:.2f}"
                               if g.wavelength_range_um else "–" for g in infos],
            "Dichte (g/cm³)": [g.density_g_per_cm3 for g in infos],
            "rel. Kosten": [g.relative_cost for g in infos],
            "unterstützt": [g.supported for g in infos]})
        f1, f2, f3 = st.columns(3)
        query = f1.text_input("Suche im Namen", value="")
        only_supported = f2.checkbox("Nur Gläser mit unterstützter Formel", value=False)
        statuses = f3.multiselect("Status", sorted(set(df_all["Status"])), default=[])
        df = df_all
        if query:
            df = df[df["Referenz"].str.contains(query, case=False, regex=False)]
        if only_supported:
            df = df[df["unterstützt"]]
        if statuses:
            df = df[df["Status"].isin(statuses)]
        st.dataframe(df, hide_index=True, **STRETCH)
        picked = st.multiselect("Gläser für Glaskarte und Dispersion", list(df["Referenz"]),
                                default=list(df["Referenz"])[:2])

        gm = lib.glass_map([cat])
        ok = (gm.vd > 0) & (gm.nd > 1.0)
        fig, ax = plt.subplots(figsize=(7, 4.8))
        ax.scatter(gm.vd[ok], gm.nd[ok], s=14, color="lightgray", label="Katalog")
        for ref in picked:
            for k, r in enumerate(gm.reference):
                if r == ref and ok[k]:
                    ax.scatter([gm.vd[k]], [gm.nd[k]], s=40, label=ref)
                    ax.annotate(ref.split(":")[-1], (gm.vd[k], gm.nd[k]), fontsize=7,
                                xytext=(4, 4), textcoords="offset points")
        ax.invert_xaxis()
        ax.set_xlabel("Abbe-Zahl ν_d")
        ax.set_ylabel("Brechzahl n_d")
        ax.set_title(f"Glaskarte {cat} (Werte aus den NM-Zeilen)")
        ax.legend(fontsize=7, ncol=2)
        ax.grid(alpha=0.3)
        show(fig)

        if picked:
            detail = st.selectbox("Details zu einem Glas", picked)
            g = lib.glass(detail)
            d1, d2 = st.columns(2)
            with d1:
                st.write({"Formel": g.formula, "unterstützt": g.supported,
                          "Grund (falls nein)": g.unsupported_reason, "n_d": g.nd, "ν_d": g.vd,
                          "Dichte g/cm³": g.density_g_per_cm3, "Kommentar": g.comment,
                          "dn/dT-Daten": g.thermal._asdict() if g.thermal else None})
            with d2:
                if len(g.transmission):
                    fig, ax = plt.subplots(figsize=(5.5, 3.6))
                    ax.plot(g.transmission[:, 0], g.transmission[:, 1], "-")
                    ax.set_xlabel("Wellenlänge / µm")
                    ax.set_ylabel("Reintransmission τ_i")
                    thick = g.transmission[0, 2]
                    ax.set_title(f"Innere Transmission (Dicke {thick:g} mm)")
                    ax.grid(alpha=0.3)
                    show(fig)
                else:
                    st.caption("Der Katalog enthält keine Transmissionsdaten für dieses Glas.")
    else:
        options: list[str] = []
        for label, cname in named:
            options += [f"{cname}:{g}" for g in agf_names(candidates[label][1])]
        picked = st.multiselect("Materialien", options + ["AIR", "VACUUM"], default=options[:2])

    extra = st.text_input("Weitere Referenzen (Komma)", value="CONST:1.5168")
    picked = picked + [e.strip() for e in extra.split(",") if e.strip()]
    lo, hi = st.slider("Wellenlängenbereich (µm)", 0.3, 2.5, (0.4, 0.9), step=0.01)
    lam = np.linspace(lo, hi, 150)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    abbe_rows = []
    for ref in picked:
        try:
            n = index_curve(ref, lam)
        except (rt.RaytatouilleError, ValueError) as error:
            st.error(f"{ref}: {error}")
            continue
        ax.plot(lam, n.real, label=ref)
        try:
            nd, nF, nC = (index_curve(ref, np.array([x])).real[0] for x in (0.5875618, 0.4861327, 0.6562725))
            abbe_rows.append({"Material": ref, "n_d": nd,
                              "Abbe ν_d": (nd - 1) / (nF - nC) if nF != nC else float("inf")})
        except (rt.RaytatouilleError, ValueError):
            pass
    ax.set_xlabel("Wellenlänge / µm")
    ax.set_ylabel("Brechzahl n (absolut)")
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    show(fig)
    if abbe_rows:
        st.dataframe(pd.DataFrame(abbe_rows), hide_index=True, **STRETCH)
        st.caption(f"Absolute Brechzahlen bei {env_t:g} °C und {env_p:g} atm. Der Katalogwert nd "
                   "bezieht sich meist auf Luft und weicht deshalb leicht ab.")
