"""The layout draws polygon apertures at their size and obscurations as blocked bands (needs the library)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.library


def compiled(rtt_repo, name):
    import raytatouille as rt

    from rtt_explorer.compat import FEATURES

    if not FEATURES.aperture_shapes:
        pytest.skip("Bibliotheksfunktion fehlt: aperture_shapes")
    return rt.compile(rt.load(str(rtt_repo / "tests" / "reference" / "m8" / name)), rt.MaterialLibrary())


def draw(comp, plane):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from rtt_explorer.drawing import draw_geometry_api

    fig, ax = plt.subplots()
    draw_geometry_api(ax, comp, plane, {}, 10.0, False)
    return fig, ax


def blocked(ax):
    """(z, lateral min, lateral max) of the obscuration lines, sorted."""
    return sorted((round(float(line.get_xdata().mean()), 3), round(float(min(line.get_ydata())), 3),
                   round(float(max(line.get_ydata())), 3)) for line in ax.lines if line.get_gid() == "obscuration")


def test_polygon_aperture_extent_is_the_cut_through_the_axis(rtt_repo):
    import raytatouille as rt

    from rtt_explorer.drawing import aperture_extent

    surfs = rt.layout.surfaces(compiled(rtt_repo, "hexagon_mirror.rtt.json"))
    mirror, detector = surfs[1], surfs[2]
    assert aperture_extent(mirror, "yz") == pytest.approx(34.0)  # through two opposite vertices
    assert aperture_extent(mirror, "xz") == pytest.approx(29.445, abs=1e-3)  # across the flats
    assert aperture_extent(detector, "yz") == pytest.approx(2.0)  # polygon with 4 vertices


def test_spider_and_central_obstruction_are_drawn_on_the_stop_in_yz(rtt_repo):
    import matplotlib.pyplot as plt
    import raytatouille as rt

    comp = compiled(rtt_repo, "spider_telescope.rtt.json")
    z_stop = float(rt.layout.surfaces(comp)[0].translation[2])
    fig, ax = draw(comp, "yz")
    lines = blocked(ax)
    plt.close(fig)
    # at the stop: central disc radius 10, arm along x seen edge-on (±0.5), arm along y (±31)
    assert [(lo, hi) for z, lo, hi in lines if abs(z - z_stop) < 1e-6] == [(-31.0, 31.0), (-10.0, 10.0), (-0.5, 0.5)]
    assert len(lines) == 3


def test_decentred_ellipse_on_the_mirror_shows_only_where_the_section_hits_it(rtt_repo):
    import matplotlib.pyplot as plt
    import raytatouille as rt

    comp = compiled(rtt_repo, "spider_telescope.rtt.json")
    z_mirror = float(rt.layout.surfaces(comp)[1].translation[2])
    out = {}
    for plane in ("yz", "xz"):
        fig, ax = draw(comp, plane)
        out[plane] = [1 for z, _, _ in blocked(ax) if abs(z - z_mirror) < 1.0]
        plt.close(fig)
    # the ellipse sits at (20, 5) with half height 1.98: neither the line x = 0 nor y = 0 reaches it
    assert out == {"yz": [], "xz": []}


def test_system_without_obscurations_draws_none(rtt_repo):
    import matplotlib.pyplot as plt
    import raytatouille as rt

    comp = rt.compile(rt.load(str(rtt_repo / "tests" / "reference" / "m1" / "singlet_const.rtt.json")),
                      rt.MaterialLibrary())
    fig, ax = draw(comp, "yz")
    assert blocked(ax) == []
    plt.close(fig)


@pytest.mark.parametrize("name", ["m8/hexagon_mirror.rtt.json", "m8/spider_telescope.rtt.json"])
@pytest.mark.parametrize("plane", ["yz", "xz"])
def test_layout_view_renders_polygon_and_obscured_systems(rtt_repo, monkeypatch, name, plane):
    from pathlib import Path

    from test_app import pick_reference, start, widget
    from test_app_library_06 import need, ok, view

    need("aperture_shapes")
    at = pick_reference(start(rtt_repo, monkeypatch), str(Path(name)))
    at = view(at, "Layout")
    ok(at)
    at = widget(at, "radio", "Schnittebene").set_value(plane).run()
    ok(at)
