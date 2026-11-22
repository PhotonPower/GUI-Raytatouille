"""Feature flags for the library functions added in 0.9.0, 0.10.0 and the commits after it."""

from __future__ import annotations

import dataclasses

import pytest

pytestmark = pytest.mark.library

NEW_FLAGS = (
    "tolerance",
    "irradiance",
    "design",
    "surface_types",
    "freeform",
    "anamorphic_first_order",
    "aperture_shapes",
    "inactive",
    "on_iteration",
    "object_reference",
    "stop_on_surface",
    "schemas",
)


def test_new_flags_exist_and_are_booleans():
    from rtt_explorer.compat import FEATURES

    for name in NEW_FLAGS:
        assert isinstance(getattr(FEATURES, name), bool), name


def test_flags_match_the_installed_library():
    """Each flag is the presence of one attribute; check them directly against raytatouille."""
    import raytatouille as rt

    from rtt_explorer.compat import FEATURES

    model = rt.model
    assert FEATURES.tolerance == (hasattr(rt, "tolerance") and hasattr(rt.tolerance, "monte_carlo"))
    assert FEATURES.irradiance == hasattr(rt.analysis, "irradiance_map")
    assert FEATURES.design == hasattr(getattr(rt, "design", None), "singlet")
    assert FEATURES.surface_types == hasattr(model, "Biconic")
    assert FEATURES.freeform == hasattr(model, "ZernikeFringeSag")
    assert FEATURES.anamorphic_first_order == hasattr(rt.paraxial, "first_order_section")
    assert FEATURES.aperture_shapes == hasattr(model, "PolygonAperture")
    assert FEATURES.inactive == hasattr(model.Element, "active")
    assert FEATURES.on_iteration == hasattr(rt.optim, "IterationState")
    assert FEATURES.object_reference == hasattr(model.ObjectSpace, "reference")
    assert FEATURES.stop_on_surface == hasattr(model.SystemAperture, "stop")
    assert FEATURES.schemas == hasattr(rt, "schema")


def test_every_flag_is_listed_in_the_sidebar_overview():
    from rtt_explorer.compat import FEATURES

    flags = {f.name for f in dataclasses.fields(FEATURES)}
    assert len(FEATURES.rows()) == len(flags)
    labels = [label for label, _ in FEATURES.rows()]
    assert len(set(labels)) == len(labels)
