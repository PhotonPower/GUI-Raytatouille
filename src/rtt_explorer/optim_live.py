"""Live record of an optimization run (pure logic, no Streamlit, no library).

``optimize(on_iteration=...)`` calls back after every accepted solve with an ``IterationState``
(``k``, ``phi``, ``values``). ``LiveHistory`` keeps those states and tells the view when a redraw is
due, so a fast run does not redraw the chart hundreds of times.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable


class LiveHistory:
    """Accepted states of a running optimization and a throttle for redrawing them."""

    def __init__(self, min_interval: float = 0.15, clock: Callable[[], float] = time.monotonic) -> None:
        if min_interval < 0:
            raise ValueError("min_interval must not be negative")
        self.k: list[int] = []
        self.phi: list[float] = []
        self._last_values: tuple[float, ...] | None = None
        self._min_interval = min_interval
        self._clock = clock
        self._drawn_at: float | None = None

    def add(self, state) -> None:
        """Record one ``IterationState`` (values are copied: the library may reuse the buffer)."""
        self.k.append(int(state.k))
        self.phi.append(float(state.phi))
        self._last_values = tuple(float(v) for v in state.values)

    @property
    def count(self) -> int:
        return len(self.k)

    @property
    def best(self) -> float | None:
        """Smallest finite phi so far, or None."""
        finite = [p for p in self.phi if math.isfinite(p)]
        return min(finite) if finite else None

    @property
    def last_values(self) -> tuple[float, ...] | None:
        return self._last_values

    def plot_data(self) -> tuple[list[int], list[float]]:
        """(k, phi) of the states that a logarithmic axis can show: finite and positive."""
        pairs = [(k, p) for k, p in zip(self.k, self.phi) if math.isfinite(p) and p > 0]
        return [k for k, _ in pairs], [p for _, p in pairs]

    def due(self, force: bool = False) -> bool:
        """True if a redraw is due: forced, nothing drawn yet, or the interval has passed."""
        if force or self._drawn_at is None:
            return True
        return self._clock() - self._drawn_at >= self._min_interval

    def mark_drawn(self) -> None:
        self._drawn_at = self._clock()
