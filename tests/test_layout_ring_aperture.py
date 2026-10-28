"""The layout draws the material of a ring aperture: thick blocked centre and jaws, thin open ring.

Needs the library, like ``test_app.py``."""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.library


def ring_system(kind: str) -> dict:
    """Singlet with a ring aperture (inner radius 2 mm, outer radius 7 mm) of the given element
    type at z = 30 mm, behind the lens (no tracing needed, the test only draws)."""
    return {
        "schema_version": "0.2.0", "name": "ring",
        "units": {"length": "mm", "wavelength": "um"},
        "wavelengths": [{"um": 0.5876, "reference": True}],
        "aperture": {"type": "epd", "value": 10.0},
        "fields": {"type": "angle_deg", "points": [{}]},
        "root": {"type": "assembly", "name": "system", "children": [
            {"type": "stop", "name": "stop",
             "surfaces": [{"id": "STO", "aperture": {"type": "circular", "radius": 5.0}}]},
            {"type": "lens", "name": "L1", "pose": {"position": [0, 0, 5.0]}, "material": "CONST:1.5168",
             "surfaces": [
                 {"id": "L1.S1", "shape": {"base": {"type": "conic", "radius": 51.68}},
                  "aperture": {"type": "circular", "radius": 12.7}},
                 {"id": "L1.S2", "pose": {"position": [0, 0, 4.0]}, "aperture": {"type": "circular", "radius": 12.7}}]},
            {"type": kind, "name": "ring", "pose": {"position": [0, 0, 30.0]},
             "surfaces": [{"id": "RING", "aperture": {"type": "circular", "radius": 7.0, "inner_radius": 2.0}}]},
            {"type": "detector", "name": "image", "pose": {"position": [0, 0, 106.363]}, "surfaces": [{"id": "IMG"}]},
        ]},
        "paths": [{"name": "main", "events": [{"surface": "STO"}, {"surface": "L1.S1"}, {"surface": "L1.S2"},
                                              {"surface": "RING"}]}],
    }


def lines_at(ax, z: float):
    """(lateral min, lateral max, line width, colour) of the lines drawn at z."""
    return sorted((min(line.get_ydata()), max(line.get_ydata()), line.get_linewidth(), line.get_color())
                  for line in ax.lines if abs(float(line.get_xdata()[0]) - z) < 1e-9)


@pytest.mark.parametrize("kind", ["thin_element", "stop"])
def test_ring_aperture_draws_a_thick_centre_and_thick_jaws_and_a_thin_open_ring(tmp_path, kind):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import raytatouille as rt

    from rtt_explorer.drawing import draw_geometry_api

    system = ring_system(kind)
    if kind == "stop":  # only one stop element is allowed: the aperture stop becomes a plain surface
        system["root"]["children"][0] = {"type": "detector", "name": "pupil",
                                         "surfaces": [{"id": "STO", "aperture": {"type": "circular", "radius": 5.0}}]}
    path = tmp_path / "ring.rtt.json"
    path.write_text(json.dumps(system), encoding="utf-8")
    comp = rt.compile(rt.load(path))
    fig, ax = plt.subplots()
    draw_geometry_api(ax, comp, "yz", {}, 10.0, False)
    thick = [(lo, hi) for lo, hi, lw, _ in lines_at(ax, 30.0) if lw == 3]
    thin = [(lo, hi) for lo, hi, lw, _ in lines_at(ax, 30.0) if lw < 1]
    plt.close(fig)
    assert (-2.0, 2.0) in [(round(lo, 6), round(hi, 6)) for lo, hi in thick]  # blocked centre
    assert len(thick) == 3  # centre and two jaws
    assert sorted((round(lo, 6), round(hi, 6)) for lo, hi in thin) == [(-7.0, -2.0), (2.0, 7.0)]  # open ring
