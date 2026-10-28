"""Geometry for the layout drawing (pure logic, numpy only, no Streamlit, no library).

Positions are global (x, y, z) in mm. A rotation matrix holds the local axes of a surface as its
columns, as in ``raytatouille.layout.SurfaceLayout.rotation``.
"""

from __future__ import annotations

import math

import numpy as np

# Normal of the drawing plane and the index of its lateral coordinate
SECTION = {"yz": (np.array([1.0, 0.0, 0.0]), 1), "xz": (np.array([0.0, 1.0, 0.0]), 0)}


def plane_segment(translation, rotation, plane: str, lo: float, hi: float) -> tuple[np.ndarray, np.ndarray]:
    """(z, lateral) of the two points at distance lo and hi from the vertex of a planar surface.

    The segment runs along the cut of the surface plane with the drawing plane, so a stop or a
    detector keeps its position and tilt. If the surface lies in the drawing plane (no cut), the
    local lateral axis is used."""
    normal, col = SECTION[plane]
    rotation = np.asarray(rotation, dtype=float)
    local_lateral = rotation[:, col]
    direction = np.cross(rotation[:, 2], normal)
    length = float(np.linalg.norm(direction))
    if length < 1e-9:
        direction = local_lateral
    else:
        direction = direction / length
        if float(direction @ local_lateral) < 0.0:
            direction = -direction
    points = np.asarray(translation, dtype=float) + np.outer([lo, hi], direction)
    return points[:, 2], points[:, col]


def exit_segments(position, direction, lost_at, length: float) -> tuple[np.ndarray, np.ndarray]:
    """(start, end) points, each (k, 3), of the rays continued beyond the last event of a path.

    A recorded path holds the start point and one point per event, so a ray leaving the last
    surface (a mirror, a total internal reflection) has no further point. The stub follows the
    direction after the last event; lost rays and rays without a finite end are skipped."""
    position = np.asarray(position, dtype=float)
    direction = np.asarray(direction, dtype=float)
    if position.ndim != 3 or position.shape[1] < 2:
        return np.empty((0, 3)), np.empty((0, 3))
    end, vec = position[:, -1, :], direction[:, -1, :]
    ok = (np.asarray(lost_at) < 0) & np.isfinite(end).all(axis=1) & np.isfinite(vec).all(axis=1)
    return end[ok], end[ok] + length * vec[ok]


def stub_length(z_parts, lateral_parts, fraction: float = 0.3) -> float:
    """Length of the exit stubs: a fraction of the larger extent of the drawn rays (at least 1 mm)."""
    extent = 1.0
    if len(z_parts):
        z, lateral = np.concatenate(z_parts), np.concatenate(lateral_parts)
        if z.size:
            extent = max(extent, float(np.ptp(z)), float(np.ptp(lateral)))
    return fraction * extent


def inner_radius(aperture) -> float:
    """Inner radius in mm of a circular aperture ``(kind, parameters)``; 0 for no or another aperture.

    ``aperture`` is ``raytatouille.layout.SurfaceLayout.aperture`` (``None`` without aperture)."""
    if aperture is None:
        return 0.0
    kind, params = aperture
    return float(params.get("inner_radius", 0.0)) if kind == "circular" else 0.0


def aperture_bands(inner: float, outer: float, jaw: float = 1.4) -> tuple[list[tuple[float, float]],
                                                                         list[tuple[float, float]]]:
    """(blocked, open) bands ``(lo, hi)`` of the lateral coordinate of a stop-like aperture, in mm.

    The aperture lets light pass between ``inner`` and ``outer`` from the axis. Blocked are the
    central disc (if ``inner > 0``) and the jaws outside, drawn up to ``jaw * outer``. Open are the
    ring parts, one band across the diameter without a hole. ``ValueError`` unless
    ``0 <= inner < outer`` (finite)."""
    if not (math.isfinite(inner) and math.isfinite(outer) and 0.0 <= inner < outer):
        raise ValueError("Apertur: es muss 0 <= Innenradius < Außenradius gelten")
    edge = jaw * outer
    blocked = [(-inner, inner)] if inner > 0.0 else []
    blocked += [(outer, edge), (-edge, -outer)]
    free = [(inner, outer), (-outer, -inner)] if inner > 0.0 else [(-outer, outer)]
    return blocked, free
