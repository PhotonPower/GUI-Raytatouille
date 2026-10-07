"""Active glass and coating catalogues (chosen automatically from the references in the system)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from ..catalogs import Candidates, agf_names, assign_names, auto_catalogs, auto_coatings, coating_info
from ..compat import FEATURES


def select_catalogs(refs: set[tuple[str, str]], crefs: set[tuple[str, str]],
                    candidates: Candidates, coat_candidates: Candidates, mode: str,
                    source_key: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Sidebar multiselects; returns ``(named, selected_coatings)``.

    ``named`` is a list of ``(candidate label, catalogue name in the system)``.
    """
    auto = auto_catalogs(refs, candidates)
    default_cats = auto or (["schott.agf"] if mode == "System bauen" and "schott.agf" in candidates else [])
    with st.sidebar:
        selected_catalogs = st.multiselect(
            "Aktive Glaskataloge", list(candidates), default=[c for c in default_cats if c in candidates],
            key=f"cats_{source_key}_{sorted(refs)}",
            help="Gleichnamige Dateien (z. B. zwei 'schott.agf') werden mit Alias geladen "
                 "(SCHOTT, SCHOTT_2), sofern die Bibliothek das kann.")
        named = assign_names(selected_catalogs, candidates)
        if not FEATURES.alias:
            unique, seen_names = [], set()
            for label, cname in named:
                if cname in seen_names:
                    st.warning(f"{label}: Katalogname {cname} ist schon vergeben (diese Bibliotheksversion "
                               "hat keinen Alias) und wird nicht geladen.")
                    continue
                seen_names.add(cname)
                unique.append((label, cname))
            named = unique
        for label, cname in named:
            if cname != Path(candidates[label][0]).stem.upper():
                st.caption(f"{label} → Name im System: {cname}")
        missing = [f"{c}:{g}" for c, g in sorted(refs) if not any(
            cname == c and g in agf_names(candidates[label][1]) for label, cname in named)]
        if missing:
            st.warning("Nicht im gewählten Katalog gefunden: " + ", ".join(missing))

        selected_coatings: list[str] = []
        if FEATURES.coatings and (coat_candidates or crefs):
            auto_c = auto_coatings(crefs, coat_candidates)
            selected_coatings = st.multiselect(
                "Aktive Coating-Kataloge", list(coat_candidates),
                default=[c for c in auto_c if c in coat_candidates],
                key=f"coats_{source_key}_{sorted(crefs)}")
            missing_c = [f"{c}:{n}" for c, n in sorted(crefs) if not any(
                coating_info(coat_candidates[s][1])[0] == c and n in coating_info(coat_candidates[s][1])[1]
                for s in selected_coatings)]
            if missing_c:
                st.warning("Coating nicht im gewählten Katalog gefunden: " + ", ".join(missing_c))
    return named, selected_coatings
