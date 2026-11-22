"""Run a library call in a thread and poll its progress from the calling thread (pure logic, no Streamlit).

The library reports progress with ``progress(done, total, stage)`` "with the GIL from any thread". Streamlit can only
draw from the script thread, which would be blocked inside the call. So the call runs in a worker thread, the
callback only stores the numbers (``Progress``), and the script thread polls them and redraws (``run_with_progress``).
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any


class Progress:
    """Thread-safe store of the last ``progress(done, total, stage)`` report; usable as the library callback."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = (0, 0, "")

    def __call__(self, done: int, total: int, stage: str) -> None:
        with self._lock:
            self._state = (int(done), int(total), str(stage))

    def snapshot(self) -> tuple[int, int, str]:
        with self._lock:
            return self._state

    @property
    def fraction(self) -> float:
        """Share of the work done, 0 to 1 (0 while the total is unknown)."""
        done, total, _ = self.snapshot()
        return 0.0 if total <= 0 else min(1.0, max(0.0, done / total))


def run_with_progress(func: Callable[[Progress], Any], on_tick: Callable[[Progress], None],
                      interval: float = 0.1, progress: Progress | None = None) -> Any:
    """Call ``func(progress)`` in a worker thread; call ``on_tick(progress)`` from this thread every ``interval`` s.

    Returns the result of ``func``; an exception of ``func`` is raised here after the last tick. ``on_tick`` also runs
    once after the work is done. An ``Exception`` in ``on_tick`` is ignored (the display is only a convenience and
    must not lose the result); anything else, such as Streamlit's rerun signal, propagates and leaves the worker
    running to its end in the background."""
    progress = Progress() if progress is None else progress
    box: dict[str, Any] = {}

    def target() -> None:
        try:
            box["result"] = func(progress)
        except BaseException as error:  # noqa: BLE001 - handed to the calling thread
            box["error"] = error

    def tick() -> None:
        try:
            on_tick(progress)
        except Exception:  # noqa: BLE001
            pass

    worker = threading.Thread(target=target, daemon=True, name="rtt-run")
    worker.start()
    while worker.is_alive():
        worker.join(interval)
        tick()
    tick()
    if "error" in box:
        raise box["error"]
    return box["result"]
