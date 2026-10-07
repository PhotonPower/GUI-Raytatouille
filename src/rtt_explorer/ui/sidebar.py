"""Sidebar: project folder, system source, environment, library features, catalogues."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import raytatouille as rt
import streamlit as st

from ..catalogs import Candidates, coating_info
from ..compat import FEATURES
from ..repo import find_repo


@dataclass
class ProjectChoice:
    """What the user chose in the upper part of the sidebar."""

    repo: Path | None
    repo_ok: bool
    mode: str
    temperature: float | None
    pressure: float | None


def project_sidebar() -> ProjectChoice:
    """Repo path, system mode, environment override and the feature overview."""
    with st.sidebar:
        st.header("Projekt")
        repo_text = st.text_input("Pfad zum Raytatouille-Repo", value=find_repo(),
                                  help="Enthält tests/reference und tests/catalogs.")
        repo = Path(repo_text) if repo_text else None
        repo_ok = bool(repo and (repo / "tests" / "reference").is_dir())
        if not repo_ok:
            st.warning("Repo nicht gefunden: Beispielsysteme und Kataloge sind nicht verfügbar. "
                       "Hochladen und Selberbauen funktionieren trotzdem.")

        modes = (["Beispielsystem"] if repo_ok else []) + ["System bauen", "Datei hochladen"]
        mode = st.radio("System", modes)

        st.header("Umgebung")
        override_env = st.checkbox("Temperatur/Druck überschreiben", value=False)
        temperature = pressure = None
        if override_env:
            temperature = st.number_input("Temperatur (°C)", value=20.0, step=1.0)
            pressure = st.number_input("Luftdruck (atm)", value=1.0, step=0.01, format="%.3f")
        st.caption("Wirkt auf Ciddor-Luft und (falls im Katalog) auf dn/dT der Gläser.")

        with st.expander("Funktionen dieser Bibliotheksversion"):
            st.write(f"raytatouille {getattr(rt, '__version__', '?')}")
            for label, ok in FEATURES.rows():
                st.write(("✅ " if ok else "❌ ") + label)
    return ProjectChoice(repo, repo_ok, mode, temperature, pressure)


def collect_catalogs(repo: Path | None, repo_ok: bool) -> tuple[Candidates, Candidates]:
    """Glass and coating catalogue candidates from the repo and from uploads (sidebar)."""
    # Kataloge: Kandidaten aus dem Repo und Uploads
    candidates: dict[str, tuple[str, bytes]] = {}
    coat_candidates: dict[str, tuple[str, bytes]] = {}
    if repo_ok:
        cat_dir = repo / "tests" / "catalogs"
        for p in sorted(cat_dir.rglob("*.agf")):
            candidates[str(p.relative_to(cat_dir))] = (p.name, p.read_bytes())
        for p in sorted(cat_dir.rglob("*.json")):
            data = p.read_bytes()
            if coating_info(data)[0]:
                coat_candidates[str(p.relative_to(cat_dir))] = (p.name, data)
    with st.sidebar:
        st.header("Kataloge")
        uploads = st.file_uploader("Eigene AGF-Glaskataloge", type=["agf"], accept_multiple_files=True)
        for up in uploads or []:
            candidates[f"Upload: {up.name}"] = (up.name, up.getvalue())
        if FEATURES.coatings:
            cuploads = st.file_uploader("Eigene Coating-Kataloge (.json)", type=["json"],
                                        accept_multiple_files=True)
            for up in cuploads or []:
                if coating_info(up.getvalue())[0]:
                    coat_candidates[f"Upload: {up.name}"] = (up.name, up.getvalue())
                else:
                    st.warning(f"{up.name} ist kein Coating-Katalog (Feld 'catalog' fehlt).")
    return candidates, coat_candidates
