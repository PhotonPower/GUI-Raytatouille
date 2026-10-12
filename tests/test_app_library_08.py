"""Smoke tests of the functions of Raytatouille 0.8 (wavefront, Zernike fit, diffraction PSF, MTF,
encircled energy, through focus). They need the library and a checkout, like ``test_app.py``."""

from __future__ import annotations

import pytest

from test_app import metric, pick_reference, start, widget
from test_app_library_06 import need, ok, ref, table, view

pytestmark = pytest.mark.library

# m6/paraboloid_f10: paraboloid f = 100 mm with D = 10 mm, aberration-free on axis, lambda = 0.5876 um.
# The app compiles it in air (n' about 1.00027), so N_w = 10 / n' (rel. 3e-4).
PARABOLOID = "m6/paraboloid_f10.rtt.json"
AIRY_F10 = 1.22 * 0.5876 * 10.0


def need_reference(rtt_repo, name: str) -> None:
    """Skip when the checkout predates the reference system (m6 and r2 came with 0.8)."""
    if not (rtt_repo / "tests" / "reference" / name).is_file():
        pytest.skip(f"Referenzsystem fehlt im Checkout: {name}")


def diffraction(rtt_repo, monkeypatch, kind: str, name: str = PARABOLOID):
    need_reference(rtt_repo, name)
    at = view(pick_reference(start(rtt_repo, monkeypatch), ref(name)), "Beugung")
    at = widget(at, "radio", "Auswertung").set_value(kind).run()
    ok(at)
    return at


def test_psf_of_the_paraboloid_is_diffraction_limited(rtt_repo, monkeypatch):
    need("diffraction")
    at = diffraction(rtt_repo, monkeypatch, "PSF")
    assert metric(at, "Strehlzahl") == pytest.approx(1.0, abs=1e-4)
    assert metric(at, "Airy-Radius (Näherung)") == pytest.approx(AIRY_F10, rel=1e-3)


def test_encircled_energy_of_the_paraboloid_follows_airy(rtt_repo, monkeypatch):
    need("diffraction")
    at = diffraction(rtt_repo, monkeypatch, "Eingeschlossene Energie")
    # Airy pattern: 83.8 % of the energy inside the first dark ring, 91 % inside the second
    assert metric(at, "Radius 80 %") < AIRY_F10 < metric(at, "Radius 90 %")
    assert metric(at, "Radius 50 %") == pytest.approx(0.42 * AIRY_F10, rel=0.05)  # r50 = 0.51 lambda N


def test_through_focus_of_the_paraboloid_peaks_at_the_focus(rtt_repo, monkeypatch):
    need("diffraction")
    at = diffraction(rtt_repo, monkeypatch, "Through-Focus")
    assert metric(at, "Strehlzahl bei 0") == pytest.approx(1.0, abs=1e-4)
    assert metric(at, "beste Fokuslage") == pytest.approx(0.0, abs=1e-9)


def test_mtf_and_polychromatic_psf_of_the_cooke_triplet(rtt_repo, monkeypatch):
    need("diffraction")
    at = view(start(rtt_repo, monkeypatch), "Beugung")
    for kind in ("PSF", "MTF", "Eingeschlossene Energie", "Through-Focus"):
        at = widget(at, "radio", "Auswertung").set_value(kind).run()
        ok(at)
    assert 0.0 < metric(at, "Strehlzahl bei 0") <= 1.0


def test_wavefront_of_the_paraboloid_and_a_focus_shift(rtt_repo, monkeypatch):
    need("wavefront")
    need_reference(rtt_repo, PARABOLOID)
    at = view(pick_reference(start(rtt_repo, monkeypatch), ref(PARABOLOID)), "OPD / Wellenfront")
    ok(at)
    assert metric(at, "Strehl (Maréchal)") == pytest.approx(1.0, abs=1e-3)
    assert metric(at, "σ um den besten Fokus") == pytest.approx(0.0, abs=1e-4)
    terms = next(df.value for df in at.dataframe if "Koeffizient (Wellen)" in df.value.columns)
    assert len(terms) == 37
    # 50 um defocus at F/10: W020 = dz / (8 N^2) = 0.05 mm / 800 = 62.5 nm, about 0.106 waves
    at = widget(at, "number_input", "Fokusverschiebung (mm)").set_value(0.05).run()
    ok(at)
    defocus = next(df.value for df in at.dataframe if "Koeffizient (Wellen)" in df.value.columns)
    assert abs(defocus.set_index("j").loc[4, "Koeffizient (Wellen)"]) > 0.01
    assert metric(at, "RMS") > 0.01
    # the Zernike fit removes defocus: sigma about the best focus stays near 0 for a pure focus shift
    assert metric(at, "σ um den besten Fokus") < 0.01


def test_airy_radius_in_the_spot_view_uses_the_working_f_number(rtt_repo, monkeypatch):
    need("prescription")
    need_reference(rtt_repo, "r2/ideal_lens.rtt.json")
    import raytatouille as rt

    at = pick_reference(start(rtt_repo, monkeypatch), ref("r2/ideal_lens.rtt.json"))
    at = view(at, "Spot")
    ok(at)
    # object at 75 mm, image at 150 mm: N_w is about three times |EFL| / EPD
    system = rt.load(rtt_repo / "tests" / "reference" / "r2" / "ideal_lens.rtt.json")
    n_w = rt.paraxial.prescription(rt.compile(system), path=0).paraxial_working_f_number
    assert metric(at, "Airy-Radius (Näherung)") == pytest.approx(1.22 * 0.5876 * n_w, rel=1e-3)


