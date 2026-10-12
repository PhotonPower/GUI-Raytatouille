"""Pupil point lists typed by the user and the ray nearest to a point (pure logic)."""

from __future__ import annotations

import math

import pytest

from rtt_explorer.pupil_points import jones_text, nearest_index, parse_pupil_points


def test_points_separated_by_comma_semicolon_or_blanks():
    text = "0, 0\n0.5;0.5\n  -1   0  \n\n# comment\n0.25,-0.75"
    assert parse_pupil_points(text) == ([0.0, 0.5, -1.0, 0.25], [0.0, 0.5, 0.0, -0.75])


def test_points_outside_the_unit_circle_are_allowed():
    assert parse_pupil_points("1.2 0.9") == ([1.2], [0.9])


@pytest.mark.parametrize(("text", "message"), [
    ("", "Mindestens ein Punkt"),
    ("# nur Kommentar", "Mindestens ein Punkt"),
    ("0.5", "Zeile 1: zwei Zahlen"),
    ("0 0\n1 2 3", "Zeile 2: zwei Zahlen"),
    ("0 x", "Zeile 1: 'x' ist keine Zahl"),
    ("0 nan", "Zeile 1: nur endliche Zahlen"),
])
def test_bad_point_lists_give_german_errors(text, message):
    with pytest.raises(ValueError, match=message):
        parse_pupil_points(text)


def test_nearest_index_finds_the_ray_closest_to_the_point():
    xs, ys = [3.0, 0.1, -2.0], [0.0, -0.1, 1.0]
    assert nearest_index(xs, ys) == 1
    assert nearest_index(xs, ys, -2.0, 1.2) == 2


def test_jones_text_gives_amplitude_and_phase():
    assert jones_text(complex(0.0, 0.5)) == "0.5000 ∠ 90.00°"
    assert jones_text(complex(-1.0, 0.0)) == "1.0000 ∠ 180.00°"
    assert jones_text(complex(math.nan, 0.0)) == "–"
