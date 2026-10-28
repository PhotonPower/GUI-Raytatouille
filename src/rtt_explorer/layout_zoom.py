"""Zoom windows for the layout drawing (pure logic, numpy only, no Streamlit, no library).

A window is ``(z_min, z_max, lateral_min, lateral_max)`` in mm: z horizontal, the lateral
coordinate (y in the yz section, x in the xz section) vertical.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

Window = tuple[float, float, float, float]


def checked_window(z_min: float, z_max: float, lat_min: float, lat_max: float) -> Window:
    """The window as floats; ``ValueError`` if a bound is not finite or a range is empty or reversed."""
    window = (float(z_min), float(z_max), float(lat_min), float(lat_max))
    if not all(math.isfinite(v) for v in window):
        raise ValueError("Ausschnitt: alle Grenzen müssen endliche Zahlen sein")
    if not (window[1] > window[0] and window[3] > window[2]):
        raise ValueError("Ausschnitt leer: es muss z von < z bis und unten < oben gelten")
    return window


def source_window(source_z: float, source_lat: float, half_width: float, aspect: float = 3.0) -> Window:
    """Window centred on the source: width ``2 * half_width`` in z, height ``width / aspect``.

    ``aspect`` is width over height of the window; the height is derived so that a source on the
    axis does not vanish in a thin strip. ``ValueError`` for a non-positive or non-finite size."""
    if not (math.isfinite(half_width) and half_width > 0.0):
        raise ValueError("Quellfenster: die halbe Breite muss größer als 0 sein")
    if not (math.isfinite(aspect) and aspect > 0.0):
        raise ValueError("Quellfenster: das Seitenverhältnis muss größer als 0 sein")
    half_height = half_width / aspect
    return (source_z - half_width, source_z + half_width, source_lat - half_height, source_lat + half_height)


def fit_aspect(window: Window, aspect: float) -> Window:
    """Widen the window around its centre to width over height ``aspect``; it is never reduced.

    For equal axis scaling: ``aspect`` is the width over the height of the axes box in the figure, so
    the drawing keeps equal scales and shows the complete window. ``ValueError`` for an empty window
    or a non-positive aspect."""
    z_min, z_max, lat_min, lat_max = checked_window(*window)
    if not (math.isfinite(aspect) and aspect > 0.0):
        raise ValueError("Seitenverhältnis: muss größer als 0 sein")
    width, height = z_max - z_min, lat_max - lat_min
    if width / height < aspect:
        extra = (height * aspect - width) / 2.0
        return (z_min - extra, z_max + extra, lat_min, lat_max)
    extra = (width / aspect - height) / 2.0
    return (z_min, z_max, lat_min - extra, lat_max + extra)


def source_point(positions: Sequence[np.ndarray], lat: int) -> tuple[float, float] | None:
    """Mean start point ``(z, lateral)`` of all rays; ``None`` if no ray has a finite start.

    ``positions`` holds the recorded positions of the bundles, each ``(rays, points, 3)`` in global
    (x, y, z); the first point of a ray is its start. ``lat`` is the lateral index (1 for yz, 0 for xz)."""
    starts = [np.asarray(p, dtype=float)[:, 0, :] for p in positions if np.size(p)]
    if not starts:
        return None
    start = np.vstack(starts)
    start = start[np.isfinite(start[:, [2, lat]]).all(axis=1)]
    if not len(start):
        return None
    return float(start[:, 2].mean()), float(start[:, lat].mean())


def image_plane_z(bundles: Sequence[tuple[np.ndarray, np.ndarray]]) -> float | None:
    """Mean z of the end points of the rays that arrived; ``None`` if no ray has a finite end.

    ``bundles`` holds ``(position, lost_at)`` per bundle: the recorded positions ``(rays, points, 3)``
    in global (x, y, z) and the event index where a ray was lost (``-1`` if it was not). The last
    point of a ray is its final state; lost rays are skipped, so a bundle that is blocked completely
    gives no image plane instead of NaN."""
    ends = []
    for position, lost_at in bundles:
        position, lost_at = np.asarray(position, dtype=float), np.asarray(lost_at)
        if position.ndim != 3 or not len(position):
            continue
        z = position[:, -1, 2][lost_at < 0]
        ends.append(z[np.isfinite(z)])
    if not ends:
        return None
    z = np.concatenate(ends)
    return float(z.mean()) if z.size else None


def image_window(z_img: float, width: float, z_parts: Sequence[np.ndarray], lat_parts: Sequence[np.ndarray],
                 fallback: tuple[float, float]) -> Window:
    """Window in front of the image plane: from ``z_img - width`` to ``z_img + 0.1 * width``.

    The lateral range is symmetric, 1.2 times the largest ray height inside the window (at least
    1e-3 mm); non-finite points are ignored. Without a ray in the window it is ``fallback``.
    ``ValueError`` for a non-finite plane or a non-positive width."""
    if not math.isfinite(z_img):
        raise ValueError("Bildebene: z ist nicht endlich")
    if not (math.isfinite(width) and width > 0.0):
        raise ValueError("Bildfenster: die Breite muss größer als 0 sein")
    z_min, z_max = z_img - width, z_img + 0.1 * width
    lat_max = 0.0
    found = False
    for z, lat in zip(z_parts, lat_parts):
        z, lat = np.asarray(z, dtype=float), np.asarray(lat, dtype=float)
        inside = np.isfinite(z) & np.isfinite(lat) & (z >= z_min) & (z <= z_max)
        if inside.any():
            found = True
            lat_max = max(lat_max, float(np.abs(lat[inside]).max()))
    if not found:
        return (z_min, z_max, float(fallback[0]), float(fallback[1]))
    span = max(1.2 * lat_max, 1e-3)
    return (z_min, z_max, -span, span)
