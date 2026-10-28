"""Layout: object space tint and lost rays drawn up to the last surface. They need the library
and a checkout, like ``test_app.py``."""

from __future__ import annotations

import pytest

from test_app import pick_reference, start, widget
from test_app_library_06 import need, ok, ref, view

pytestmark = pytest.mark.library

IN_GLASS = "r3/object_in_glass.rtt.json"


def need_reference(rtt_repo, name: str) -> None:
    if not (rtt_repo / "tests" / "reference" / name).is_file():
        pytest.skip(f"Referenzsystem fehlt im Checkout: {name}")


def layout(rtt_repo, monkeypatch, name: str | None = None):
    need("paths")
    at = start(rtt_repo, monkeypatch)
    if name is not None:
        need("object_medium")
        need_reference(rtt_repo, name)
        at = pick_reference(at, ref(name))
    at = view(at, "Layout")
    ok(at)
    return at


def test_truncating_lost_rays_is_an_option_that_is_off_by_default(rtt_repo, monkeypatch):
    at = layout(rtt_repo, monkeypatch)
    box = widget(at, "checkbox", "Verlorene Strahlen nur bis zur letzten Fläche")
    assert not box.value
    ok(box.check().run())
    ok(widget(at, "checkbox", "Verlorene Strahlen nur bis zur letzten Fläche").uncheck().run())


def test_the_object_space_of_a_source_in_glass_is_tinted_and_explained(rtt_repo, monkeypatch):
    at = layout(rtt_repo, monkeypatch, IN_GLASS)
    captions = [c.value for c in at.caption]
    assert any("Objektraum" in c and "CONST:1.53" in c for c in captions), captions


def test_a_system_without_an_object_medium_has_no_object_space_caption(rtt_repo, monkeypatch):
    at = layout(rtt_repo, monkeypatch)
    assert not any("Objektraum" in c.value for c in at.caption)


def test_the_options_work_together_with_the_zoom_buttons(rtt_repo, monkeypatch):
    at = layout(rtt_repo, monkeypatch, IN_GLASS)
    at = widget(at, "checkbox", "Verlorene Strahlen nur bis zur letzten Fläche").check().run()
    ok(at)
    at = widget(at, "button", "Auf Quelle zoomen").click().run()
    ok(at)
    at = widget(at, "button", "Gesamtes System").click().run()
    ok(at)


def test_draw_object_medium_tints_from_the_source_to_the_first_interface(rtt_repo):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import raytatouille as rt

    from rtt_explorer.compat import FEATURES
    from rtt_explorer.drawing import draw_object_medium

    if not FEATURES.object_medium:
        pytest.skip("Bibliotheksfunktion fehlt: object_medium")
    need_reference(rtt_repo, IN_GLASS)
    comp = rt.compile(rt.load(rtt_repo / "tests" / "reference" / IN_GLASS))
    interface = list(comp.surface_ids).index("H.S1")  # the plane where the glass of the object ends
    fig, ax = plt.subplots()
    assert draw_object_medium(ax, comp, "yz", interface, -0.5, {}, 10.0)
    (patch,) = ax.patches
    z, lateral = patch.get_xy()[:, 0], patch.get_xy()[:, 1]
    plt.close(fig)
    assert (z.min(), z.max()) == pytest.approx((-0.5, 0.5))  # source at z = -0.5, interface at 0.5
    assert (lateral.min(), lateral.max()) == pytest.approx((-2.4, 2.4))  # aperture of the interface


def test_draw_object_medium_draws_nothing_if_the_source_is_behind_the_surface(rtt_repo):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import raytatouille as rt

    from rtt_explorer.compat import FEATURES
    from rtt_explorer.drawing import draw_object_medium

    if not FEATURES.object_medium:
        pytest.skip("Bibliotheksfunktion fehlt: object_medium")
    need_reference(rtt_repo, IN_GLASS)
    comp = rt.compile(rt.load(rtt_repo / "tests" / "reference" / IN_GLASS))
    fig, ax = plt.subplots()
    assert not draw_object_medium(ax, comp, "yz", list(comp.surface_ids).index("H.S1"), 3.0, {}, 10.0)
    assert not ax.patches
    plt.close(fig)
