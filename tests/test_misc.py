"""Small pure helpers: colours, repo search, Streamlit width switch."""

from __future__ import annotations

import pytest

from rtt_explorer.colors import wavelength_rgb
from rtt_explorer.repo import find_repo
from rtt_explorer.stretch import stretch_kwargs


class TestWavelengthRgb:
    def test_visible_colours_are_dominated_by_the_expected_channel(self):
        r, g, b = wavelength_rgb(0.65)
        assert r > g and r > b
        r, g, b = wavelength_rgb(0.53)
        assert g > r and g > b
        r, g, b = wavelength_rgb(0.45)
        assert b > r and b > g

    @pytest.mark.parametrize("um", [0.2, 0.35, 0.4, 0.55, 0.7, 0.78, 1.0, 5.0])
    def test_components_stay_in_unit_range(self, um):
        assert all(0.0 <= c <= 1.0 for c in wavelength_rgb(um))

    def test_infrared_is_dark_red_and_uv_purple(self):
        assert wavelength_rgb(1.5) == (0.5, 0.0, 0.0)
        assert wavelength_rgb(0.3) == (0.5, 0.0, 0.8)


class TestFindRepo:
    def test_environment_variable_wins(self, tmp_path, monkeypatch):
        (tmp_path / "tests" / "reference").mkdir(parents=True)
        monkeypatch.setenv("RTT_REPO", str(tmp_path))
        assert find_repo() == str(tmp_path)

    def test_folder_without_reference_systems_is_ignored(self, tmp_path, monkeypatch):
        monkeypatch.setenv("RTT_REPO", str(tmp_path))
        monkeypatch.chdir(tmp_path)
        assert find_repo() != str(tmp_path)

    def test_finds_sibling_folder_named_raytatouille(self, tmp_path, monkeypatch):
        (tmp_path / "Raytatouille" / "tests" / "reference").mkdir(parents=True)
        work = tmp_path / "GUI-Raytatouille"
        work.mkdir()
        monkeypatch.delenv("RTT_REPO", raising=False)
        monkeypatch.chdir(work)
        assert find_repo() == str(tmp_path / "Raytatouille")


class TestStretchKwargs:
    @pytest.mark.parametrize("version", ["1.49.0", "1.50.2", "2.0.0", "1.49.0.dev1"])
    def test_new_streamlit_uses_width(self, version):
        assert stretch_kwargs(version) == {"width": "stretch"}

    @pytest.mark.parametrize("version", ["1.40.1", "1.48.9", "0.99.0"])
    def test_old_streamlit_uses_container_width(self, version):
        assert stretch_kwargs(version) == {"use_container_width": True}

    def test_unparsable_version_falls_back_to_container_width(self):
        assert stretch_kwargs("dev") == {"use_container_width": True}