@pytest.mark.parametrize("name", ["m6/paraboloid_f10.rtt.json", "m6/paraboloid_f50.rtt.json",
                                  "m6/planoconvex_f10.rtt.json", "m6/fold45_metal.rtt.json",
                                  "m6/fold45_focus.rtt.json", "r2/ideal_lens.rtt.json"])
@pytest.mark.parametrize("view_name", ["Layout", "Spot", "OPD / Wellenfront", "Beugung", "Modell"])
def test_m6_systems_render(rtt_repo, monkeypatch, name, view_name):
    need_reference(rtt_repo, name)
    at = pick_reference(start(rtt_repo, monkeypatch), ref(name))
    at = view(at, view_name)
    assert not at.exception, [e.value for e in at.exception]


# ---------------------------------------------------------------- part 2: ideal lens, Jones, interferogram

def test_ideal_lens_in_model_and_layout(rtt_repo, monkeypatch):
    need("ideal_lens")
    need_reference(rtt_repo, "r2/ideal_lens.rtt.json")
    at = pick_reference(start(rtt_repo, monkeypatch), ref("r2/ideal_lens.rtt.json"))
    at = view(at, "Modell")
    ok(at)
    interactions = set(table(at, "Wechselwirkung")["Wechselwirkung"])
    assert "ideale Linse f = 50, Objekt 75" in interactions
    assert "ideale Zylinderlinse f = 50, Achse 0°, Objekt 75" in interactions
    ok(view(at, "Layout"))


def test_builder_ideal_lens_has_its_focal_length(rtt_repo, monkeypatch):
    need("ideal_lens")
    import pandas as pd

    from rtt_explorer.builder import BUILDER_COLUMNS, VARIABLE_COLUMNS

    at = start(rtt_repo, monkeypatch)
    at = widget(at, "radio", "System").set_value("System bauen").run()
    df = pd.DataFrame([["Blende", 0.0, 0.0, 1.0, "AIR", 10.0, ""],
                       ["Ideallinse", 50.0, 0.0, 50.0, "AIR", 12.0, ""],
                       ["Bild", 0.0, 0.0, 0.0, "AIR", 0.0, ""]], columns=BUILDER_COLUMNS)
    for col in VARIABLE_COLUMNS:
        df[col] = False
    at.session_state["bdf"] = df
    at.session_state["bver"] = at.session_state["bver"] + 1
    at = at.run()
    ok(at)
    # The app compiles in air (n about 1.00027); f of the ideal lens is along the propagation in that medium.
    assert metric(at, "Brennweite EFL") == pytest.approx(50.0, rel=1e-3)
    ok(view(at, "Layout"))


def test_bundle_with_a_pupil_point_list(rtt_repo, monkeypatch):
    need("point_list")
    at = view(start(rtt_repo, monkeypatch), "Strahlenbündel")
    at = widget(at, "selectbox", "Pupillenraster").set_value("Punktliste (px, py)").run()
    ok(at)
    status = table(at, "Strahlen")
    assert status["Strahlen"].sum() == 5  # the five default points
    at = widget(at, "text_area", "Pupillenpunkte (eine Zeile je Punkt: px, py)").set_value("0, x").run()
    assert any("Zeile 1" in e.value for e in at.error)


def test_jones_pupil_of_the_cooke_triplet(rtt_repo, monkeypatch):
    need("jones")
    at = view(start(rtt_repo, monkeypatch), "Polarisation")
    ok(at)
    # uncoated glass: a little diattenuation at the rim, no retardance from Fresnel transmission alone
    assert 0.0 < metric(at, "Diattenuation max") < 0.2
    assert "x′" in table(at, "x").index
    at = widget(at, "radio", "Quelle").set_value("Linear").run()
    ok(at)


def test_jones_pupil_of_the_metal_fold_with_a_free_beam(rtt_repo, monkeypatch):
    need("jones")
    need_reference(rtt_repo, "m6/fold45_metal.rtt.json")
    at = view(pick_reference(start(rtt_repo, monkeypatch), ref("m6/fold45_metal.rtt.json")), "Polarisation")
    ok(at)  # no stop: the view starts with the free collimated beam
    # 45 degree reflection on a metal: the phase difference of s and p gives a clear retardance
    assert metric(at, "Retardance max") > 1.0


def test_interferogram_of_the_offset_michelson(rtt_repo, monkeypatch):
    need("interferogram")
    at = view(pick_reference(start(rtt_repo, monkeypatch), ref("m4/michelson_offset.rtt.json")), "Pfade & Ghosts")
    ok(at)
    arrived, launched = (int(v) for v in next(m for m in at.metric
                                              if m.label == "Punkte auf beiden Pfaden").value.split("/"))
    assert 0 < arrived <= launched
    assert metric(at, "Streifen über die Fläche") >= 0.0
