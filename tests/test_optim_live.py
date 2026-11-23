"""Live record of an optimization run (pure logic; fakes stand in for IterationState)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from rtt_explorer.optim_live import LiveHistory


def state(k, phi, values=(1.0,)):
    return SimpleNamespace(k=k, phi=phi, values=values)


def test_records_every_state_in_order():
    live = LiveHistory()
    for k, phi in enumerate([1.0, 0.5, 0.25], start=1):
        live.add(state(k, phi))
    assert live.k == [1, 2, 3]
    assert live.phi == [1.0, 0.5, 0.25]
    assert live.count == 3


def test_best_and_last_values():
    live = LiveHistory()
    assert live.best is None and live.last_values is None
    live.add(state(1, 2.0, (1.0, 2.0)))
    live.add(state(2, 0.5, (3.0, 4.0)))
    assert live.best == 0.5
    assert live.last_values == (3.0, 4.0)


def test_values_are_copied_so_later_changes_do_not_leak():
    values = [1.0, 2.0]
    live = LiveHistory()
    live.add(state(1, 1.0, values))
    values[0] = 99.0
    assert live.last_values == (1.0, 2.0)


def test_draw_is_throttled_but_the_first_and_forced_calls_pass():
    now = [0.0]
    live = LiveHistory(min_interval=0.2, clock=lambda: now[0])
    assert live.due() is True  # nothing drawn yet
    live.mark_drawn()
    now[0] = 0.1
    assert live.due() is False
    assert live.due(force=True) is True
    now[0] = 0.25
    assert live.due() is True


def test_a_phi_of_zero_or_nan_does_not_break_the_log_plot_data():
    live = LiveHistory()
    live.add(state(1, 0.0))
    live.add(state(2, float("nan")))
    live.add(state(3, 1e-3))
    k, phi = live.plot_data()
    assert k == [3]
    assert phi == [1e-3]


def test_min_interval_must_not_be_negative():
    with pytest.raises(ValueError):
        LiveHistory(min_interval=-1.0)
