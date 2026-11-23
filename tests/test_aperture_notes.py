"""Stop surface and NA reading of the system aperture in the model view (fakes, plus the real library)."""

from __future__ import annotations

from types import SimpleNamespace as NS

import pytest

from rtt_explorer.model_table import aperture_notes


def aperture(kind="ENTRANCE_PUPIL_DIAMETER", stop=None, reading="PARAXIAL"):
    return NS(type=NS(name=kind), stop=None if stop is None else NS(surface=stop),
              reading=None if reading is None else NS(name=reading))


def test_default_aperture_has_no_notes():
    assert aperture_notes(aperture()) == []


def test_stop_surface_is_named():
    assert aperture_notes(aperture(stop="L2.S1")) == [
        "Blende: die Apertur der Fläche L2.S1 (aperture.stop); ohne sie gilt das Blendenelement"]


def test_na_reading_paraxial_and_real():
    assert aperture_notes(aperture("OBJECT_SPACE_NA")) == ["NA paraxial gelesen: u = NA / n (Standard)"]
    assert aperture_notes(aperture("OBJECT_SPACE_NA", reading="REAL")) == [
        "NA real gelesen: der Randstrahl hat n·sin U = NA (aperture.reading)"]


def test_reading_matters_only_for_the_na_type():
    assert aperture_notes(aperture("ENTRANCE_PUPIL_DIAMETER", reading="REAL")) == []


def test_both_notes_and_old_library():
    assert len(aperture_notes(aperture("OBJECT_SPACE_NA", stop="S", reading="REAL"))) == 2
    assert aperture_notes(NS(type=NS(name="STOP_SIZE"))) == []


@pytest.mark.library
@pytest.mark.parametrize("name, fragment", [
    ("m2/cooke_triplet_surface_stop.rtt.json", "Fläche L2.S1"),
    ("r3/immersion_real_na.rtt.json", "NA real gelesen"),
    ("m2/cooke_triplet.rtt.json", None),
])
def test_real_library_files(rtt_repo, name, fragment):
    import raytatouille as rt

    notes = aperture_notes(rt.load(str(rtt_repo / "tests" / "reference" / name)).aperture)
    if fragment is None:
        assert notes == []
    else:
        assert any(fragment in n for n in notes)
