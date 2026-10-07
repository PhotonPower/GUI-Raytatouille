"""Glass and coating catalogues: parsing and automatic selection (pure Python, no library needed)."""

from __future__ import annotations

import json
from pathlib import Path

# Catalogue candidates: label shown in the UI -> (file name, file content).
Candidates = dict[str, tuple[str, bytes]]


def agf_names(data: bytes) -> list[str]:
    """Glass names (NM records) of an AGF file; UTF-16 with BOM or ANSI/UTF-8."""
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = data.decode("utf-16", errors="replace")
    else:
        text = data.decode("utf-8", errors="replace")
    names = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) > 1 and parts[0] == "NM":
            names.append(parts[1])
    return names


def _walk(node, visit):
    if isinstance(node, dict):
        visit(node)
        for value in node.values():
            _walk(value, visit)
    elif isinstance(node, list):
        for item in node:
            _walk(item, visit)


def material_refs(system_dict: dict) -> set[tuple[str, str]]:
    """(CATALOG, GLASS) of all catalogue references in the 'material' fields."""
    found: set[tuple[str, str]] = set()

    def visit(node):
        value = node.get("material")
        for v in (value if isinstance(value, list) else [value]):
            if isinstance(v, str) and ":" in v and not v.upper().startswith("CONST"):
                cat, _, glass = v.partition(":")
                found.add((cat.upper(), glass))

    _walk(system_dict, visit)
    return found


def coating_refs(system_dict: dict) -> set[tuple[str, str]]:
    """(CATALOG, NAME) of all coating interactions."""
    found: set[tuple[str, str]] = set()

    def visit(node):
        inter = node.get("interaction")
        if isinstance(inter, dict) and inter.get("type") == "coating":
            name = str(inter.get("name", ""))
            cat, _, coat = name.partition(":")
            found.add((cat.upper(), coat))

    _walk(system_dict, visit)
    return found


def coating_info(data: bytes) -> tuple[str, set[str]]:
    """Catalogue name (upper case) and coating names of a coating catalogue file."""
    try:
        d = json.loads(data.decode("utf-8"))
        return str(d.get("catalog", "")).upper(), {str(c.get("name")) for c in d.get("coatings", [])}
    except (ValueError, AttributeError, UnicodeDecodeError):
        return "", set()


def assign_names(labels: list[str], candidates: dict[str, tuple[str, bytes]]) -> list[tuple[str, str]]:
    """(label, name in the system): file stem in upper case, later duplicates get _2, _3 ..."""
    seen: dict[str, int] = {}
    out = []
    for label in labels:
        stem = Path(candidates[label][0]).stem.upper()
        seen[stem] = seen.get(stem, 0) + 1
        out.append((label, stem if seen[stem] == 1 else f"{stem}_{seen[stem]}"))
    return out


def auto_catalogs(refs: set[tuple[str, str]], candidates: dict[str, tuple[str, bytes]]) -> list[str]:
    """Pick one catalogue file per catalogue name that contains the referenced glasses."""
    chosen: list[str] = []
    used: set[str] = set()
    for cat, glass in sorted(refs):
        if cat in used:
            continue
        for label, (fname, data) in candidates.items():
            if Path(fname).stem.upper() == cat and glass in agf_names(data):
                chosen.append(label)
                used.add(cat)
                break
    return chosen


def auto_coatings(refs: set[tuple[str, str]], candidates: dict[str, tuple[str, bytes]]) -> list[str]:
    chosen: list[str] = []
    used: set[str] = set()
    for cat, coat in sorted(refs):
        if cat in used:
            continue
        for label, (_, data) in candidates.items():
            name, coats = coating_info(data)
            if name == cat and coat in coats:
                chosen.append(label)
                used.add(cat)
                break
    return chosen
