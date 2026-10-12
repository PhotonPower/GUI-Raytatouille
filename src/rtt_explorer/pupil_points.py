"""Pupil point lists typed by the user, the ray nearest to a point and the text of a Jones matrix element
(pure Python, no library).

Error messages are German because they are shown to the user as they are.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence

_SEPARATORS = re.compile(r"[,;\s]+")


def parse_pupil_points(text: str) -> tuple[list[float], list[float]]:
    """(px, py) from one point per line, ``px, py`` or ``px; py`` or ``px py`` with a decimal point.

    Empty lines and lines starting with ``#`` are skipped; points outside the unit circle are
    allowed (the library aims them like single pupil points)."""
    px, py = [], []
    for number, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p for p in _SEPARATORS.split(line) if p]
        if len(parts) != 2:
            raise ValueError(f"Zeile {number}: zwei Zahlen px und py erwartet, z. B. „0.5, -0.25“.")
        values = []
        for part in parts:
            try:
                values.append(float(part))
            except ValueError:
                raise ValueError(f"Zeile {number}: '{part}' ist keine Zahl (Dezimalpunkt verwenden).") from None
        if not all(math.isfinite(v) for v in values):
            raise ValueError(f"Zeile {number}: nur endliche Zahlen sind erlaubt.")
        px.append(values[0])
        py.append(values[1])
    if not px:
        raise ValueError("Mindestens ein Punkt ist nötig (eine Zeile „px, py“).")
    return px, py


def nearest_index(xs: Sequence[float], ys: Sequence[float], x0: float = 0.0, y0: float = 0.0) -> int:
    """Index of the point (xs[i], ys[i]) closest to (x0, y0), e.g. the chief ray of a free beam."""
    return min(range(len(xs)), key=lambda i: (xs[i] - x0) ** 2 + (ys[i] - y0) ** 2)


def jones_text(value: complex) -> str:
    """A Jones matrix element as amplitude and phase in degree; "–" where the library gives NaN."""
    if not (math.isfinite(value.real) and math.isfinite(value.imag)):
        return "–"
    return f"{abs(value):.4f} ∠ {math.degrees(math.atan2(value.imag, value.real)):.2f}°"
