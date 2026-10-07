"""Ray bundles that need no stop (free collimated beam)."""

from __future__ import annotations

import math

import numpy as np
import raytatouille as rt


def collimated_batch(kind: str, n: int, plane: str, radius: float, z0: float, tilt_x_deg: float,
                     tilt_y_deg: float, wavelength: int):
    """Collimated beam without stop: a fan across the diameter or a hexapolar disc, starting at
    z = z0 with directions tilted by the given angles about the axes (tan convention)."""
    if kind == "Fächer":
        t = np.linspace(-radius, radius, n)
        pts = np.column_stack([np.zeros(n), t]) if plane == "yz" else np.column_stack([t, np.zeros(n)])
    else:
        pts_list = [(0.0, 0.0)]
        for ring in range(1, n + 1):
            count = 6 * ring
            for k in range(count):
                a = 2.0 * math.pi * k / count
                pts_list.append((ring / n * radius * math.cos(a), ring / n * radius * math.sin(a)))
        pts = np.array(pts_list)
    batch = rt.trace.RayBatch(len(pts))
    batch.pos_x[:] = pts[:, 0]
    batch.pos_y[:] = pts[:, 1]
    batch.pos_z[:] = z0
    d = np.array([math.tan(math.radians(tilt_x_deg)), math.tan(math.radians(tilt_y_deg)), 1.0])
    d /= np.linalg.norm(d)
    batch.dir_x[:], batch.dir_y[:], batch.dir_z[:] = d[0], d[1], d[2]
    batch.wl[:] = wavelength
    return batch
