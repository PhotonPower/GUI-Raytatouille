"""Run a library call in a thread and poll its progress from the calling thread (pure logic)."""

from __future__ import annotations

import threading
import time

import pytest

from rtt_explorer.progress_run import Progress, run_with_progress


def test_progress_keeps_the_last_report_and_its_fraction():
    progress = Progress()
    assert progress.snapshot() == (0, 0, "")
    assert progress.fraction == 0.0
    progress(5, 20, "monte_carlo")
    assert progress.snapshot() == (5, 20, "monte_carlo")
    assert progress.fraction == 0.25
    progress(20, 20, "monte_carlo")
    assert progress.fraction == 1.0


def test_fraction_is_clamped_and_safe_for_zero_total():
    progress = Progress()
    progress(3, 0, "x")
    assert progress.fraction == 0.0
    progress(9, 4, "x")
    assert progress.fraction == 1.0


def test_result_is_returned_and_ticks_come_from_the_calling_thread():
    caller = threading.get_ident()
    seen: list[int] = []
    ticks: list[float] = []

    def work(progress):
        for k in range(1, 5):
            time.sleep(0.05)
            progress(k, 4, "run")
        return "done"

    def on_tick(progress):
        seen.append(threading.get_ident())
        ticks.append(progress.fraction)

    assert run_with_progress(work, on_tick, interval=0.01) == "done"
    assert set(seen) == {caller}
    assert ticks[-1] == 1.0  # a final tick after the work is done
    assert ticks == sorted(ticks)


def test_exception_of_the_work_is_raised_in_the_caller_after_the_last_tick():
    ticks = []

    def work(progress):
        progress(1, 2, "run")
        raise ValueError("kaputt")

    with pytest.raises(ValueError, match="kaputt"):
        run_with_progress(work, ticks.append, interval=0.01)
    assert ticks  # at least the final tick


def test_work_receives_the_progress_object_it_is_polled_with():
    mine = Progress()

    def work(progress):
        assert progress is mine
        return 1

    assert run_with_progress(work, lambda p: None, interval=0.01, progress=mine) == 1


def test_a_failing_tick_does_not_lose_the_result():
    def work(progress):
        time.sleep(0.05)
        return 7

    def bad_tick(progress):
        raise RuntimeError("display broke")

    assert run_with_progress(work, bad_tick, interval=0.01) == 7
