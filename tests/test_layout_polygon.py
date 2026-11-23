"""Polygon apertures and obscurations in the section of the layout (pure geometry)."""

from __future__ import annotations

import math

import pytest

from rtt_explorer.layout_geometry import obscuration_intervals, polygon_section_intervals

HEXAGON = [[29.445, 17.0], [0.0, 34.0], [-29.445, 17.0], [-29.445, -17.0], [-0.0, -34.0], [29.445, -17.0]]
SQUARE = [[-2.0, -2.0], [2.0, -2.0], [2.0, 2.0], [-2.0, 2.0]]


def test_square_is_cut_over_its_full_width_in_both_planes():
    assert polygon_section_intervals(SQUARE, "yz") == [pytest.approx((-2.0, 2.0))]
    assert polygon_section_intervals(SQUARE, "xz") == [pytest.approx((-2.0, 2.0))]


def test_hexagon_reaches_its_vertices_in_yz_and_its_flats_in_xz():
    (lo, hi), = polygon_section_intervals(HEXAGON, "yz")
    assert (lo, hi) == pytest.approx((-34.0, 34.0))
    (lo, hi), = polygon_section_intervals(HEXAGON, "xz")
    assert (lo, hi) == pytest.approx((-29.445, 29.445))


def test_diamond_has_its_vertices_on_the_axes():
    r = 5.0
    diamond = [[r, 0.0], [0.0, r], [-r, 0.0], [0.0, -r]]
    assert polygon_section_intervals(diamond, "yz") == [pytest.approx((-r, r))]
    assert polygon_section_intervals(diamond, "xz") == [pytest.approx((-r, r))]


def test_concave_u_shape_gives_two_intervals_on_the_axis_through_its_arms():
    # a "U" with a notch around x = 0: the line x = 0 only hits the base
    u = [[-3.0, -3.0], [3.0, -3.0], [3.0, 3.0], [1.0, 3.0], [1.0, -1.0], [-1.0, -1.0], [-1.0, 3.0], [-3.0, 3.0]]
    assert polygon_section_intervals(u, "yz") == [pytest.approx((-3.0, -1.0))]
    # the line y = 2 would cut both arms; y = 0 axis (xz) passes through both arms and the notch
    xz = polygon_section_intervals(u, "xz")
    assert xz == [pytest.approx((-3.0, -1.0)), pytest.approx((1.0, 3.0))]


def test_polygon_off_the_axis_is_missed():
    away = [[1.0, -1.0], [3.0, -1.0], [3.0, 1.0], [1.0, 1.0]]
    assert polygon_section_intervals(away, "yz") == []


def test_polygon_needs_three_vertices():
    with pytest.raises(ValueError):
        polygon_section_intervals([[0.0, 0.0], [1.0, 1.0]], "yz")


def test_circular_obscuration_on_the_axis_and_decentred():
    p = {"radius": 10.0, "decenter_x": 0.0, "decenter_y": 0.0}
    assert obscuration_intervals("circular", p, "yz") == [pytest.approx((-10.0, 10.0))]
    off = {"radius": 10.0, "decenter_x": 20.0, "decenter_y": 0.0}
    assert obscuration_intervals("circular", off, "yz") == []  # the line x = 0 misses it
    assert obscuration_intervals("circular", off, "xz") == [pytest.approx((10.0, 30.0))]


def test_spider_arms_cut_along_and_across():
    arm = {"half_width_x": 31.0, "half_width_y": 0.5, "decenter_x": 0.0, "decenter_y": 0.0, "rotation_deg": 0.0}
    assert obscuration_intervals("rectangular", arm, "yz") == [pytest.approx((-0.5, 0.5))]  # across a horizontal arm
    assert obscuration_intervals("rectangular", arm, "xz") == [pytest.approx((-31.0, 31.0))]  # along it
    turned = {**arm, "rotation_deg": 90.0}
    assert obscuration_intervals("rectangular", turned, "yz") == [pytest.approx((-31.0, 31.0))]
    assert obscuration_intervals("rectangular", turned, "xz") == [pytest.approx((-0.5, 0.5))]


def test_elliptical_obscuration_hits_and_misses_the_section():
    hit = {"semi_axis_x": 3.0, "semi_axis_y": 1.5, "decenter_x": 0.0, "decenter_y": 1.0, "rotation_deg": 0.0}
    assert obscuration_intervals("elliptical", hit, "yz") == [pytest.approx((-0.5, 2.5))]
    far = {"semi_axis_x": 3.0, "semi_axis_y": 1.5, "decenter_x": 20.0, "decenter_y": 5.0, "rotation_deg": 30.0}
    assert obscuration_intervals("elliptical", far, "yz") == []
    assert obscuration_intervals("elliptical", far, "xz") == []  # half height 1.98 < 5


def test_rotated_ellipse_has_the_expected_chord():
    # semi axes 4 and 1 turned by 90 degrees: along y it is 4 long, along x only 1
    p = {"semi_axis_x": 4.0, "semi_axis_y": 1.0, "decenter_x": 0.0, "decenter_y": 0.0, "rotation_deg": 90.0}
    assert obscuration_intervals("elliptical", p, "yz") == [pytest.approx((-4.0, 4.0))]
    (lo, hi), = obscuration_intervals("elliptical", p, "xz")
    assert math.isclose(hi, 1.0, abs_tol=1e-12) and math.isclose(lo, -1.0, abs_tol=1e-12)


def test_unknown_obscuration_kind_is_an_error():
    with pytest.raises(ValueError, match="Obskuration"):
        obscuration_intervals("star", {}, "yz")
