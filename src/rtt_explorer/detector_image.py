"""Detector image like a camera (pure logic, numpy only, no Streamlit, no library).

Rays hit the image surface at points (x, y) in mm in its local coordinates; the image is the sum of
the ray weights per pixel. Row 0 of an image is the lowest y, column 0 the lowest x (``imshow`` with
``origin="lower"``).
"""

from __future__ import annotations

import math

import numpy as np

Extent = tuple[float, float, float, float]  # (x_min, x_max, y_min, y_max) in mm

_GOLDEN_ANGLE = math.pi * (3.0 - math.sqrt(5.0))


def sunflower_points(n: int) -> tuple[np.ndarray, np.ndarray]:
    """``n`` normalised pupil points, uniform in area on the unit disk (Vogel's sunflower spiral).

    Unlike hexapolar rings there are no rings or spokes that would show as a pattern in the image.
    ``ValueError`` for ``n < 1``."""
    if n < 1:
        raise ValueError("Pupillenpunkte: die Anzahl muss mindestens 1 sein")
    k = np.arange(n, dtype=float) + 0.5
    r = np.sqrt(k / n)
    angle = k * _GOLDEN_ANGLE
    return r * np.cos(angle), r * np.sin(angle)


def image_extent(x, y, margin: float = 0.05, square: bool = False) -> Extent:
    """Rectangle around the finite points, enlarged by ``margin`` of its width and height.

    ``square`` makes both widths equal around the same centre (square pixels for a square number of
    pixels). A single point or points on a line get a small non-empty size. ``ValueError`` without a
    finite point."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    if not ok.any():
        raise ValueError("Bildfeld: es gibt keinen endlichen Punkt")
    x, y = x[ok], y[ok]
    x0, x1, y0, y1 = float(x.min()), float(x.max()), float(y.min()), float(y.max())
    width, height = x1 - x0, y1 - y0
    if width <= 0.0 and height <= 0.0:
        width = height = 1.0e-3
    width, height = width or height, height or width  # a line gets the size of the other direction
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    width, height = width * (1.0 + 2.0 * margin), height * (1.0 + 2.0 * margin)
    if square:
        width = height = max(width, height)
    return cx - width / 2.0, cx + width / 2.0, cy - height / 2.0, cy + height / 2.0


def _checked_grid(extent: Extent, nx: int, ny: int) -> None:
    if nx < 1 or ny < 1:
        raise ValueError("Bild: die Pixelzahlen müssen mindestens 1 sein")
    x0, x1, y0, y1 = extent
    if not all(math.isfinite(v) for v in extent) or not (x1 > x0 and y1 > y0):
        raise ValueError("Bildfeld: es muss x von < x bis und y von < y bis gelten (endliche Zahlen)")


def pixel_image(x, y, weight, extent: Extent, nx: int, ny: int) -> np.ndarray:
    """Sum of ``weight`` per pixel, shape ``(ny, nx)``; points outside ``extent`` and non-finite
    points are ignored, a point on the upper edge belongs to the last pixel."""
    _checked_grid(extent, nx, ny)
    x, y, weight = (np.asarray(a, dtype=float) for a in (x, y, weight))
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(weight)
    x0, x1, y0, y1 = extent
    image, _, _ = np.histogram2d(y[ok], x[ok], bins=(ny, nx), range=((y0, y1), (x0, x1)), weights=weight[ok])
    return image


def hits_per_pixel(x, y, extent: Extent, nx: int, ny: int) -> float:
    """Median number of rays in the pixels that were hit (0 if none): a measure of the noise."""
    counts = pixel_image(x, y, np.ones(np.size(x)), extent, nx, ny)
    hit = counts[counts > 0]
    return float(np.median(hit)) if hit.size else 0.0


def pixel_pitch_um(extent: Extent, nx: int, ny: int) -> tuple[float, float]:
    """Pixel size (x, y) in micrometre."""
    _checked_grid(extent, nx, ny)
    x0, x1, y0, y1 = extent
    return 1000.0 * (x1 - x0) / nx, 1000.0 * (y1 - y0) / ny


def scaled(image: np.ndarray, mode: str, floor: float = 1.0e-4) -> np.ndarray:
    """Image normalised to [0, 1] for display: ``"linear"`` divides by the maximum; ``"log"`` maps
    ``floor`` (relative to the maximum) to 0 and the maximum to 1. An empty image stays 0;
    ``ValueError`` for another mode."""
    if mode not in ("linear", "log"):
        raise ValueError("Skala: 'linear' oder 'log'")
    image = np.asarray(image, dtype=float)
    top = float(image.max()) if image.size else 0.0
    if not top > 0.0:
        return np.zeros_like(image)
    relative = image / top
    if mode == "linear":
        return relative
    low = math.log10(floor)
    return (np.log10(np.maximum(relative, floor)) - low) / (0.0 - low)


def emission_weights(cosine) -> np.ndarray:
    """Weights of an isotropic point source for rays aimed uniformly at a plane.

    ``cosine`` is the cosine of the angle between each ray and the normal of that plane (the stop).
    A ray bundle that is uniform on the plane has 1 / cos^3 rays per solid angle (d(Omega) = cos^3(alpha)
    dA / h^2 for a source at the normal distance h), so the weight cos^3 gives the same power per
    solid angle in every direction. Rays against the normal get the same weight as along it."""
    return np.abs(np.asarray(cosine, dtype=float)) ** 3
