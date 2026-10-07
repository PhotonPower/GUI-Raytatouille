"""Layout drawing: lenses, mirrors, stops and detector with ``raytatouille.layout``."""

from __future__ import annotations

import math

import numpy as np
import raytatouille as rt
from matplotlib.patches import Polygon

from .builder import AIR_WORDS, is_air


def aperture_extent(surface, plane: str) -> float | None:
    """Half-extent of the aperture along the section direction, mm (None: no aperture)."""
    if surface.aperture is None:
        return None
    typ, p = surface.aperture
    if typ == "circular":
        return float(p["radius"])
    key = {"rectangular": ("half_width_y", "half_width_x"),
           "elliptical": ("semi_axis_y", "semi_axis_x")}.get(typ)
    return float(p[key[0 if plane == "yz" else 1]]) if key else None


def surface_extents(surfs, bundles) -> dict[int, float]:
    """Largest ray distance from the local axis per surface index (from recorded paths)."""
    est: dict[int, float] = {}
    for paths in bundles:
        pos = np.asarray(paths.position)
        events = np.asarray(paths.event_surfaces)
        for k, s_idx in enumerate(events):
            p = pos[:, k + 1, :]
            ok = np.isfinite(p).all(axis=1)
            if not ok.any():
                continue
            sf = surfs[int(s_idx)]
            local = (p[ok] - sf.translation) @ sf.rotation
            est[int(s_idx)] = max(est.get(int(s_idx), 0.0), float(np.hypot(local[:, 0], local[:, 1]).max()))
    return est


def draw_geometry_api(ax, comp, plane: str, est: dict[int, float], default_h: float,
                      label_surfaces: bool) -> None:
    """Draw lenses, mirrors, stops and detector with raytatouille.layout.

    Elements with unbounded surfaces (no aperture) are drawn from sag values with a height
    estimated from the traced rays, since the library has no profile for them."""
    lay = rt.layout
    surfs = lay.surfaces(comp)
    elements = lay.elements(comp)
    col = 1 if plane == "yz" else 0

    def height(i: int) -> float:
        a = aperture_extent(surfs[i], plane)
        if a is not None:
            return a
        return est[i] * 1.15 + 0.5 if i in est else default_h

    def own_profile(i: int, n: int = 101):
        h = height(i)
        t = np.linspace(-h, h, n)
        x, y = (np.zeros(n), t) if plane == "yz" else (t, np.zeros(n))
        z = lay.sag(comp, i, x, y)
        local = np.column_stack([x, y, z])[np.isfinite(z)]
        return local @ surfs[i].rotation.T + surfs[i].translation

    def profile_lines(i: int):
        # Without aperture the library cuts a surface at the domain of its shape (the whole
        # hemisphere of a sphere): use the height estimated from the rays instead.
        if surfs[i].aperture is None:
            return [own_profile(i)]
        try:
            return lay.profile(comp, i, plane, 101)
        except ValueError:
            return [own_profile(i)]

    def is_glass(medium: int) -> bool:
        return comp.media[medium].reference.strip().upper() not in AIR_WORDS

    for ei, el in enumerate(elements):
        idx = list(range(el.first_surface, el.first_surface + el.surface_count))
        polygons: list[np.ndarray] = []
        bounded = all(surfs[i].aperture is not None for i in idx)
        try:
            if bounded:
                polygons = list(lay.outlines(comp, ei, plane, 101))
        except ValueError:
            bounded = False
        if not bounded and (el.kind == "lens" or el.segmented):
            for k in idx[:-1]:
                if is_glass(surfs[k].medium_back):
                    a, b = profile_lines(k)[0], profile_lines(k + 1)[0]
                    polygons.append(np.vstack([a, b[::-1], a[:1]]))
        for poly in polygons:
            ax.add_patch(Polygon(np.column_stack([poly[:, 2], poly[:, col]]), closed=True,
                                 alpha=0.35, fc="tab:blue", ec="k", lw=1.0))
        if polygons:
            continue
        for i in idx:
            sf = surfs[i]
            z = float(sf.translation[2])
            if sf.kind == "stop":
                r = aperture_extent(sf, plane) or default_h
                for sign in (1, -1):
                    ax.plot([z, z], [sign * r, sign * 1.4 * r], "k-", lw=3)
            elif sf.kind == "detector":
                h = (aperture_extent(sf, plane) or (est[i] * 1.2 + 0.5 if i in est else default_h))
                ax.plot([z, z], [-h, h], "-", color="tab:red", lw=2)
            else:
                for line in profile_lines(i):
                    ax.plot(line[:, 2], line[:, col], "-", color="k", lw=1.6)
    if label_surfaces:
        for i, sf in enumerate(surfs):
            ax.annotate(comp.surface_ids[i], (float(sf.translation[2]), height(i)), fontsize=7,
                        xytext=(0, 4), textcoords="offset points", ha="center", color="gray")


def draw_builder_sketch(rows: list[dict], epd: float, ax) -> None:
    """Fallback without raytatouille.layout: lens section from the builder table."""
    default_h = 0.6 * epd
    heights = [r["sd"] if r["sd"] > 0 else default_h for r in rows]

    def profile(row, h):
        c = 1.0 / row["radius"] if row["radius"] else 0.0
        k = row["conic"]
        if c and (1 + k) > 0:
            h = min(h, 0.999 * math.sqrt(1.0 / ((1 + k) * c * c)))
        y = np.linspace(-h, h, 60)
        if not c:
            return row["z"] + 0 * y, y
        sag = c * y**2 / (1 + np.sqrt(1 - (1 + k) * c * c * y**2))
        return row["z"] + sag, y

    for idx in range(len(rows) - 1):
        a, b = rows[idx], rows[idx + 1]
        if a["typ"] == "Fläche" and b["typ"] == "Fläche" and not is_air(a["mat"]):
            za, ya = profile(a, heights[idx])
            zb, yb = profile(b, heights[idx + 1])
            ax.add_patch(Polygon(np.column_stack([np.r_[za, zb[::-1]], np.r_[ya, yb[::-1]]]),
                                 closed=True, alpha=0.35, ec="k", lw=1.0))
    for idx, r in enumerate(rows):
        if r["typ"] == "Blende":
            h = heights[idx]
            for sign in (1, -1):
                ax.plot([r["z"], r["z"]], [sign * h, sign * 1.5 * h], "k-", lw=3)
        if r["typ"] == "Bild":
            ax.plot([r["z"], r["z"]], [-default_h, default_h], "-", color="tab:red", lw=2)
