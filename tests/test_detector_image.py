"""Detector image: pupil points, pixel image and scales (pure logic, numpy only)."""

from __future__ import annotations

import numpy as np
import pytest

from rtt_explorer.detector_image import (
    emission_weights,
    hits_per_pixel,
    image_extent,
    pixel_image,
    pixel_pitch_um,
    scaled,
    sunflower_points,
)


def test_sunflower_points_lie_in_the_unit_disk_and_are_uniform_in_area():
    px, py = sunflower_points(20_000)
    assert px.shape == py.shape == (20_000,)
    r2 = px**2 + py**2
    assert r2.max() <= 1.0
    # uniform in area: r^2 is uniform on [0, 1], so mean 1/2 and variance 1/12
    assert r2.mean() == pytest.approx(0.5, abs=2e-3)
    assert r2.var() == pytest.approx(1.0 / 12.0, abs=2e-3)
    # centred and without a preferred direction
    assert abs(px.mean()) < 2e-3 and abs(py.mean()) < 2e-3
    assert np.mean(px * py) == pytest.approx(0.0, abs=2e-3)


def test_sunflower_points_are_reproducible_and_distinct():
    a = sunflower_points(1000)
    b = sunflower_points(1000)
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])
    assert len({(round(x, 12), round(y, 12)) for x, y in zip(*a)}) == 1000


@pytest.mark.parametrize("n", [0, -5])
def test_sunflower_points_need_a_positive_count(n):
    with pytest.raises(ValueError):
        sunflower_points(n)


def test_image_extent_covers_the_points_with_a_margin():
    x = np.array([-2.0, 4.0, 1.0])
    y = np.array([0.0, 1.0, -1.0])
    x0, x1, y0, y1 = image_extent(x, y, margin=0.1)
    assert (x0, x1) == pytest.approx((-2.6, 4.6))
    assert (y0, y1) == pytest.approx((-1.2, 1.2))


def test_image_extent_ignores_non_finite_points():
    x = np.array([0.0, np.nan, 2.0, np.inf])
    y = np.array([0.0, 5.0, 2.0, 1.0])
    x0, x1, y0, y1 = image_extent(x, y, margin=0.0)
    assert (x0, x1) == (0.0, 2.0)
    assert (y0, y1) == (0.0, 2.0)


def test_image_extent_square_has_equal_widths_around_the_same_centre():
    x = np.array([0.0, 10.0])
    y = np.array([0.0, 2.0])
    x0, x1, y0, y1 = image_extent(x, y, margin=0.0, square=True)
    assert x1 - x0 == pytest.approx(y1 - y0)
    assert (x0 + x1) / 2 == pytest.approx(5.0) and (y0 + y1) / 2 == pytest.approx(1.0)
    assert x0 <= 0.0 and x1 >= 10.0 and y0 <= 0.0 and y1 >= 2.0


def test_image_extent_of_a_single_point_is_not_empty():
    x0, x1, y0, y1 = image_extent(np.array([3.0]), np.array([-1.0]))
    assert x1 > x0 and y1 > y0
    assert x0 < 3.0 < x1 and y0 < -1.0 < y1


@pytest.mark.parametrize("x, y", [(np.array([]), np.array([])), (np.array([np.nan]), np.array([np.nan]))])
def test_image_extent_needs_a_finite_point(x, y):
    with pytest.raises(ValueError):
        image_extent(x, y)


def test_pixel_image_sums_weights_per_pixel_and_keeps_the_total():
    x = np.array([0.5, 0.6, 2.5, 3.9])
    y = np.array([0.5, 0.5, 1.5, 1.5])
    w = np.array([1.0, 2.0, 4.0, 8.0])
    image = pixel_image(x, y, w, (0.0, 4.0, 0.0, 2.0), nx=4, ny=2)
    assert image.shape == (2, 4)  # (ny, nx)
    assert image.sum() == pytest.approx(15.0)
    assert image[0, 0] == 3.0  # row 0 is the lowest y, column 0 the lowest x
    assert image[1, 2] == 4.0
    assert image[1, 3] == 8.0


def test_pixel_image_counts_a_point_on_the_upper_edge_in_the_last_pixel():
    image = pixel_image(np.array([4.0]), np.array([2.0]), np.array([1.0]), (0.0, 4.0, 0.0, 2.0), nx=4, ny=2)
    assert image[1, 3] == 1.0


def test_pixel_image_ignores_points_outside_the_extent_and_non_finite_points():
    x = np.array([5.0, -1.0, 1.0, np.nan, 2.0])
    y = np.array([1.0, 1.0, 1.0, 1.0, np.inf])
    image = pixel_image(x, y, np.ones(5), (0.0, 4.0, 0.0, 2.0), nx=4, ny=2)
    assert image.sum() == 1.0 and image[1, 1] == 1.0


@pytest.mark.parametrize("nx, ny, extent", [(0, 4, (0, 1, 0, 1)), (4, -1, (0, 1, 0, 1)), (4, 4, (1, 1, 0, 1)),
                                            (4, 4, (0, 1, 2, 1)), (4, 4, (0, np.inf, 0, 1))])
def test_pixel_image_rejects_bad_sizes_and_extents(nx, ny, extent):
    with pytest.raises(ValueError):
        pixel_image(np.array([0.5]), np.array([0.5]), np.array([1.0]), extent, nx, ny)


def test_hits_per_pixel_is_the_median_count_of_the_illuminated_pixels():
    x = np.array([0.5, 0.6, 0.7, 2.5])
    y = np.array([0.5, 0.5, 0.5, 1.5])
    assert hits_per_pixel(x, y, (0.0, 4.0, 0.0, 2.0), nx=4, ny=2) == 2.0  # pixels with 3 and 1 hits
    assert hits_per_pixel(np.array([9.0]), np.array([9.0]), (0.0, 4.0, 0.0, 2.0), nx=4, ny=2) == 0.0


def test_pixel_pitch_in_micrometre():
    assert pixel_pitch_um((0.0, 4.0, -1.0, 1.0), nx=200, ny=50) == pytest.approx((20.0, 40.0))


def test_scaled_linear_is_normalised_to_the_maximum():
    s = scaled(np.array([[0.0, 2.0], [4.0, 1.0]]), "linear")
    assert s.tolist() == [[0.0, 0.5], [1.0, 0.25]]


def test_scaled_log_maps_the_floor_to_0_and_the_maximum_to_1():
    image = np.array([[0.0, 1e-4], [1e-2, 1.0]])
    s = scaled(image, "log", floor=1e-4)
    assert s.ravel().tolist() == pytest.approx([0.0, 0.0, 0.5, 1.0])


def test_scaled_of_an_empty_image_is_all_zero_and_unknown_mode_is_an_error():
    assert scaled(np.zeros((2, 2)), "linear").sum() == 0.0
    assert scaled(np.zeros((2, 2)), "log").sum() == 0.0
    with pytest.raises(ValueError):
        scaled(np.ones((2, 2)), "sqrt")


def test_emission_weights_of_an_isotropic_source_are_the_cube_of_the_cosine():
    # Rays uniform on a plane at distance h from the source: rays per solid angle ~ 1 / cos^3, so an
    # isotropic source needs the weight cos^3 (d(Omega) = cos^3(alpha) dA / h^2).
    cosine = np.array([1.0, 0.5, -0.5, 0.0])
    assert emission_weights(cosine).tolist() == pytest.approx([1.0, 0.125, 0.125, 0.0])
