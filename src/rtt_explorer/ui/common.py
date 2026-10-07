"""Small UI helpers shared by all views."""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import raytatouille as rt
import streamlit as st

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


def run(label_error: str, func, *args, **kwargs):
    """Call an analysis; show library errors as readable messages instead of a traceback."""
    try:
        return func(*args, **kwargs)
    except rt.RaytatouilleError as error:
        st.error(f"{label_error}: {error}")
    except (ValueError, IndexError) as error:
        st.error(f"{label_error}: {error}")
    return None
