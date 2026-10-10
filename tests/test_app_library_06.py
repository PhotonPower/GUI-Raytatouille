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
