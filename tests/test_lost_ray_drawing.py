"""Lost rays in the layout: end at the last valid surface (pure logic, numpy only)."""

from __future__ import annotations

import numpy as np
import pytest

from rtt_explorer.layout_geometry import loss_slots, truncate_lost


def paths():
    """Three rays, 4 events (5 slots): alive, lost at event 2, lost at event 0.

    The slot after the loss event holds the point where the ray met the surface that lost it."""
    z = np.array([[0.0, 1.0, 2.0, 3.0, 4.0]] * 3)
    y = np.array([[0.0, 0.1, 0.2, 0.3, 0.4],
                  [0.0, 0.5, 1.0, 1.5, np.nan],  # lost at event 2: slot 3 is its loss point
                  [0.0, 9.0, np.nan, np.nan, np.nan]])  # lost at event 0: slot 1 is its loss point
    position = np.stack([np.zeros_like(z), y, z], axis=2)
    lost_at = np.array([-1, 2, 0])
    return position, lost_at


def test_truncate_lost_cuts_a_lost_ray_after_its_last_valid_surface():
    position, lost_at = paths()
    cut = truncate_lost(position, lost_at)
    assert cut.shape == position.shape
    # alive ray: unchanged
    assert np.array_equal(cut[0], position[0])
    # lost at event 2: slots 0..2 stay (start and the two surfaces it passed), slot 3 on is NaN
    # (slot 3 was the loss point, a finite point in the recorded path)
    assert np.array_equal(cut[1, :3], position[1, :3])
    assert np.isnan(cut[1, 3:]).all()
    # lost at event 0: only the start stays
    assert np.array_equal(cut[2, :1], position[2, :1])
    assert np.isnan(cut[2, 1:]).all()


def test_truncate_lost_returns_a_copy():
    position, lost_at = paths()
    before = position.copy()
    cut = truncate_lost(position, lost_at)
    assert cut is not position
    assert np.array_equal(position, before, equal_nan=True)


def test_truncate_lost_without_a_lost_ray_changes_nothing():
    position, _ = paths()
    cut = truncate_lost(position[:1], np.array([-1]))
    assert np.array_equal(cut, position[:1])


def test_loss_slots_are_the_loss_point_or_the_last_valid_point():
    lost_at = np.array([2, 0])
    assert loss_slots(lost_at, truncated=False).tolist() == [3, 1]
    assert loss_slots(lost_at, truncated=True).tolist() == [2, 0]


def test_the_marker_lies_on_a_drawn_point_in_both_forms():
    position, lost_at = paths()
    lost = np.nonzero(lost_at >= 0)[0]
    for truncated in (False, True):
        shown = truncate_lost(position, lost_at) if truncated else position
        slots = loss_slots(lost_at[lost], truncated)
        assert np.isfinite(shown[lost, slots]).all()


def test_the_untruncated_marker_is_the_point_the_library_recorded():
    position, lost_at = paths()
    lost = np.nonzero(lost_at >= 0)[0]
    slots = loss_slots(lost_at[lost], False)
    assert position[lost, slots, 1].tolist() == [1.5, 9.0]


def test_the_truncated_marker_is_the_last_surface_the_ray_reached():
    position, lost_at = paths()
    lost = np.nonzero(lost_at >= 0)[0]
    slots = loss_slots(lost_at[lost], True)
    assert position[lost, slots, 1].tolist() == [1.0, 0.0]


@pytest.mark.parametrize("bad", [np.zeros((3, 4)), np.zeros(5)])
def test_truncate_lost_rejects_a_wrong_shape(bad):
    with pytest.raises(ValueError):
        truncate_lost(bad, np.array([-1, -1, -1]))
