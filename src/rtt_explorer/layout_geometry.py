"""Geometry for the layout drawing (pure logic, numpy only, no Streamlit, no library).

Positions are global (x, y, z) in mm. A rotation matrix holds the local axes of a surface as its
columns, as in ``raytatouille.layout.SurfaceLayout.rotation``.
"""

from __future__ import annotations

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
