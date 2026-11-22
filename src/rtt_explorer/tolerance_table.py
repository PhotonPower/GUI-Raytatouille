"""Tolerance items, sensitivity and Monte Carlo results as table rows (pure logic, no Streamlit, no library).

The functions read attributes and the ``name`` of enums of the objects of ``raytatouille.tolerance``, so tests can use
fakes. Texts are German: they are shown as they are.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

KIND_LABELS = {
    "RADIUS": "Radius", "CURVATURE_RELATIVE": "Krümmung (relativ)", "CONIC": "Konik", "THICKNESS": "Dicke",
    "PARAM": "Parameterwert", "PARAMETER": "Parameter", "DECENTER_X": "Dezentrierung x",
    "DECENTER_Y": "Dezentrierung y", "SHIFT_Z": "Verschiebung z", "TILT_X_DEG": "Kippung x",
    "TILT_Y_DEG": "Kippung y", "TILT_Z_DEG": "Kippung z", "INDEX": "Brechzahl", "ABBE": "Abbezahl",
    "ZERNIKE": "Zernike-Term",
}
# Units of the limits: those of the kind (mm for lengths, degree for tilts, none for the relative kinds).
KIND_UNITS = {
    "RADIUS": "mm", "CURVATURE_RELATIVE": "–", "CONIC": "–", "THICKNESS": "mm", "PARAM": "Einheit des Parameters",
    "PARAMETER": "Einheit des Parameters", "DECENTER_X": "mm", "DECENTER_Y": "mm", "SHIFT_Z": "mm",
    "TILT_X_DEG": "°", "TILT_Y_DEG": "°", "TILT_Z_DEG": "°", "INDEX": "–", "ABBE": "–", "ZERNIKE": "mm",
}
DISTRIBUTIONS = {"NORMAL": "normal (±2σ = T)", "UNIFORM": "gleichverteilt", "ENDPOINT": "Endpunkte ±T"}
ORIGINS = {"CLASS": "Klasse", "EXPLICIT": "explizit"}
MAX_TRIALS = 5000  # upper limit of the number of Monte Carlo trials in the view


def kind_label(name: str) -> str:
    return KIND_LABELS.get(name, name)


def kind_unit(name: str) -> str:
    return KIND_UNITS.get(name, "")


def item_target(item) -> str:
    """Text of what a tolerance item hits: surface, node or parameter, with segment and term if given."""
    if getattr(item, "surface", None):
        text = f"Fläche {item.surface}"
    elif getattr(item, "node", None):
        text = f"Knoten {item.node}"
    elif getattr(item, "parameter", None):
        text = f"Parameter {item.parameter}"
    else:
        return ""
    if getattr(item, "segment", None) is not None:
        text += f", Segment {item.segment}"
    if getattr(item, "term", None) is not None:
        text += f", Term {item.term}"
    return text


def item_rows(items: Sequence, origins: Sequence | None) -> list[dict]:
    """One row per item of ``expand``: number, id, kind, target, limit T, unit, distribution and origin."""
    rows = []
    for k, it in enumerate(items):
        kind = it.kind.name
        origin = ""
        if origins is not None and k < len(origins):
            origin = ORIGINS.get(origins[k].source.name, origins[k].source.name)
        rows.append({"Nr": k + 1, "Id": it.id, "Art": kind_label(kind), "Ziel": item_target(it),
                     "Grenze T": it.limit, "Einheit": kind_unit(kind),
                     "Verteilung": DISTRIBUTIONS.get(it.distribution.name, it.distribution.name),
                     "Herkunft": origin})
    return rows


def contribution_shares(kind: str, deltas: Sequence, qs: Sequence) -> list[float | None]:
    """Share of each item in the spread of a criterion (fractions summing to 1; None where there is no value).

    A linear criterion adds the squares of the effects delta_i (RSS = sqrt(sum delta_i^2)); a quadratic one adds the
    q_i to the mean square (negative q_i do not count towards the share)."""
    if kind == "QUADRATIC":
        raw = [None if q is None else max(float(q), 0.0) for q in qs]
    else:
        raw = [None if d is None else float(d) ** 2 for d in deltas]
    total = sum(r for r in raw if r is not None)
    return [None if r is None else (r / total if total > 0 else 0.0) for r in raw]


def sensitivity_rows(criterion, items: Sequence) -> list[dict]:
    """Rows of one criterion of a sensitivity run: the criterion at +T and -T, its share and the limit T'."""
    entries = list(criterion.items)
    shares = contribution_shares(criterion.kind.name, [None if e.excluded else e.delta for e in entries],
                                 [None if e.excluded else e.q for e in entries])
    inverse = getattr(getattr(criterion, "inverse", None), "limits", None)
    rows = []
    for k, (it, entry, share) in enumerate(zip(items, entries, shares)):
        kind = it.kind.name
        rows.append({
            "Id": it.id, "Art": kind_label(kind), "Ziel": item_target(it), "T": it.limit, "Einheit": kind_unit(kind),
            "Φ(+T)": entry.plus, "Φ(−T)": entry.minus, "größte Änderung": entry.worst,
            "Anteil (%)": None if share is None else 100.0 * share,
            "T′ (inverse Sensitivität)": inverse[k] if inverse is not None and k < len(inverse) else None,
            "Hinweis": entry.excluded or ""})
    return rows


def _num(value: float) -> str:
    return f"{value:g}"


def criterion_limit_text(criterion) -> str:
    """The bounds of a criterion definition: ``≤ max``, ``≥ min``, ``min … max`` and ``Änderung ≤ max_change``."""
    lo, hi = getattr(criterion, "min", None), getattr(criterion, "max", None)
    parts = []
    if lo is not None and hi is not None:
        parts.append(f"{_num(lo)} … {_num(hi)}")
    elif hi is not None:
        parts.append(f"≤ {_num(hi)}")
    elif lo is not None:
        parts.append(f"≥ {_num(lo)}")
    change = getattr(criterion, "max_change", None)
    if change is not None:
        parts.append(f"Änderung ≤ {_num(change)}")
    return "; ".join(parts) if parts else "–"


def yield_text(y) -> str:
    """``good von total (percentage), Intervall lower bis upper %`` of a Yield; ``–`` without trials."""
    if y.total <= 0 or not math.isfinite(y.fraction):
        return "–"
    return (f"{y.good} von {y.total} ({100 * y.fraction:.1f} %), "
            f"Intervall {100 * y.lower:.1f} bis {100 * y.upper:.1f} %")


def percentile_columns(percentiles: Sequence) -> dict[str, float]:
    """``{"50 %": value, ...}`` of the percentiles of a criterion."""
    return {f"{100 * p.p:g} %": p.value for p in percentiles}


def monte_carlo_rows(stats: Sequence, definitions: Sequence) -> list[dict]:
    """One row per criterion of a Monte Carlo run: statistics, percentiles, bounds and yield."""
    by_id = {d.id: d for d in definitions}
    rows = []
    for s in stats:
        definition = by_id.get(s.id)
        rows.append({"Kriterium": s.id, "Grenze": "" if definition is None else criterion_limit_text(definition),
                     "Prüflinge": s.with_value, "Mittel": s.mean, "σ": s.standard_deviation, "Min": s.min,
                     "Max": s.max, **percentile_columns(s.percentiles), "Ausbeute": yield_text(s.yield_)})
    return rows
