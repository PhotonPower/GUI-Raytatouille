"""Irradiance view: visits of a surface, ray limits and loss rows (pure logic)."""

from __future__ import annotations

from types import SimpleNamespace as NS

import numpy as np
import pytest

from rtt_explorer.irradiance_logic import (
    MAX_BATCH_RAYS,
    MAX_PATH_RAYS,
    cell_size_um,
    event_label,
    loss_rows,
    max_rays,
    visits,
)


def test_visits_group_the_events_by_surface_in_order_of_first_visit():
    # double pass: P.S2 (3) and P.S1 (2) are visited twice
    assert visits([0, 2, 3, 4, 3, 2, 1]) == {0: [0], 2: [1, 5], 3: [2, 4], 4: [3], 1: [6]}
    assert list(visits([0, 2, 3, 4, 3, 2, 1])) == [0, 2, 3, 4, 1]


def test_visits_accept_numpy_integers_and_return_plain_ints():
    result = visits(np.array([5, 7, 5], dtype=np.uint32))
    assert result == {5: [0, 2], 7: [1]}
    assert all(type(k) is int for k in result) and all(type(e) is int for v in result.values() for e in v)


def test_event_label_names_the_visit_only_for_a_surface_visited_more_than_once():
    assert event_label(3, 0, 1) == "Ereignis 3"
    assert event_label(5, 1, 2) == "Ereignis 5 (2. Besuch)"


def test_max_rays_is_larger_for_the_last_surface_that_needs_no_recording():
    assert max_rays(True) == MAX_BATCH_RAYS
    assert max_rays(False) == MAX_PATH_RAYS
    assert MAX_BATCH_RAYS > MAX_PATH_RAYS


def test_loss_rows_name_the_three_reasons_and_keep_counts_and_weights():
    rows = loss_rows(NS(count=3, weight=2.5), NS(count=0, weight=0.0), NS(count=12, weight=9.0))
    assert [r["Grund"] for r in rows] == ["außerhalb des Rasters", "an einer Apertur abgeschattet",
                                         "Fläche nicht erreicht"]
    assert [r["Strahlen"] for r in rows] == [3, 0, 12]
    assert [r["Gewicht"] for r in rows] == [2.5, 0.0, 9.0]


def test_cell_size_in_micrometres_from_the_edges():
    x = np.linspace(-1.0, 1.0, 5)  # 4 cells of 0.5 mm
    y = np.linspace(0.0, 0.3, 4)  # 3 cells of 0.1 mm
    assert cell_size_um(x, y) == pytest.approx((500.0, 100.0))
