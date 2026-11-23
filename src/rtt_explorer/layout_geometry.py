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


def truncate_lost(position, lost_at) -> np.ndarray:
    """Copy of the recorded positions in which a lost ray ends at its last valid surface.

    ``position`` is ``(rays, slots, 3)`` as recorded by the library: slot 0 is the start and slot
    k + 1 the point after event k. A ray lost at event j has the point where it met the surface
    that lost it in slot j + 1, which can lie far from any real surface (the extension of a mirror,
    a plane beyond its aperture). Slots j + 1 and later become NaN, so the ray is drawn up to slot
    j, the last surface it reached. Rays that were not lost (``lost_at < 0``) stay as they are.
    ``ValueError`` unless ``position`` has three dimensions."""
    position = np.array(position, dtype=float)
    if position.ndim != 3:
        raise ValueError("Positionen: erwartet (Strahlen, Punkte, 3)")
    lost_at = np.asarray(lost_at)
    for i in np.nonzero(lost_at >= 0)[0]:
        position[i, int(lost_at[i]) + 1:, :] = np.nan
    return position


def loss_slots(lost_at, truncated: bool) -> np.ndarray:
    """Slot of the loss marker for rays lost at the events ``lost_at`` (all >= 0).

    The point the library recorded for the loss (slot j + 1), or, for truncated rays, the last
    valid surface (slot j)."""
    slots = np.asarray(lost_at, dtype=int)
    return slots if truncated else slots + 1


def first_boundary(kinds) -> int | None:
    """Index of the first event of a path that is not a stop: the first interface of the system.

    ``kinds`` are the kinds of the surfaces of the events (``raytatouille.layout`` kinds such as
    "stop", "lens", "mirror", "thin_element", "detector"). A stop does not change the medium, so
    the object space reaches the first other surface; None if there is none."""
    for k, kind in enumerate(kinds):
        if kind != "stop":
            return k
    return None


def object_space_polygon(z_source: float, profile, half_height: float | None = None) -> np.ndarray:
    """Outline of the object space: from the source plane to the first interface, (z, lateral).

    ``profile`` is ``(k, 2)`` points (z, lateral) of the interface surface. The polygon runs from
    the top of the source plane along the profile (top to bottom) to the bottom of the source
    plane; ``half_height`` is the height of the source plane (default: the largest lateral
    coordinate of the profile). ``ValueError`` for an empty, non-finite or wrongly shaped profile,
    or a source plane that is not in front of the whole profile."""
    profile = np.asarray(profile, dtype=float)
    if profile.ndim != 2 or profile.shape[1] != 2 or not len(profile) or not np.isfinite(profile).all():
        raise ValueError("Objektraum: das Profil muss endliche (z, lateral)-Punkte enthalten")
    if z_source >= float(profile[:, 0].min()):
        raise ValueError("Objektraum: die Quelle muss vor der ersten Fläche liegen")
    height = float(np.abs(profile[:, 1]).max()) if half_height is None else float(half_height)
    ordered = profile[np.argsort(-profile[:, 1], kind="stable")]
    return np.vstack([[z_source, height], ordered, [z_source, -height]])


def _section_axes(plane: str) -> tuple[int, int]:
    """(index of the coordinate that is 0 on the section line, index of the lateral coordinate) in local (x, y).

    The section "yz" cuts along the local y axis at x = 0, "xz" along the local x axis at y = 0."""
    return (0, 1) if plane == "yz" else (1, 0)


def polygon_section_intervals(vertices, plane: str) -> list[tuple[float, float]]:
    """Intervals ``(lo, hi)`` of the lateral coordinate where the section line through the axis lies inside a polygon.

    ``vertices`` is ``SurfaceLayout.aperture_vertices`` ((n, 2) in mm, local frame). The line is x = 0 for the
    section "yz" and y = 0 for "xz"; the result follows the even-odd rule, so a concave polygon can give several
    intervals, and an empty list means the line misses the polygon. ``ValueError`` for fewer than 3 vertices."""
    pts = np.asarray(vertices, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) < 3:
        raise ValueError("Ein Polygon braucht mindestens 3 Eckpunkte")
    u, v = _section_axes(plane)
    crossings = []
    for a, b in zip(pts, np.roll(pts, -1, axis=0)):
        # half-open rule: a vertex on the line counts for exactly one of its two edges
        if (a[u] <= 0.0 < b[u]) or (b[u] <= 0.0 < a[u]):
            crossings.append(float(a[v] + (b[v] - a[v]) * (0.0 - a[u]) / (b[u] - a[u])))
    crossings.sort()
    return [(crossings[k], crossings[k + 1]) for k in range(0, len(crossings) - 1, 2)]


def obscuration_intervals(kind: str, params: dict, plane: str) -> list[tuple[float, float]]:
    """Intervals ``(lo, hi)`` of the lateral coordinate where the section line is inside an obscuration.

    ``kind`` and ``params`` are an entry of ``SurfaceLayout.obscurations``: "circular" (radius), "rectangular"
    (half_width_x, half_width_y, rotation_deg) or "elliptical" (semi_axis_x, semi_axis_y, rotation_deg), each with
    decenter_x and decenter_y in the local frame; the rotation turns the axes of the shape from +x towards +y.
    Empty if the line misses the shape; ``ValueError`` for another kind."""
    if kind not in ("circular", "rectangular", "elliptical"):
        raise ValueError(f"Obskuration vom Typ „{kind}“ ist unbekannt")
    cx, cy = float(params.get("decenter_x", 0.0)), float(params.get("decenter_y", 0.0))
    theta = math.radians(float(params.get("rotation_deg", 0.0)))
    cos, sin = math.cos(theta), math.sin(theta)

    def to_shape(px: float, py: float) -> tuple[float, float]:
        """Rotate a vector by -theta into the frame of the shape."""
        return cos * px + sin * py, -sin * px + cos * py

    u, v = _section_axes(plane)
    direction = [0.0, 0.0]
    direction[v] = 1.0
    ax, ay = to_shape(-cx, -cy)  # the line passes through the local origin: point of the line at t = 0
    bx, by = to_shape(*direction)
    if kind == "rectangular":
        lo, hi = -math.inf, math.inf
        for a, b, half in ((ax, bx, float(params["half_width_x"])), (ay, by, float(params["half_width_y"]))):
            if abs(b) < 1e-12:
                if abs(a) > half:
                    return []
                continue
            t0, t1 = sorted(((-half - a) / b, (half - a) / b))
            lo, hi = max(lo, t0), min(hi, t1)
        return [(lo, hi)] if lo < hi else []
    if kind == "circular":
        sx = sy = float(params["radius"])
    else:
        sx, sy = float(params["semi_axis_x"]), float(params["semi_axis_y"])
    alpha = bx * bx / (sx * sx) + by * by / (sy * sy)
    beta = ax * bx / (sx * sx) + ay * by / (sy * sy)
    gamma = ax * ax / (sx * sx) + ay * ay / (sy * sy) - 1.0
    disc = beta * beta - alpha * gamma
    if disc <= 0.0:
        return []
    root = math.sqrt(disc)
    return [((-beta - root) / alpha, (-beta + root) / alpha)]
