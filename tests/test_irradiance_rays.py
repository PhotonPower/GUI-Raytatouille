"""Irradiance on a surface from traced rays (needs the library and a checkout, like ``test_app.py``)."""

from __future__ import annotations

import numpy as np
import pytest

pytestmark = pytest.mark.library


def need() -> None:
    from rtt_explorer.compat import FEATURES

    if not FEATURES.irradiance:
        pytest.skip("Bibliotheksfunktion fehlt: irradiance")


def load(rtt_repo, name, with_glass=False):
    import raytatouille as rt

    lib = rt.MaterialLibrary()
    if with_glass:
        lib.add_catalog(str(rtt_repo / "tests" / "catalogs" / "schott.agf"))
    return rt.compile(rt.load(str(rtt_repo / "tests" / "reference" / name)), lib)


def aim():
    import raytatouille as rt

    return rt.trace.Aiming.PARAXIAL


def test_path_events_are_the_surfaces_of_the_path_in_order(rtt_repo):
    need()
    from rtt_explorer.irradiance_rays import path_events

    comp = load(rtt_repo, "m1/singlet_const.rtt.json")
    events = path_events(comp, "main", 0, 1, aim())
    assert [comp.surface_ids[i] for i in events] == ["STO", "L1.S1", "L1.S2", "IMG"]


def test_footprint_on_a_lens_surface_matches_the_library_call(rtt_repo):
    need()
    import raytatouille as rt

    from rtt_explorer.irradiance_rays import irradiance, trace_rays

    comp = load(rtt_repo, "m1/singlet_const.rtt.json")
    surface = comp.surface_ids.index("L1.S1")
    traced = trace_rays(comp, "main", 0, 1, 2000, aim(), surface)
    assert traced.form == "paths" and traced.launched == 2000
    got = irradiance(comp, traced, surface, None, 32, 32, None)
    rays = rt.trace.make_rays(comp, rt.trace.PointListPupil(*traced.pupil), path="main", fields=[0], wavelength=1,
                              aiming=aim())
    _, paths = rt.trace.trace(comp, rays, path="main", record_path=True)
    expected = rt.analysis.irradiance_map(comp, paths, surface="L1.S1", nx=32, ny=32)
    assert np.array_equal(got.values, expected.values)
    assert got.surface_id == "L1.S1"


def test_last_surface_uses_the_batch_form_with_many_rays_and_conserves_the_power(rtt_repo):
    need()
    from rtt_explorer.irradiance_rays import irradiance, trace_rays

    comp = load(rtt_repo, "m1/singlet_const.rtt.json")
    image = comp.surface_ids.index("IMG")
    traced = trace_rays(comp, "main", 0, 1, 200_000, aim(), image)
    assert traced.form == "batch"
    m = irradiance(comp, traced, image, None, 40, 40, (-1.0, 1.0, -1.0, 1.0))
    dx, dy = np.diff(m.x_edges)[0], np.diff(m.y_edges)[0]
    assert m.values.sum() * dx * dy == pytest.approx(m.weight_counted, rel=1e-9)
    assert m.rays_counted + m.outside_grid.count + m.vignetted.count + m.not_reached.count == traced.launched


def test_automatic_extent_contains_every_hit(rtt_repo):
    need()
    from rtt_explorer.irradiance_rays import auto_extent, irradiance, trace_rays

    comp = load(rtt_repo, "m1/singlet_const.rtt.json")
    image = comp.surface_ids.index("IMG")
    traced = trace_rays(comp, "main", 0, 1, 5000, aim(), image)
    extent = auto_extent(comp, traced, image, None)
    m = irradiance(comp, traced, image, None, 32, 32, extent)
    assert m.outside_grid.count == 0
    assert m.rays_counted == int(traced.alive)


def test_event_choice_separates_the_visits_of_a_surface_in_a_double_pass(rtt_repo):
    need()
    from rtt_explorer.irradiance_logic import visits
    from rtt_explorer.irradiance_rays import irradiance, path_events, trace_rays

    comp = load(rtt_repo, "m7/double_pass.rtt.json", with_glass=True)
    events = path_events(comp, "main", 0, 0, aim())
    surface = comp.surface_ids.index("P.S2")
    first, second = visits(events)[surface]
    traced = trace_rays(comp, "main", 0, 0, 500, aim(), surface)
    both = irradiance(comp, traced, surface, None, 8, 8, (-20.0, 20.0, -20.0, 20.0))
    one = irradiance(comp, traced, surface, first, 8, 8, (-20.0, 20.0, -20.0, 20.0))
    two = irradiance(comp, traced, surface, second, 8, 8, (-20.0, 20.0, -20.0, 20.0))
    assert list(both.events) == [first, second]
    assert one.weight_counted + two.weight_counted == pytest.approx(both.weight_counted, rel=1e-9)


def test_aperture_mode_on_a_surface_without_aperture_is_a_german_error(rtt_repo):
    need()
    from rtt_explorer.irradiance_rays import irradiance_extent

    comp = load(rtt_repo, "m1/singlet_const.rtt.json")
    image = comp.surface_ids.index("IMG")
    with pytest.raises(ValueError, match="keine Apertur"):
        irradiance_extent(comp, image, "aperture", None, None)


def test_too_many_rays_for_a_recorded_surface_is_a_german_error(rtt_repo):
    need()
    from rtt_explorer.irradiance_logic import MAX_PATH_RAYS
    from rtt_explorer.irradiance_rays import trace_rays

    comp = load(rtt_repo, "m1/singlet_const.rtt.json")
    with pytest.raises(ValueError, match="höchstens"):
        trace_rays(comp, "main", 0, 1, MAX_PATH_RAYS + 1, aim(), comp.surface_ids.index("L1.S1"))
