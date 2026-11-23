"""Switch components on and off with the ``active`` flag (pure logic: dictionaries, no Streamlit, no library).

Schema 0.10 (ADR 0049): every assembly and element may carry ``"active": false``. The node stays in the model,
but the calculation leaves it out; an inactive assembly switches off all its children. The root cannot be
switched off. The file only carries the key when it is ``false``, and a file before schema 0.10 with the key
is a read error, so switching something off raises the schema version to 0.10.0.
"""

from __future__ import annotations

import copy

from .model_table import ELEMENT_KINDS

MIN_VERSION = (0, 10, 0)


def _version(text) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in str(text).split("."))
    except ValueError:
        return (0,)


def node_rows(system_dict: dict) -> list[dict]:
    """One row per assembly or element below the root, in tree order.

    Keys: ``pointer`` (JSON pointer), ``name``, ``kind`` (German label), ``depth``, ``active`` (the node's own
    flag) and ``by_parent`` (True if an assembly above is switched off).
    """
    rows: list[dict] = []

    def walk(node: dict, pointer: str, depth: int, parent_off: bool) -> None:
        for index, child in enumerate(node.get("children") or []):
            here = f"{pointer}/children/{index}"
            kind = child.get("type", "")
            active = child.get("active", True) is not False
            rows.append({"pointer": here, "name": child.get("name", ""),
                         "kind": "Baugruppe" if kind == "assembly" else ELEMENT_KINDS.get(kind, kind),
                         "depth": depth, "active": active, "by_parent": parent_off})
            if kind == "assembly":
                walk(child, here, depth + 1, parent_off or not active)

    walk(system_dict.get("root") or {}, "/root", 0, False)
    return rows


def with_active(system_dict: dict, states: dict[str, bool]) -> dict:
    """A copy of the system with the flag of each pointer in ``states`` set (``False`` is written, ``True`` removes
    the key). Raises ValueError (German) for the root or a pointer that is not a node."""
    out = copy.deepcopy(system_dict)
    known = {row["pointer"] for row in node_rows(out)}
    off = False
    for pointer, state in states.items():
        if pointer == "/root":
            raise ValueError("Die Wurzel lässt sich nicht ausschalten; schalte ihre Kinder aus.")
        if pointer not in known:
            raise ValueError(f"Kein Bauteil unter {pointer}.")
        node = out
        for part in pointer.lstrip("/").split("/"):
            node = node[int(part)] if isinstance(node, list) else node[part]
        if state:
            node.pop("active", None)
        else:
            node["active"] = False
            off = True
    if off and _version(out.get("schema_version")) < MIN_VERSION:
        out["schema_version"] = "0.10.0"
    return out
