"""Smoke tests of the whole app with Streamlit's AppTest against the real library.

They run only if ``raytatouille`` is installed and a Raytatouille checkout is found (set
``RTT_REPO``); otherwise pytest skips them (see conftest.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import rtt_explorer

pytestmark = pytest.mark.library

SCRIPT = str(Path(rtt_explorer.__file__).with_name("streamlit_app.py"))
VIEWS = ["Layout", "Spot", "Ray Fans", "OPD / Wellenfront", "Verzeichnung & Feldkrümmung", "Farbfehler",
         "Seidel", "Prescription", "Strahlenbündel", "Pfade & Ghosts", "Polarisation", "Materialien", "Modell",
         "System-Datei"]


def start(repo: Path, monkeypatch) -> AppTest:
    monkeypatch.setenv("RTT_REPO", str(repo))
    return AppTest.from_file(SCRIPT, default_timeout=180).run()


def widget(at: AppTest, kind: str, label: str):
    return next(w for w in getattr(at, kind) if w.label == label)


def metric(at: AppTest, label: str) -> float:
    return float(next(m for m in at.metric if m.label == label).value.split()[0])


def pick_reference(at: AppTest, name: str) -> AppTest:
    return widget(at, "selectbox", "Beispielsystem").set_value(name).run()


def test_view_registry_matches_the_expected_order():
    from rtt_explorer.views import VIEWS as registry

    assert list(registry) == VIEWS


def test_start_page_shows_the_cooke_triplet(rtt_repo, monkeypatch):
    at = start(rtt_repo, monkeypatch)
    assert not at.exception
    assert not at.error
    assert at.title[0].value.endswith("Raytatouille Explorer")
    assert metric(at, "Blendenzahl f/#") == pytest.approx(4.0, abs=0.01)
    assert metric(at, "Brennweite EFL") == pytest.approx(50.0, abs=0.05)


@pytest.mark.parametrize("view", VIEWS)
def test_every_view_renders_for_the_cooke_triplet(rtt_repo, monkeypatch, view):
    at = start(rtt_repo, monkeypatch)
    widget(at, "radio", "Analyse").set_value(view).run()
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]


def test_every_reference_system_loads_without_an_exception(rtt_repo, monkeypatch):
    names = sorted(str(p.relative_to(rtt_repo / "tests" / "reference"))
                   for p in (rtt_repo / "tests" / "reference").rglob("*.rtt.json"))
    assert names
    at = start(rtt_repo, monkeypatch)
    for name in names:
        pick_reference(at, name)
        assert not at.exception, f"{name}: {[e.value for e in at.exception]}"


def test_builder_singlet_has_the_expected_focal_length(rtt_repo, monkeypatch):
    at = start(rtt_repo, monkeypatch)
    widget(at, "radio", "System").set_value("System bauen").run()
    assert not at.exception
    # R = 51.68 mm, n = 1.5168 against air (Ciddor): f = R / (n - n_air) is about 100.05 mm
    assert metric(at, "Brennweite EFL") == pytest.approx(100.0, abs=0.1)
    assert metric(at, "Blendenzahl f/#") == pytest.approx(5.0, abs=0.01)


@pytest.mark.parametrize("preset_index", range(5))
def test_every_builder_preset_compiles(rtt_repo, monkeypatch, preset_index):
    at = start(rtt_repo, monkeypatch)
    widget(at, "radio", "System").set_value("System bauen").run()
    box = widget(at, "selectbox", "Vorlage")
    box.set_value(box.options[preset_index]).run()
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]
    assert metric(at, "Brennweite EFL") > 0


def test_without_repo_only_builder_and_upload_are_offered(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    at = start(tmp_path / "gibt-es-nicht", monkeypatch)
    assert not at.exception
    assert widget(at, "radio", "System").options == ["System bauen", "Datei hochladen"]
    assert any("Repo nicht gefunden" in w.value for w in at.warning)
    assert metric(at, "Brennweite EFL") > 0  # the builder still works
