"""Formatting of library diagnostics and ray losses (pure logic, no library needed)."""

from __future__ import annotations

import pytest

from rtt_explorer.messages import diagnostic_text, loss_rows, surface_for_location, unique

LOCATIONS = ["/root/children/0/surfaces/0", "/root/children/0/surfaces/1", "/root/children/1/surfaces/0",
             "/root/children/10/surfaces/0"]
IDS = ["L1.S1", "L1.S2", "STO", "IMG"]


def test_location_inside_a_surface_names_that_surface():
    assert surface_for_location("/root/children/0/surfaces/1/shape/base/radius", LOCATIONS, IDS) == "L1.S2"


def test_exact_surface_location_names_the_surface():
    assert surface_for_location("/root/children/1/surfaces/0", LOCATIONS, IDS) == "STO"


def test_prefix_must_end_at_a_pointer_segment():
    # "/root/children/1..." must not match "/root/children/10/..."
    assert surface_for_location("/root/children/10/surfaces/0/aperture", LOCATIONS, IDS) == "IMG"
    assert surface_for_location("/root/children/1", LOCATIONS, IDS) is None


@pytest.mark.parametrize("location", [None, "", "/paths/0", "/wavelengths/2"])
def test_location_outside_the_surfaces_names_nothing(location):
    assert surface_for_location(location, LOCATIONS, IDS) is None


def test_diagnostic_text_with_code_and_surface():
    text = diagnostic_text("rays.lost", "62 % of the rays are lost", "/root/children/1/surfaces/0", LOCATIONS, IDS)
    assert text == "62 % of the rays are lost (Fläche STO, Code `rays.lost`)"


def test_diagnostic_text_with_code_and_plain_location():
    assert diagnostic_text("stop.not_on_path", "msg", "/paths/0", LOCATIONS, IDS) == \
        "msg (Ort /paths/0, Code `stop.not_on_path`)"


def test_diagnostic_text_without_code_and_location_is_the_message():
    assert diagnostic_text("", "msg", None, LOCATIONS, IDS) == "msg"


def test_loss_rows_skip_arrived_and_empty_statuses():
    names = {0: "ALIVE", 1: "MISSED", 2: "VIGNETTED", 3: "TIR"}
    rows = loss_rows([80, 0, 15, 5], names, launched=100, alive=0)
    assert rows == [{"Status": "VIGNETTED", "Strahlen": 15, "Anteil (%)": 15.0},
                    {"Status": "TIR", "Strahlen": 5, "Anteil (%)": 5.0}]


def test_loss_rows_name_unknown_status_by_number():
    rows = loss_rows([1, 0, 0, 0, 0, 0, 0, 0, 3], {0: "ALIVE"}, launched=4, alive=0)
    assert rows == [{"Status": "8", "Strahlen": 3, "Anteil (%)": 75.0}]


def test_loss_rows_without_launched_rays_are_empty():
    assert loss_rows([0, 0], {0: "ALIVE", 1: "MISSED"}, launched=0, alive=0) == []


def test_unique_keeps_first_occurrence_order():
    assert unique(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]
