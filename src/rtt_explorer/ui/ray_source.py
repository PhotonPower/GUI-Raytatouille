"""Ray source selection: pupil and fields (needs a stop) or a free collimated beam."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import raytatouille as rt
import streamlit as st

from ..compat import FEATURES
from ..rays import collimated_batch

if TYPE_CHECKING:
    from ..context import AppContext


def source_ui(ctx: AppContext, key: str) -> dict:
    """Ray source: pupil/fields (needs a stop) or a free collimated beam (any system)."""
    can_aim = ctx.can_aim
    comp = ctx.comp
    system_dict_for_refs = ctx.system_dict
    options = ["Pupille und Felder (braucht Blende)", "Kollimiertes Bündel (frei)"]
    choice = st.radio("Strahlquelle", options, index=0 if can_aim else 1, horizontal=True,
                      key=f"src_{key}_{can_aim}")
    if choice == options[0]:
        if not can_aim:
            st.warning("Dieses System hat keine Blende, die Pupille lässt sich nicht anzielen. "
                       "Nimm das freie Bündel.")
        return {"free": False}
    z_default = -10.0
    if FEATURES.layout:
        z_default = float(min(float(sf.translation[2]) for sf in rt.layout.surfaces(comp))) - 10.0
    aperture = system_dict_for_refs.get("aperture", {})
    r_default = float(aperture.get("value", 10.0)) / 2 if aperture.get("type") == "epd" else 5.0
    a, b, c, d = st.columns(4)
    radius = a.number_input("Bündelradius (mm)", min_value=0.01, value=r_default, key=f"src_r_{key}")
    z0 = b.number_input("Startebene z (mm)", value=z_default, key=f"src_z_{key}")
    tx = c.number_input("Neigung um x (°)", value=0.0, step=1.0, key=f"src_tx_{key}")
    ty = d.number_input("Neigung um y (°)", value=0.0, step=1.0, key=f"src_ty_{key}")
    return {"free": True, "radius": radius, "z0": z0, "tx": tx, "ty": ty}


def make_batch(ctx: AppContext, src: dict, kind: str, n: int, plane: str, field: int, wl: int, aim):
    """(rays, start x or pupil x, start y or pupil y) for the chosen source."""
    if src["free"]:
        batch = collimated_batch(kind, n, plane, src["radius"], src["z0"], src["tx"], src["ty"], wl)
        return batch, np.array(batch.pos_x), np.array(batch.pos_y)
    if kind == "Fächer":
        sampling = rt.trace.FanYPupil(n=n) if plane == "yz" else rt.trace.FanXPupil(n=n)
    else:
        sampling = rt.trace.HexapolarPupil(rings=n)
    batch = rt.trace.make_rays(ctx.comp, sampling, path=ctx.path_choice, fields=[field], wavelength=wl,
                               aiming=aim)
    return batch, np.array(batch.pupil_x), np.array(batch.pupil_y)
