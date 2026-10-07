"""Locate a checkout of the Raytatouille repository (reference systems and catalogues)."""

from __future__ import annotations

import os
from pathlib import Path


def find_repo() -> str:
    """Return the path of the Raytatouille checkout, or an empty string if none is found.

    A checkout is recognised by its ``tests/reference`` folder. Searched in this order: the
    environment variable ``RTT_REPO``, the current folder, the parents of this file, and a sibling
    folder named ``Raytatouille`` next to the current folder or one of its two parents.
    """
    candidates: list[Path] = []
    if os.environ.get("RTT_REPO"):
        candidates.append(Path(os.environ["RTT_REPO"]))
    candidates.append(Path.cwd())
    candidates += list(Path(__file__).resolve().parents)[:4]
    candidates += [p / "Raytatouille" for p in list(Path.cwd().parents)[:2] + [Path.cwd()]]
    for p in candidates:
        if (p / "tests" / "reference").is_dir():
            return str(p)
    return ""
