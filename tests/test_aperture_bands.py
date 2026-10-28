"""Blocked and open bands of annular apertures in the layout (pure logic)."""

from __future__ import annotations

import pytest

from rtt_explorer.layout_geometry import aperture_bands, inner_radius


def test_inner_radius_of_a_circular_aperture():
    assert inner_radius(("circular", {"radius": 7.0, "inner_radius": 2.0})) == 2.0


@pytest.mark.parametrize("aperture", [None, ("circular", {"radius": 7.0}),
                                      ("circular", {"radius": 7.0, "inner_radius": 0.0}),
                                      ("rectangular", {"half_width_x": 3.0, "half_width_y": 2.0}),
                                      ("elliptical", {"semi_axis_x": 3.0, "semi_axis_y": 2.0})])
def test_inner_radius_is_zero_without_a_hole(aperture):
    assert inner_radius(aperture) == 0.0


def test_ring_has_a_blocked_centre_and_blocked_jaws_outside_and_two_open_bands():
    blocked, free = aperture_bands(2.0, 7.0)
    assert [x for band in blocked for x in band] == pytest.approx([-2.0, 2.0, 7.0, 9.8, -9.8, -7.0])
    assert free == [(2.0, 7.0), (-7.0, -2.0)]


def test_aperture_without_a_hole_has_one_open_band_and_only_the_jaws_blocked():
    blocked, free = aperture_bands(0.0, 5.0, jaw=1.5)
    assert blocked == [(5.0, 7.5), (-7.5, -5.0)]
    assert free == [(-5.0, 5.0)]


def test_blocked_and_open_bands_do_not_overlap_and_cover_the_whole_range():
    blocked, free = aperture_bands(1.5, 4.0)
    edges = sorted(x for band in blocked + free for x in band)
    # every band edge appears twice (shared by two bands) except the outer ends
    inner_edges = edges[1:-1]
    assert all(inner_edges.count(x) == 2 for x in set(inner_edges))


@pytest.mark.parametrize("inner, outer", [(7.0, 7.0), (8.0, 7.0), (-1.0, 7.0), (0.0, 0.0), (0.0, -2.0),
                                          (0.0, float("nan")), (float("inf"), 5.0)])
def test_aperture_bands_reject_an_empty_or_reversed_ring(inner, outer):
    with pytest.raises(ValueError):
        aperture_bands(inner, outer)
