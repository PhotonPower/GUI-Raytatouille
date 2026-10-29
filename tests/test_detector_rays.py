"""Detector image: the rays of ``compute_hits`` against closed formulas. They need the library, like
``test_app.py``."""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

pytestmark = pytest.mark.library

H = 20.0  # distance of the point source in front of the stop, mm
R_STOP = 15.0  # radius of the stop, mm
L = 20.0  # distance of the detector behind the stop, mm


def system(*, finite: bool, detector_radius: float | None = None):
    """Stop (r = 15 mm) at z = 0 and a detector at z = 20 mm in VACUUM; a point source 20 mm in front
    of the stop (finite) or at infinity (parallel rays on the axis). Only stop and detector: no ray
    is refracted, so every ray is a straight line and every weight 1 before the emission model."""
    import raytatouille as rt

    detector = {"id": "IMG"}
    if detector_radius is not None:
        detector["aperture"] = {"type": "circular", "radius": detector_radius}
    doc = {
        "schema_version": "0.7.0",
        "units": {"length": "mm", "wavelength": "um"},
        "environment": {"medium": "VACUUM"},
        "object": {"at_infinity": False, "distance": H} if finite else {"at_infinity": True},
        "wavelengths": [{"um": 0.5876, "reference": True}],
        "aperture": {"type": "stop_size"},
        "fields": {"type": "object_height" if finite else "angle_deg", "points": [{}]},
        "root": {"type": "assembly", "name": "system", "children": [
            {"type": "stop", "name": "stop", "surfaces": [
                {"id": "STO", "aperture": {"type": "circular", "radius": R_STOP}}]},
            {"type": "detector", "name": "image", "pose": {"position": [0, 0, L]}, "surfaces": [detector]},
        ]},
        "paths": [{"name": "main", "events": "auto"}],
    }
    return rt.compile(rt.System.from_json(json.dumps(doc)))


def hits(comp, *, isotropic: bool, n: int = 200_000, aiming=None):
    import raytatouille as rt

    from rtt_explorer.detector_rays import compute_hits

    return compute_hits(comp, "main", 0, 0, n, aiming or rt.trace.Aiming.REAL, isotropic)


def test_parallel_rays_through_a_stop_give_a_uniform_disk_on_the_detector():
    h = hits(system(finite=False), isotropic=False)
    r2 = h.x**2 + h.y**2
    assert h.arrived == h.launched == 200_000
    assert math.sqrt(r2.max()) <= R_STOP * (1 + 1e-9)
    assert r2.mean() == pytest.approx(R_STOP**2 / 2.0, rel=5e-3)  # uniform disk: <r^2> = R^2 / 2
    assert np.allclose(h.weight, 1.0)
    assert h.image_surface == "IMG"
    assert not h.isotropic  # an object at infinity has no emission model


def test_isotropic_weights_give_the_same_power_per_solid_angle():
    # A point source at distance H shines through the stop at angles up to alpha_max; the detector
    # at the same distance behind the stop magnifies by m = (H + L) / H = 2. The power inside the
    # detector radius 10 mm (stop radius 5 mm, cos(alpha) = H / sqrt(H^2 + r^2)) is the fraction
    # (1 - cos a_5) / (1 - cos a_15) of the total: the ratio of the solid angles.
    h = hits(system(finite=True), isotropic=True)
    cos_a = lambda r: H / math.sqrt(H * H + r * r)  # noqa: E731
    expected = (1 - cos_a(5.0)) / (1 - cos_a(R_STOP))
    inside = np.hypot(h.x, h.y) <= 10.0
    assert h.weight[inside].sum() / h.weight.sum() == pytest.approx(expected, rel=2e-2)
    # without the emission model the same rays are uniform in the stop plane: (5 / 15)^2
    plain = hits(system(finite=True), isotropic=False)
    inside = np.hypot(plain.x, plain.y) <= 10.0
    assert plain.weight[inside].sum() / plain.weight.sum() == pytest.approx((5.0 / R_STOP) ** 2, rel=2e-2)
    assert expected != pytest.approx((5.0 / R_STOP) ** 2, rel=0.2)
    assert h.isotropic


def test_the_mean_isotropic_weight_is_the_mean_of_cos_cubed_over_the_stop():
    # <cos^3> over the uniform disk of radius R at distance H: (2 H^3 / R^2) (1 / H - 1 / sqrt(H^2 + R^2))
    h = hits(system(finite=True), isotropic=True)
    expected = 2 * H**3 / R_STOP**2 * (1 / H - 1 / math.sqrt(H * H + R_STOP**2))
    assert h.weight.mean() == pytest.approx(expected, rel=5e-3)


def test_rays_that_miss_the_detector_aperture_are_counted_as_lost():
    h = hits(system(finite=False, detector_radius=10.0), isotropic=False, n=50_000)
    assert h.arrived < h.launched
    assert math.sqrt((h.x**2 + h.y**2).max()) <= 10.0 * (1 + 1e-9)
    # fraction of the disk of radius 15 inside radius 10
    assert h.arrived / h.launched == pytest.approx((10.0 / R_STOP) ** 2, rel=1e-2)


def test_no_arriving_ray_is_an_error():
    comp = system(finite=False, detector_radius=1.0e-6)
    with pytest.raises(ValueError, match="Strahl"):
        hits(comp, isotropic=False, n=100)


def test_the_hexapolar_fallback_gives_the_same_disk_without_the_point_list():
    import raytatouille as rt

    from rtt_explorer.detector_rays import compute_hits

    h = compute_hits(system(finite=False), "main", 0, 0, 20_000, rt.trace.Aiming.REAL, False, point_list=False)
    r2 = h.x**2 + h.y**2
    assert h.launched >= 20_000
    assert r2.mean() == pytest.approx(R_STOP**2 / 2.0, rel=2e-2)
