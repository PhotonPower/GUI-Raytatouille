"""Drawing of the object space (medium of the source) in the layout (pure logic, numpy only)."""

from __future__ import annotations

import numpy as np
import pytest

from rtt_explorer.layout_geometry import first_boundary, object_space_polygon


def test_first_boundary_skips_stops_in_front_of_the_first_interface():
    assert first_boundary(["stop", "lens", "lens", "detector"]) == 1
    assert first_boundary(["lens", "lens"]) == 0


def test_first_boundary_counts_a_mirror_or_thin_element_as_boundary():
    assert first_boundary(["stop", "mirror"]) == 1
    assert first_boundary(["thin_element", "detector"]) == 0


def test_first_boundary_is_none_without_a_boundary():
    assert first_boundary(["stop", "stop"]) is None
    assert first_boundary([]) is None


def test_polygon_of_a_flat_interface_is_a_rectangle_from_the_source_to_the_surface():
    profile = np.array([[0.0, -2.0], [0.0, 2.0]])
    poly = object_space_polygon(-0.06, profile)
    assert poly.shape == (4, 2)
    assert set(map(tuple, poly.round(9))) == {(-0.06, 2.0), (-0.06, -2.0), (0.0, 2.0), (0.0, -2.0)}
    # the polygon is simple: the area is width times height
    x, y = poly[:, 0], poly[:, 1]
    area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    assert area == pytest.approx(0.06 * 4.0)


def test_polygon_follows_a_curved_interface():
    lateral = np.linspace(-2.0, 2.0, 5)
    profile = np.column_stack([lateral**2 / 8.0, lateral])  # a dome-like sag towards +z
    poly = object_space_polygon(-1.0, profile)
    # source side: two corners at z = -1 with the height of the profile
    assert (poly[:, 0] == -1.0).sum() == 2
    assert {tuple(p) for p in poly if p[0] == -1.0} == {(-1.0, 2.0), (-1.0, -2.0)}
    # the interface points keep their z
    on_surface = {tuple(np.round(p, 9)) for p in poly if p[0] != -1.0}
    assert on_surface == {tuple(np.round(p, 9)) for p in profile}


def test_polygon_orders_the_profile_from_top_to_bottom_whatever_its_order():
    profile = np.array([[0.0, 2.0], [0.0, -2.0], [0.0, 0.0]])
    poly = object_space_polygon(-1.0, profile)
    interface = poly[poly[:, 0] == 0.0]
    assert interface[:, 1].tolist() == sorted(interface[:, 1].tolist(), reverse=True)


def test_polygon_height_can_be_given():
    profile = np.array([[0.0, -2.0], [0.0, 2.0]])
    poly = object_space_polygon(-1.0, profile, half_height=3.0)
    source_side = poly[poly[:, 0] == -1.0]
    assert sorted(source_side[:, 1].tolist()) == [-3.0, 3.0]


@pytest.mark.parametrize("profile", [np.zeros((0, 2)), np.array([[0.0, np.nan], [0.0, 1.0]]), np.zeros((3, 3))])
def test_polygon_rejects_an_empty_non_finite_or_wrong_shaped_profile(profile):
    with pytest.raises(ValueError):
        object_space_polygon(-1.0, profile)


def test_polygon_rejects_a_source_behind_the_surface():
    profile = np.array([[0.0, -2.0], [0.0, 2.0]])
    with pytest.raises(ValueError):
        object_space_polygon(1.0, profile)
