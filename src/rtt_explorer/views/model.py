"""View "Modell": the model tree of the loaded system, read only (library G3)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..context import AppContext
from ..model_table import num, param_text, surface_rows
from ..ui.common import STRETCH

TITLE = "Modell"

APERTURE_TYPES = {"ENTRANCE_PUPIL_DIAMETER": "Eintrittspupille Ø (mm)",
                  "IMAGE_SPACE_F_NUMBER": "Blendenzahl bildseitig", "OBJECT_SPACE_NA": "NA objektseitig",
                  "STOP_SIZE": "Blendengröße (mm)"}
FIELD_TYPES = {"ANGLE_DEG": "Winkel (°)", "OBJECT_HEIGHT": "Objekthöhe (mm)",
               "PARAXIAL_IMAGE_HEIGHT": "paraxiale Bildhöhe (mm)"}


def render(ctx: AppContext) -> None:
    """Render the view "Modell"."""
    if not ctx.features.model:
        st.info("Die installierte Bibliotheksversion kann das Modell nicht lesen (`System.root` ab 0.5). "
                "Die Ansicht System-Datei zeigt das JSON.")
        return
    system = ctx.system
    aperture, objects = system.aperture, system.object_space
    m = st.columns(3)
    m[0].metric(APERTURE_TYPES.get(aperture.type.name, aperture.type.name), param_text(aperture.value))
    m[1].metric("Objekt", "unendlich" if objects.at_infinity else f"{param_text(objects.distance)} mm")
    m[2].metric("Feldart", FIELD_TYPES.get(system.fields.type.name, system.fields.type.name))

    st.markdown("**Flächen** (V = Variable, → = an eine Zeile der Parametertabelle gebunden)")
    st.dataframe(pd.DataFrame(surface_rows(system.root)), hide_index=True, **STRETCH)

    st.markdown("**Pfade**")
    st.dataframe(pd.DataFrame([{
        "Pfad": p.name,
        "Ereignisse": "automatisch" if p.automatic else " → ".join(_event_text(e) for e in p.events),
    } for p in system.paths]), hide_index=True, **STRETCH)

    params = list(getattr(system, "parameters", []))
    configs = [c.name for c in getattr(system, "configurations", [])]
    if params or configs:
        st.markdown("**Parametertabelle**" + (f" (Konfigurationen: {', '.join(configs)})" if configs else ""))
        st.dataframe(pd.DataFrame([_parameter_row(r, configs) for r in params]), hide_index=True, **STRETCH)
        st.caption("Die Bibliothek liest Parametertabelle und Konfigurationen (Schema 0.4), wertet sie in "
                   "Python aber noch nicht aus; gebundene Werte lassen sich daher noch nicht kompilieren.")
    st.caption("Nur lesen: Geändert wird das System im Baukasten oder in der Datei. Modell aus "
               "`System.root`, `System.paths` und `System.parameters` der Bibliothek.")


def _event_text(event) -> str:
    kind = event.kind.name.lower()
    order = getattr(event, "order", 0)
    text = f"{event.surface} ({kind}"
    return text + (f", Ordnung {order:+d})" if order else ")")


def _parameter_row(row, configs: list[str]) -> dict:
    if getattr(row, "expression", None):
        value = f"= {row.expression}"
    elif getattr(row, "values", None):
        value = ", ".join(f"{c}: {num(v)}" for c, v in zip(configs, row.values)) if configs else \
            ", ".join(num(v) for v in row.values)
    else:
        value = num(getattr(row, "value", None))
    bounds = ""
    if getattr(row, "min", None) is not None or getattr(row, "max", None) is not None:
        bounds = f"[{num(row.min) if row.min is not None else '−∞'}, {num(row.max) if row.max is not None else '∞'}]"
    return {"Name": row.name, "Wert": value, "Variable": bool(getattr(row, "variable", False)), "Grenzen": bounds}
