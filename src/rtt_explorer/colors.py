"""Spectral colours for ray plots."""

from __future__ import annotations


def wavelength_rgb(um: float) -> tuple[float, float, float]:
    """Rough spectral colour for a wavelength in um (violet to red; IR dark red, UV purple)."""
    w = um * 1000.0
    if w < 380:
        return (0.5, 0.0, 0.8)
    if w < 440:
        r, g, b = -(w - 440) / 60, 0.0, 1.0
    elif w < 490:
        r, g, b = 0.0, (w - 440) / 50, 1.0
    elif w < 510:
        r, g, b = 0.0, 1.0, -(w - 510) / 20
    elif w < 580:
        r, g, b = (w - 510) / 70, 1.0, 0.0
    elif w < 645:
        r, g, b = 1.0, -(w - 645) / 65, 0.0
    elif w <= 780:
        r, g, b = 1.0, 0.0, 0.0
    else:
        return (0.5, 0.0, 0.0)
    fade = 0.7 if w < 400 or w > 700 else 1.0
    return (max(r, 0) * fade, max(g, 0) * 0.85 * fade, max(b, 0) * fade)
