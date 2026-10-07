"""Build libraries and compile systems; results are cached per input.

Errors never escape as exceptions: ``make_system`` returns them as text in the result dictionary.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import raytatouille as rt
import streamlit as st

from .compat import FEATURES


@st.cache_resource(show_spinner=False)
def make_library(catalogs: tuple[tuple[str, bytes], ...]):
    """MaterialLibrary from (name in the system, AGF bytes)."""
    lib = rt.MaterialLibrary()
    tmp = Path(tempfile.mkdtemp(prefix="rtt_agf_"))
    for name, data in catalogs:
        if FEATURES.alias:
            lib.add_catalog_text(data, name)
        else:
            path = tmp / f"{name.lower()}.agf"
            path.write_bytes(data)
            lib.add_catalog(path)
    return lib


@st.cache_resource(show_spinner=False)
def make_coatings(coatings: tuple[tuple[str, bytes], ...]):
    lib = rt.CoatingLibrary()
    tmp = Path(tempfile.mkdtemp(prefix="rtt_coat_"))
    for i, (fname, data) in enumerate(coatings):
        path = tmp / f"{i}_{fname}"
        path.write_bytes(data)
        lib.add_catalog(path)
    return lib


@st.cache_resource(show_spinner=False)
def make_system(json_text: str, catalogs: tuple[tuple[str, bytes], ...],
                coatings: tuple[tuple[str, bytes], ...],
                temperature_c: float | None, pressure_atm: float | None):
    """Parse, validate and compile; errors come back as text, never as exceptions."""
    result = {"system": None, "compiled": None, "library": None, "errors": [], "warnings": [],
              "failure": None}
    try:
        result["library"] = make_library(catalogs)
        coating_lib = make_coatings(coatings) if (FEATURES.coatings and coatings) else None
        system = rt.System.from_json(json_text)
        if temperature_c is not None or pressure_atm is not None:
            env = system.environment
            if temperature_c is not None:
                env.temperature_c = temperature_c
            if pressure_atm is not None:
                env.pressure_atm = pressure_atm
            system.environment = env
        result["system"] = system
        for d in rt.validate(system):
            (result["errors"] if d.severity == rt.Severity.ERROR else result["warnings"]).append(str(d))
        if not result["errors"]:
            if coating_lib is not None:
                result["compiled"] = rt.compile(system, result["library"], coating_lib)
            else:
                result["compiled"] = rt.compile(system, result["library"])
    except (rt.RaytatouilleError, ValueError, OSError) as error:
        result["failure"] = str(error)
    return result
