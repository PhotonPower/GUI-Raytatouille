"""Check a system file against the JSON schema of the library (no Streamlit, no library).

The schema comes from ``rt.schema()`` and is passed in; the check itself needs the package ``jsonschema``
(optional: ``pip install jsonschema``). Messages are those of ``jsonschema`` (English) with the JSON pointer.
"""

from __future__ import annotations

MAX_ROWS = 50


def pointer(path) -> str:
    """JSON pointer of a path of keys and indices (``/`` for the document itself)."""
    return "/" + "/".join(str(part) for part in path)


def schema_rows(schema: dict, document) -> list[dict]:
    """Table rows ``{"Stelle", "Meldung"}`` for what ``document`` violates, sorted by location, at most MAX_ROWS.

    Raises ImportError if ``jsonschema`` is not installed."""
    from jsonschema import Draft202012Validator

    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda e: [str(p) for p in e.absolute_path])
    return [{"Stelle": pointer(e.absolute_path), "Meldung": e.message[:300]} for e in errors[:MAX_ROWS]]
