"""The script flow of one Streamlit run: sidebar, system, compile, header, chosen view."""

from __future__ import annotations

import json

import raytatouille as rt
import streamlit as st

from .catalogs import coating_refs, material_refs
from .compat import FEATURES
from .context import AppContext
from .loader import configuration_names, make_system
from .ui.catalog_select import select_catalogs
from .ui.header import first_order, render_header
from .ui.sidebar import collect_catalogs, project_sidebar
from .ui.system_source import system_source
from .views import VIEWS


def _can_aim(comp, path: str, reference_wavelength: int) -> bool:
    """True if the pupil can be aimed (the system has a stop)."""
    try:
        rt.trace.make_rays(comp, rt.trace.HexapolarPupil(rings=1), path=path, fields=[0],
                           wavelength=reference_wavelength)
    except (rt.RaytatouilleError, ValueError):
        return False
    return True


def _optimized_override(source_key: str, json_text: str) -> str:
    """The adopted optimization result instead of the source text, while source and text are unchanged.

    The view "Optimierung" stores it in ``optim_override``; ``optim_source`` and ``optim_base`` hold the
    original source so that a second optimization keeps the same base.
    """
    ss = st.session_state
    ss.optim_source, ss.optim_base = source_key, json_text
    override = ss.get("optim_override")
    if not override:
        return json_text
    if override["source"] != source_key or override["base"] != json_text:
        del ss["optim_override"]  # the source changed: the result belongs to another system
        return json_text
    a, b = st.columns([5, 1])
    a.info("Das optimierte System ist aktiv; alle Ansichten zeigen es. Die Quelle selbst ist unverändert.")
    b.button("Verwerfen", on_click=lambda: ss.pop("optim_override", None), key="optim_discard")
    return override["json"]


def run() -> None:
    """Execute one script run. ``st.stop()`` ends it early when there is nothing to show."""
    st.title("🔬 Raytatouille Explorer")
    st.caption("Optikdesign ausprobieren: System laden oder bauen, dann analysieren. "
               "Längen in mm, Wellenlängen in µm, Felder in Grad.")

    ss = st.session_state
    project = project_sidebar()
    candidates, coat_candidates = collect_catalogs(project.repo, project.repo_ok)
    json_text, source_key, builder_context = system_source(project.mode, project.repo)
    json_text = _optimized_override(source_key, json_text)

    system_dict = json.loads(json_text)
    refs = material_refs(system_dict)
    crefs = coating_refs(system_dict)
    named, selected_coatings = select_catalogs(refs, crefs, candidates, coat_candidates,
                                               project.mode, source_key)
    if crefs and not FEATURES.coatings:
        st.warning("Dieses System enthält Coatings, die installierte Bibliotheksversion kann sie "
                   "nicht kompilieren (Coating-Bibliothek erst ab 0.4).")

    catalog_tuple = tuple((cname, candidates[label][1]) for label, cname in named)
    coating_tuple = tuple((coat_candidates[s][0], coat_candidates[s][1]) for s in selected_coatings)
    configuration = None
    names = configuration_names(json_text) if FEATURES.configs else []
    if names:
        configuration = names.index(st.sidebar.selectbox(
            "Konfiguration", names, key=f"config_{source_key}",
            help="Spalte der Parametertabelle, mit der das System kompiliert wird (Schema 0.4)."))
    state = make_system(json_text, catalog_tuple, coating_tuple, project.temperature, project.pressure,
                        configuration)

    if state["failure"]:
        st.error(state["failure"])
        st.stop()
    for message in state["warnings"]:
        st.warning(message)
    if state["errors"]:
        st.error("Das System ist nicht konsistent:\n\n" + "\n\n".join(f"- {m}" for m in state["errors"]))
        st.stop()

    system, comp, lib = state["system"], state["compiled"], state["library"]
    if comp is None:
        st.stop()
    if FEATURES.glasses:
        ss.glass_options = [g.reference for cat in lib.catalogs() for g in lib.glasses(cat)][:3000]

    config_name = getattr(comp, "configuration_name", "")
    st.subheader((system.name or "System") + (f" – Konfiguration {config_name}" if config_name else ""))
    paths = list(comp.path_names)
    path_choice = paths[0] if len(paths) == 1 else st.sidebar.selectbox("Pfad", paths)
    wl_um = list(comp.wavelengths_um)
    ref_wl = comp.reference_wavelength

    ctx = AppContext(
        features=FEATURES, system=system, comp=comp, lib=lib, system_dict=system_dict,
        path_choice=path_choice, first_order=first_order(comp, path_choice),
        can_aim=_can_aim(comp, path_choice, ref_wl), candidates=candidates, named=named,
        builder_context=builder_context, coatings=state["coatings"], configuration=configuration,
        # The libraries are cached resources: their id stands for the catalogue contents.
        system_key=repr((json_text, id(lib), id(state["coatings"]), project.temperature, project.pressure,
                         configuration)),
        wl_um=wl_um, ref_wl=ref_wl,
        field_ids=list(range(comp.field_count)), wl_ids=list(range(len(wl_um))))
    render_header(ctx)

    view = st.radio("Analyse", list(VIEWS), horizontal=True)
    VIEWS[view](ctx)
