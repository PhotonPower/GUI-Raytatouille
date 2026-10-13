"""Smoke tests of the views for the functions of Raytatouille 0.5 and 0.6 (prescription, model,
paths and ghosts, diagnostics). They need the library and a checkout, like ``test_app.py``."""

from __future__ import annotations

from pathlib import Path

import pytest

from test_app import metric, pick_reference, start, widget

pytestmark = pytest.mark.library


def need(flag: str) -> None:
    """Skip when the installed library lacks the function (imported here: needs raytatouille)."""
    from rtt_explorer.compat import FEATURES

    if not getattr(FEATURES, flag):
        pytest.skip(f"Bibliotheksfunktion fehlt: {flag}")


def ref(name: str) -> str:
    """Label of a reference system as the app shows it (platform path separator)."""
    return str(Path(name))


def view(at, name: str):
    return widget(at, "radio", "Analyse").set_value(name).run()


def table(at, column: str):
    """The first table of the page with the given column (the header has its own tables)."""
    return next(df.value for df in at.dataframe if column in df.value.columns)


def ok(at) -> None:
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]


def test_prescription_of_the_singlet_matches_the_library_reference(rtt_repo, monkeypatch):
    need("prescription")
    # Library test test_compile_paraxial.py: F/# = 5.0, NA = 0.1, total track 106.363 mm for n' = 1. The app
    # compiles m0/singlet in air (Ciddor, n' about 1.00027), so F/# = 5 / n' and NA = 0.1 n' (rel. 3e-4).
    at = pick_reference(start(rtt_repo, monkeypatch), ref("m0/singlet.rtt.json"))
    at = view(at, "Prescription")
    ok(at)
    assert metric(at, "Arbeitsblende (paraxial)") == pytest.approx(5.0, rel=1e-3)
    assert metric(at, "Bild-NA (paraxial)") == pytest.approx(0.1, rel=1e-3)
    assert metric(at, "Baulänge") == pytest.approx(106.363, abs=1e-3)
    assert len(table(at, "y Rand (mm)")) == 4  # stop, two lens surfaces, image


def test_model_view_lists_the_surfaces_of_the_cooke_triplet(rtt_repo, monkeypatch):
    need("model")
    at = view(start(rtt_repo, monkeypatch), "Modell")
    ok(at)
    surfaces = table(at, "Fläche")
    assert len(surfaces) >= 7  # three lenses with two surfaces each, stop and image
    assert surfaces["Art"].isin(["Linse"]).sum() == 6


def test_ghost_ranking_of_the_cooke_triplet(rtt_repo, monkeypatch):
    need("ghosts")
    at = view(start(rtt_repo, monkeypatch), "Pfade & Ghosts")
    ok(at)
    at = widget(at, "checkbox", "Ghost-Ranking berechnen").check().run()
    ok(at)
    assert metric(at, "Ghosts") == 15  # 6 refracting surfaces: 6 * 5 / 2 two-reflection ghosts
    ranking = table(at, "rel. Bestrahlungsstärke")
    values = ranking["rel. Bestrahlungsstärke"].to_numpy()
    assert (values[:-1] >= values[1:]).all()  # sorted by the library


def test_michelson_paths_with_the_free_beam(rtt_repo, monkeypatch):
    need("path_eval")
    # Library example ghosts.py: test arm transmits 0.25, the return paths differ by 15 mm
    at = pick_reference(start(rtt_repo, monkeypatch), ref("m4/michelson_offset.rtt.json"))
    at = view(at, "Pfade & Ghosts")
    assert not at.exception, [e.value for e in at.exception]
    paths = table(at, "Mittel").set_index("Pfad")
    assert paths.loc["test arm", "Mittel"] == pytest.approx(0.25, abs=1e-6)
    widget(at, "selectbox", "Pfad a").set_value("reference arm")
    at = widget(at, "selectbox", "Pfad b").set_value("test arm").run()
    assert not at.exception
    assert metric(at, "Δ Hauptstrahl") == pytest.approx(15.0, abs=1e-6)


def drawn_rays(at) -> int:
    """Ray count from the caption below the layout ("Alle N gezeichneten Strahlen ...")."""
    return int(next(c.value for c in at.caption if c.value.startswith("Alle ")).split()[1])


def test_layout_draws_both_arms_of_the_michelson(rtt_repo, monkeypatch):
    need("paths")
    # The library traces one path at a time; the beam splitter does not split rays at run time.
    at = view(pick_reference(start(rtt_repo, monkeypatch), ref("m0/michelson.rtt.json")), "Layout")
    ok(at)
    assert not at.warning, [w.value for w in at.warning]
    all_paths = widget(at, "checkbox", "Alle Pfade zeichnen")
    assert all_paths.value  # default on
    both = drawn_rays(at)
    at = all_paths.uncheck().run()
    ok(at)
    assert both == 2 * drawn_rays(at)


