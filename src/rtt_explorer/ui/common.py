"""Small UI helpers shared by all views."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import pandas as pd
import raytatouille as rt
import streamlit as st

from ..messages import diagnostic_text, loss_rows, unique
from ..stretch import stretch_kwargs

STRETCH = stretch_kwargs(st.__version__)


def show(fig) -> None:
    st.pyplot(fig)
    plt.close(fig)


def fmt(value, digits=4) -> str:
    if value is None:
        return "–"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isinf(v) or math.isnan(v):
        return "∞" if math.isinf(v) else "–"
    return f"{v:.{digits}f}"


def diagnostic_line(comp, d) -> str:
    """One library Diagnostic (or RaytatouilleWarning) as text with surface id and code."""
    return diagnostic_text(getattr(d, "code", ""), getattr(d, "message", str(d)), getattr(d, "location", None),
                           list(getattr(comp, "surface_locations", [])), list(comp.surface_ids))


def show_result_notes(comp, result, file_stem: str, key: str) -> None:
    """Warnings, ray losses and JSON export of an analysis result, as far as the library offers them."""
    if result is None:
        return
    for text in unique(diagnostic_line(comp, d) for d in getattr(result, "warnings", [])):
        st.warning(text)
    losses = getattr(result, "losses", None)
    if losses is not None:
        names = {int(m): name for name, m in rt.trace.RayStatus.__members__.items()}
        rows = loss_rows(list(losses.by_status), names, int(losses.launched), int(rt.trace.RayStatus.ALIVE))
        if rows:
            with st.expander(f"Verlorene Strahlen: {sum(r['Strahlen'] for r in rows)} von {losses.launched}"):
                if losses.worst_surface is not None:
                    st.write(f"Die meisten Strahlen gehen an Fläche **{comp.surface_ids[int(losses.worst_surface)]}** "
                             f"verloren ({losses.worst_surface_count}).")
                st.dataframe(pd.DataFrame(rows), hide_index=True, **STRETCH)
    if hasattr(result, "to_json"):
        st.download_button("Ergebnis als JSON", result.to_json(indent=1).encode(), file_name=f"{file_stem}.result.json",
                           mime="application/json", key=f"json_{key}",
                           help="Ergebnisformat raytatouille-result der Bibliothek (rt.results.load_json).")


def run(label_error: str, func, *args, **kwargs):
    """Call an analysis; show library errors as readable messages instead of a traceback."""
    try:
        return func(*args, **kwargs)
    except rt.RaytatouilleError as error:
        st.error(f"{label_error}: {error}")
    except (ValueError, IndexError) as error:
        st.error(f"{label_error}: {error}")
    return None
