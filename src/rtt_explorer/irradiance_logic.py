"""Irradiance view: visits of a surface, ray limits and loss rows (pure logic, no Streamlit, no library)."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

MAX_PATH_RAYS = 100_000  # rays that are recorded (RayPaths): about 65 bytes per ray and event
MAX_BATCH_RAYS = 4_000_000  # the last surface of a path needs no recording


def visits(events: Sequence[int]) -> dict[int, list[int]]:
    """Event numbers of each surface of a path, in the order of the first visit.

    ``events`` holds the surface index of each event of the path. A surface visited twice (a double pass,
    a mirror) has two event numbers; the library chooses an event by this absolute number."""
    result: dict[int, list[int]] = {}
    for number, surface in enumerate(events):
        result.setdefault(int(surface), []).append(number)
    return result


def event_label(event: int, visit: int, count: int) -> str:
    """Label of an event in the selection: ``Ereignis 5`` or, for a surface visited several times, with the visit."""
    return f"Ereignis {event}" if count == 1 else f"Ereignis {event} ({visit + 1}. Besuch)"


def max_rays(is_last_surface: bool) -> int:
    """Most rays the view traces: more for the last surface of the path, which needs no recording."""
    return MAX_BATCH_RAYS if is_last_surface else MAX_PATH_RAYS


def loss_rows(outside, vignetted, not_reached) -> list[dict]:
    """Rows of the rays that do not count in the map: number and weight per reason."""
    reasons = (("außerhalb des Rasters", outside), ("an einer Apertur abgeschattet", vignetted),
               ("Fläche nicht erreicht", not_reached))
    return [{"Grund": name, "Strahlen": int(item.count), "Gewicht": float(item.weight)} for name, item in reasons]


def cell_size_um(x_edges, y_edges) -> tuple[float, float]:
    """Width and height of a cell in µm from the edges in mm (the grid is regular)."""
    return 1000.0 * float(np.mean(np.diff(x_edges))), 1000.0 * float(np.mean(np.diff(y_edges)))
