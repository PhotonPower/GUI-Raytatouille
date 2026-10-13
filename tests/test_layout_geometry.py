"""Section geometry of planar surfaces and exit stubs of recorded paths (pure logic, numpy only)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from rtt_explorer.layout_geometry import exit_segments, plane_segment, stub_length


def rot_x(deg: float) -> np.ndarray:
    """Rotation about x; its columns are the local axes in global coordinates."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def rot_z(deg: float) -> np.ndarray:
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def test_untilted_surface_on_the_axis_is_a_vertical_line_in_both_planes():
    for plane in ("yz", "xz"):
        z, lateral = plane_segment([0.0, 0.0, 30.0], np.eye(3), plane, -2.0, 3.0)
        assert z == pytest.approx([30.0, 30.0])
        assert lateral == pytest.approx([-2.0, 3.0])


def test_surface_off_the_axis_keeps_its_lateral_position():
    # Periscope: detector at y = 20
    z, y = plane_segment([0.0, 20.0, 80.0], np.eye(3), "yz", -5.0, 5.0)
    assert z == pytest.approx([80.0, 80.0])
    assert y == pytest.approx([15.0, 25.0])


def test_detector_turned_by_90_degrees_lies_along_z():
    # Michelson: detector at y = -50, rotation_deg [-90, 0, 0], facing +y
    z, y = plane_segment([0.0, -50.0, 50.0], rot_x(-90.0), "yz", -3.0, 3.0)
    assert sorted(z) == pytest.approx([47.0, 53.0])
    assert y == pytest.approx([-50.0, -50.0])


def test_tilted_surface_follows_its_tilt():
    z, y = plane_segment([0.0, 0.0, 10.0], rot_x(45.0), "yz", -1.0, 1.0)
    assert abs(z[1] - z[0]) == pytest.approx(math.sqrt(2.0))
    assert abs(y[1] - y[0]) == pytest.approx(math.sqrt(2.0))


def test_rotation_about_the_optical_axis_still_cuts_the_section_plane():
    # Turned by 90 degrees about z, local y points along -x; the cut with the yz plane stays vertical
    z, y = plane_segment([0.0, 0.0, 5.0], rot_z(90.0), "yz", -1.0, 1.0)
    assert z == pytest.approx([5.0, 5.0])
    assert sorted(y) == pytest.approx([-1.0, 1.0])


def recorded(lost_at=(-1, -1)):
    position = np.array([[[0.0, 0.0, 0.0], [0.0, 0.0, 10.0]],
                         [[0.0, 1.0, 0.0], [0.0, 1.0, 10.0]]])
    direction = np.array([[[0.0, 0.0, 1.0], [0.0, 1.0, 0.0]],
                          [[0.0, 0.0, 1.0], [0.0, 1.0, 0.0]]])
    return position, direction, np.array(lost_at)


def test_exit_segments_continue_along_the_last_direction():
    start, end = exit_segments(*recorded(), length=4.0)
    assert start == pytest.approx(np.array([[0.0, 0.0, 10.0], [0.0, 1.0, 10.0]]))
    assert end == pytest.approx(np.array([[0.0, 4.0, 10.0], [0.0, 5.0, 10.0]]))


def test_exit_segments_skip_lost_and_unfinished_rays():
    position, direction, _ = recorded()
    position[1, 1] = np.nan
    start, end = exit_segments(position, direction, np.array([-1, -1]), length=1.0)
    assert len(start) == len(end) == 1
    start, _ = exit_segments(*recorded(lost_at=(0, -1)), length=1.0)
    assert len(start) == 1


def test_exit_segments_of_a_path_without_events_are_empty():
    start, end = exit_segments(np.zeros((2, 1, 3)), np.zeros((2, 1, 3)), np.array([-1, -1]), length=1.0)
    assert start.shape == end.shape == (0, 3)


def test_stub_length_is_a_fraction_of_the_drawn_extent():
    assert stub_length([np.array([0.0, 100.0])], [np.array([-5.0, 5.0])]) == pytest.approx(30.0)
    assert stub_length([np.array([0.0, 10.0])], [np.array([0.0, 40.0])]) == pytest.approx(12.0)
    assert stub_length([], []) == pytest.approx(0.3)  # at least 1 mm of extent
