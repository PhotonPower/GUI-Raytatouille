"""Rays and irradiance maps on a surface of a path (library, no Streamlit)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import raytatouille as rt

from .detector_image import Extent, image_extent, sunflower_points
from .irradiance_logic import MAX_BATCH_RAYS, MAX_PATH_RAYS, max_rays


@dataclass(frozen=True)
class Traced:
    """Rays traced for an irradiance map.

    ``form`` is "paths" (recorded, ``data`` a RayPaths, any surface of the path, up to ``MAX_PATH_RAYS``) or
    "batch" (``data`` the RayBatch, only the last surface of the path, up to ``MAX_BATCH_RAYS``)."""

    data: object
    form: str
    path: str
    wavelength: int
    launched: int
    alive: int  # rays that ended with status ALIVE
    pupil: tuple[np.ndarray, np.ndarray]


def path_events(comp, path: str, field: int, wavelength: int, aiming) -> list[int]:
    """Surface index of every event of the path, from one recorded ray (the whole bundle is not recorded)."""
    probe = rt.trace.make_rays(comp, rt.trace.HexapolarPupil(rings=1), path=path, fields=[field],
                               wavelength=wavelength, aiming=aiming)
    _, recorded = rt.trace.trace(comp, probe, path=path, record_path=True)
    return [int(i) for i in np.asarray(recorded.event_surfaces)]


def trace_rays(comp, path: str, field: int, wavelength: int, n_rays: int, aiming, surface: int) -> Traced:
    """Trace about ``n_rays`` rays (pupil points uniform in area) of ``field`` along ``path``.

    Up to ``MAX_PATH_RAYS`` rays are recorded, which serves every surface and event of the path. More rays only
    go for the last surface of the path, without recording. ``ValueError`` (German) if the surface is not on the
    path or the number is too large for it."""
    events = path_events(comp, path, field, wavelength, aiming)
    if surface not in events:
        raise ValueError(f"Die Fläche „{comp.surface_ids[surface]}“ liegt nicht auf dem Pfad „{path}“.")
    is_last = events[-1] == surface
    if n_rays > max_rays(is_last):
        raise ValueError(f"Für diese Fläche sind höchstens {max_rays(is_last):,} Strahlen möglich".replace(",", " ")
                         + ("" if is_last else f"; die letzte Fläche des Pfads erlaubt {MAX_BATCH_RAYS:,}"
                            .replace(",", " ")) + ".")
    px, py = sunflower_points(n_rays)
    rays = rt.trace.make_rays(comp, rt.trace.PointListPupil(px, py), path=path, fields=[field],
                              wavelength=wavelength, aiming=aiming)
    if n_rays <= MAX_PATH_RAYS:
        _, data = rt.trace.trace(comp, rays, path=path, record_path=True, max_recorded_rays=MAX_PATH_RAYS)
        form = "paths"
    else:
        rt.trace.trace(comp, rays, path=path)
        data, form = rays, "batch"
    alive = int((np.asarray(rays.status) == int(rt.trace.RayStatus.ALIVE)).sum())
    return Traced(data, form, path, wavelength, int(rays.size), alive, (px, py))


def local_hits(comp, traced: Traced, surface: int, event: int | None) -> tuple[np.ndarray, np.ndarray]:
    """(x, y) in mm in the local frame of the surface of the finite hits (of one event, or of all at the surface)."""
    sf = rt.layout.surfaces(comp)[surface]
    if traced.form == "batch":
        data = traced.data
        alive = np.asarray(data.status) == int(rt.trace.RayStatus.ALIVE)
        points = np.column_stack([np.asarray(data.pos_x), np.asarray(data.pos_y), np.asarray(data.pos_z)])[alive]
    else:
        position = np.asarray(traced.data.position)
        surfaces = np.asarray(traced.data.event_surfaces)
        chosen = [k for k, s in enumerate(surfaces) if int(s) == surface and (event is None or k == event)]
        points = np.concatenate([position[:, k + 1, :] for k in chosen]) if chosen else np.empty((0, 3))
    points = points[np.isfinite(points).all(axis=1)]
    local = (points - np.asarray(sf.translation)) @ np.asarray(sf.rotation)
    return local[:, 0].copy(), local[:, 1].copy()


def auto_extent(comp, traced: Traced, surface: int, event: int | None) -> Extent:
    """Rectangle around the hits with a margin; ``ValueError`` (German) if no ray hits the surface."""
    x, y = local_hits(comp, traced, surface, event)
    if not x.size:
        raise ValueError("Kein Strahl erreicht diese Fläche.")
    return image_extent(x, y)


def irradiance_extent(comp, surface: int, mode: str, manual: Extent | None, auto: Extent | None) -> Extent | None:
    """The ``extent`` for the library: None for the aperture of the surface, the hits' rectangle or a manual one."""
    if mode == "aperture":
        if rt.layout.surfaces(comp)[surface].aperture is None:
            raise ValueError("Diese Fläche hat keine Apertur: den Bereich aus den Strahlen oder frei wählen.")
        return None
    return manual if mode == "manual" else auto


def irradiance(comp, traced: Traced, surface: int, event: int | None, nx: int, ny: int, extent: Extent | None):
    """The irradiance map of the library for ``surface`` (all its events, or one by its number in the path)."""
    if traced.form == "batch":
        return rt.analysis.irradiance_map(comp, traced.data, path=traced.path, nx=nx, ny=ny, extent=extent)
    return rt.analysis.irradiance_map(comp, traced.data, surface=comp.surface_ids[surface], path=traced.path,
                                      nx=nx, ny=ny, extent=extent, event=event, wavelength=traced.wavelength)
