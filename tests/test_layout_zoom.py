"""Zoom windows of the layout drawing (pure logic, numpy only)."""

from __future__ import annotations

import numpy as np
import pytest

from rtt_explorer.layout_zoom import checked_window, fit_aspect, source_point, source_window


def test_checked_window_returns_floats_in_order():
    assert checked_window(-1, 5, -2, 2) == (-1.0, 5.0, -2.0, 2.0)


@pytest.mark.parametrize("window", [(5, 5, -1, 1), (6, 5, -1, 1), (0, 1, 2, 2), (0, 1, 3, 2),
                                    (0, float("nan"), -1, 1), (0, 1, -float("inf"), 1)])
def test_checked_window_rejects_empty_reversed_and_non_finite_windows(window):
    with pytest.raises(ValueError):
        checked_window(*window)


def test_source_window_is_centred_on_the_source_with_the_requested_aspect():
    z0, z1, l0, l1 = source_window(0.0, 0.0, 3.0, aspect=4.0)
    assert (z0, z1) == pytest.approx((-3.0, 3.0))
    assert (l0, l1) == pytest.approx((-0.75, 0.75))
    z0, z1, l0, l1 = source_window(10.0, -2.0, 1.0, aspect=2.0)
    assert (z0 + z1) / 2 == pytest.approx(10.0)
    assert (l0 + l1) / 2 == pytest.approx(-2.0)
    assert (z1 - z0) / (l1 - l0) == pytest.approx(2.0)


@pytest.mark.parametrize("half_width, aspect", [(0.0, 3.0), (-1.0, 3.0), (1.0, 0.0), (float("nan"), 3.0)])
def test_source_window_rejects_invalid_sizes(half_width, aspect):
    with pytest.raises(ValueError):
        source_window(0.0, 0.0, half_width, aspect)


def test_source_point_is_the_mean_start_of_all_rays_for_the_lateral_axis():
    # two bundles, rays start at z = 0.001 and the lateral coordinate 0 / 0.5
    a = np.array([[[0.0, 0.0, 0.001], [0.0, 1.0, 5.0]], [[0.0, 0.0, 0.001], [0.0, 2.0, 5.0]]])
    b = np.array([[[0.0, 0.5, 0.001], [0.0, 1.0, 5.0]]])
    assert source_point([a, b], 1) == pytest.approx((0.001, 1.0 / 6.0))
    assert source_point([a, b], 0) == pytest.approx((0.001, 0.0))


def test_source_point_skips_rays_without_a_finite_start():
    a = np.array([[[0.0, np.nan, 0.0]], [[0.0, 2.0, 4.0]]])
    assert source_point([a], 1) == pytest.approx((4.0, 2.0))


def test_source_point_is_none_without_a_finite_start():
    assert source_point([], 1) is None
    assert source_point([np.full((2, 3, 3), np.nan)], 1) is None


def test_fit_aspect_widens_a_tall_window_in_z_around_its_centre():
    z0, z1, l0, l1 = fit_aspect((0.0, 2.0, -5.0, 5.0), 2.0)
    assert (l0, l1) == (-5.0, 5.0)
    assert (z0 + z1) / 2 == pytest.approx(1.0)
    assert (z1 - z0) / (l1 - l0) == pytest.approx(2.0)


def test_fit_aspect_widens_a_flat_window_laterally_around_its_centre():
    z0, z1, l0, l1 = fit_aspect((5.0, 20.0, -0.5, 0.5), 2.0)
    assert (z0, z1) == (5.0, 20.0)
    assert (l0 + l1) / 2 == pytest.approx(0.0)
    assert (z1 - z0) / (l1 - l0) == pytest.approx(2.0)


def test_fit_aspect_keeps_the_whole_window_and_leaves_a_fitting_window_unchanged():
    window = (0.0, 10.0, 0.0, 5.0)
    assert fit_aspect(window, 2.0) == pytest.approx(window)
    z0, z1, l0, l1 = fit_aspect((0.0, 3.0, 0.0, 4.0), 5.0)
    assert z0 <= 0.0 and z1 >= 3.0 and l0 <= 0.0 and l1 >= 4.0


@pytest.mark.parametrize("window, aspect", [((1, 1, 0, 1), 2.0), ((0, 1, 0, 1), 0.0), ((0, 1, 0, 1), float("nan"))])
def test_fit_aspect_rejects_an_empty_window_and_an_invalid_aspect(window, aspect):
    with pytest.raises(ValueError):
        fit_aspect(window, aspect)
