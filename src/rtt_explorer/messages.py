"""Readable texts for library diagnostics and ray losses (pure logic, no Streamlit, no library).

The library reports problems with a stable code and a JSON pointer into the system file (ADR 0022
of the library). ``CompiledSystem.surface_locations`` gives the pointer of every surface, so a
pointer inside a surface can be shown with the surface id the user knows.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence


def surface_for_location(location: str | None, surface_locations: Sequence[str],
                         surface_ids: Sequence[str]) -> str | None:
    """Id of the surface whose JSON pointer is ``location`` or a prefix of it, else ``None``."""
    if not location:
        return None
    best, best_len = None, -1
    for pointer, sid in zip(surface_locations, surface_ids):
        inside = location == pointer or location.startswith(pointer + "/")
        if inside and len(pointer) > best_len:
            best, best_len = sid, len(pointer)
    return best


def diagnostic_text(code: str | None, message: str, location: str | None,
                    surface_locations: Sequence[str] = (), surface_ids: Sequence[str] = ()) -> str:
    """``message (Fläche X, Code `c`)``; the place is a surface id if possible, else the pointer."""
    parts = []
    surface = surface_for_location(location, surface_locations, surface_ids)
    if surface is not None:
        parts.append(f"Fläche {surface}")
    elif location:
        parts.append(f"Ort {location}")
    if code:
        parts.append(f"Code `{code}`")
    return f"{message} ({', '.join(parts)})" if parts else message


def loss_rows(by_status: Sequence[int], status_names: Mapping[int, str], launched: int,
              alive: int) -> list[dict]:
    """Table rows of the lost rays per status; ``alive`` is the index of the arrived rays."""
    if launched <= 0:
        return []
    rows = []
    for status, count in enumerate(by_status):
        if status == alive or not count:
            continue
        rows.append({"Status": status_names.get(status, str(status)), "Strahlen": int(count),
                     "Anteil (%)": 100.0 * count / launched})
    return rows


def unique(texts: Iterable[str]) -> list[str]:
    """Texts without repetitions, in the order of their first occurrence."""
    return list(dict.fromkeys(texts))