EXIT_NOTE = "Blass: Austrittsrichtung nach dem letzten Ereignis"


def layout_figure(rtt_repo, monkeypatch, name: str):
    """(app, last layout figure) of a reference system; the figure is taken from the view's show()."""
    need("layout")
    figures = []
    monkeypatch.setattr("rtt_explorer.views.layout.show", figures.append)
    at = view(pick_reference(start(rtt_repo, monkeypatch), ref(name)), "Layout")
    ok(at)
    return at, figures[-1]


def detector_lines(fig):
    return [line for line in fig.axes[0].lines if line.get_color() == "tab:red" and line.get_linestyle() == "-"]


@pytest.mark.parametrize(("name", "y_mid"), [("m3/metal_periscope.rtt.json", 20.0), ("m0/michelson.rtt.json", -50.0)])
def test_detector_is_drawn_at_its_position(rtt_repo, monkeypatch, name, y_mid):
    _, fig = layout_figure(rtt_repo, monkeypatch, name)
    (line,) = detector_lines(fig)
    assert sum(line.get_ydata()) / 2 == pytest.approx(y_mid, abs=1e-6)


def test_michelson_detector_lies_along_z(rtt_repo, monkeypatch):
    _, fig = layout_figure(rtt_repo, monkeypatch, "m0/michelson.rtt.json")
    (line,) = detector_lines(fig)
    z = line.get_xdata()
    assert z[0] != pytest.approx(z[1])  # turned by 90 degrees: a segment along z, not across
    assert line.get_ydata() == pytest.approx([-50.0, -50.0])


def test_rays_leaving_the_last_surface_get_an_exit_stub(rtt_repo, monkeypatch):
    # The path tir ends with the total internal reflection at P.S2; the rays leave it towards +y.
    at, fig = layout_figure(rtt_repo, monkeypatch, "m3/tir_prism.rtt.json")
    assert any(c.value.startswith(EXIT_NOTE) for c in at.caption)
    stubs = [line for line in fig.axes[0].lines if line.get_alpha() is not None and line.get_alpha() < 1]
    assert stubs
    for line in stubs:
        z, y = line.get_xdata(), line.get_ydata()
        assert y[1] - y[0] > 1.0 and z[1] == pytest.approx(z[0], abs=1e-6)


def test_free_beam_defaults_follow_a_change_of_system(rtt_repo, monkeypatch):
    # Michelson: first surface at z = 50, EPD 5; TIR prism: first surface at z = 0, EPD 10. Without
    # a reset the beam would start at z = 40, behind the entrance face of the prism.
    need("layout")
    at = view(pick_reference(start(rtt_repo, monkeypatch), ref("m0/michelson.rtt.json")), "Layout")
    assert widget(at, "number_input", "Startebene z (mm)").value == pytest.approx(40.0)
    widget(at, "number_input", "Neigung um x (°)").set_value(1.0)
    at = pick_reference(at, ref("m3/tir_prism.rtt.json"))
    ok(at)
    assert widget(at, "number_input", "Startebene z (mm)").value == pytest.approx(-10.0)
    assert widget(at, "number_input", "Bündelradius (mm)").value == pytest.approx(5.0)
    assert widget(at, "number_input", "Neigung um x (°)").value == pytest.approx(1.0)  # not system bound
    assert drawn_rays(at) == 11


def test_paths_ending_on_a_detector_get_no_exit_stub(rtt_repo, monkeypatch):
    at, _ = layout_figure(rtt_repo, monkeypatch, "m0/michelson.rtt.json")
    assert not any(c.value.startswith(EXIT_NOTE) for c in at.caption)


@pytest.mark.parametrize("name", ["m4/grating_transmission.rtt.json", "m4/calcite_walkoff.rtt.json"])
@pytest.mark.parametrize("view_name", ["Layout", "Pfade & Ghosts", "Modell", "Prescription"])
def test_new_reference_systems_render_without_exception(rtt_repo, monkeypatch, name, view_name):
    at = pick_reference(start(rtt_repo, monkeypatch), ref(name))
    at = view(at, view_name)
    assert not at.exception, [e.value for e in at.exception]


def test_spot_offers_the_result_as_json(rtt_repo, monkeypatch):
    need("diagnostics")
    at = view(start(rtt_repo, monkeypatch), "Spot")
    ok(at)
    assert any(b.label == "Ergebnis als JSON" for b in at.get("download_button"))
