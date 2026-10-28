"""Rays of the detector image: many rays traced to the image surface (library, no Streamlit)."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import raytatouille as rt

from .detector_image import emission_weights, sunflower_points


@dataclass(frozen=True)
class Hits:
    """Where the rays of a path meet the image surface.

    ``x``, ``y`` are in mm in the local coordinates of the image surface, ``weight`` is the power of
    each arrived ray (transmission of the path, times the emission weight if ``isotropic``)."""

    x: np.ndarray
    y: np.ndarray
    weight: np.ndarray
    launched: int
    arrived: int
    image_surface: str
    isotropic: bool  # the emission weights of an isotropic point source were applied


def _hexapolar_rings(n: int) -> int:
    """Rings of a hexapolar pupil with at least ``n`` rays (1 + 3 k (k + 1) rays for k rings)."""
    return max(1, math.ceil((-3.0 + math.sqrt(9.0 + 12.0 * (n - 1))) / 6.0))


def _path_events(comp, path: str, field: int, wavelength: int, aiming):
    """Event surfaces of the path, from a recorded single ray (the full bundle is not recorded)."""
    probe = rt.trace.make_rays(comp, rt.trace.HexapolarPupil(rings=1), path=path, fields=[field],
                               wavelength=wavelength, aiming=aiming)
    _, recorded = rt.trace.trace(comp, probe, path=path, record_path=True)
    return [int(i) for i in np.asarray(recorded.event_surfaces)]


def compute_hits(comp, path: str, field: int, wavelength: int, n_rays: int, aiming, isotropic: bool,
                 point_list: bool = True) -> Hits:
    """Trace about ``n_rays`` rays of ``field`` at ``wavelength`` and collect their hits.

    The pupil points are uniform in area (sunflower spiral through ``PointListPupil``; hexapolar
    rings if the library has no point list). With ``isotropic`` and a point source (all rays start at
    one point) the rays are weighted by cos^3 of the angle to the normal of the stop, so that the
    power per solid angle is the same in every direction (``emission_weights``); otherwise every ray
    has the weight of the transmission only. ``ValueError`` if no ray reaches the image surface."""
    if point_list and hasattr(rt.trace, "PointListPupil"):
        px, py = sunflower_points(n_rays)
        sampling = rt.trace.PointListPupil(px, py)
    else:
        sampling = rt.trace.HexapolarPupil(rings=_hexapolar_rings(n_rays))
    rays = rt.trace.make_rays(comp, sampling, path=path, fields=[field], wavelength=wavelength, aiming=aiming)
    launched = int(rays.size)

    events = _path_events(comp, path, field, wavelength, aiming)
    surfaces = rt.layout.surfaces(comp) if hasattr(rt, "layout") else None
    image = events[-1]

    # Start data before the trace (the trace updates the batch in place).
    emit = np.ones(launched)
    start = np.column_stack([np.asarray(rays.pos_x), np.asarray(rays.pos_y), np.asarray(rays.pos_z)])
    point_source = bool(np.all(np.ptp(start, axis=0) < 1e-12))
    applied = False
    if isotropic and point_source and surfaces is not None:
        stop = next((i for i in events if surfaces[i].kind == "stop"), None)
        if stop is not None:
            direction = np.column_stack([np.asarray(rays.dir_x), np.asarray(rays.dir_y), np.asarray(rays.dir_z)])
            emit = emission_weights(direction @ np.asarray(surfaces[stop].rotation)[:, 2])
            applied = True

    rt.trace.trace(comp, rays, path=path)
    arrived = (np.asarray(rays.status) == int(rt.trace.RayStatus.ALIVE)) & (np.asarray(rays.last_surface) == image)
    if not arrived.any():
        raise ValueError("Kein Strahl erreicht die Bildfläche (Pfad „" + path + "“).")
    points = np.column_stack([np.asarray(rays.pos_x), np.asarray(rays.pos_y), np.asarray(rays.pos_z)])[arrived]
    if surfaces is not None:
        points = (points - np.asarray(surfaces[image].translation)) @ np.asarray(surfaces[image].rotation)
    weight = (np.asarray(rays.weight) * emit)[arrived]
    return Hits(points[:, 0].copy(), points[:, 1].copy(), weight, launched, int(arrived.sum()),
                comp.surface_ids[image], applied)
