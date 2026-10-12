"""Merit function and optimization results as table rows (pure logic, no Streamlit, no library).

The operands and generators come from ``System.optimization`` (``raytatouille.model``); the
functions read attributes and the class name of the operand, so tests can use fakes.
"""

from __future__ import annotations

from collections.abc import Sequence

from .messages import surface_for_location

FIRST_ORDER = {"EFL": "Brennweite EFL", "BFL": "Schnittweite BFL", "IMAGE_F_NUMBER": "Blendenzahl bildseitig",
               "MAGNIFICATION": "Abbildungsmaßstab"}
SPOT_REFERENCE = {"CENTROID": "um Schwerpunkt", "CHIEF": "um Hauptstrahl"}
GENERATORS = {"SpotGenerator": "RMS-Spot (Gauß)", "WavefrontGenerator": "RMS-Wellenfront (Gauß)"}
STATUS = {"CONVERGED_GRADIENT": "konvergiert (Gradient)", "CONVERGED_STEP": "konvergiert (Schrittweite)",
          "CONVERGED_MERIT": "konvergiert (Merit-Funktion)", "MAX_ITERATIONS": "Iterationsgrenze erreicht",
          "CANCELLED": "abgebrochen", "FAILED": "fehlgeschlagen"}


def _g(value) -> str:
    return f"{value:g}" if isinstance(value, float) else str(value)


def _wavelength(op) -> str:
    w = getattr(op, "wavelength", None)
    return "" if w is None else f", Wellenlänge {w}"


def operand_row(op) -> dict:
    """Kind, details, target, weight and configuration of one operand."""
    kind = type(op).__name__
    path = f"Pfad {op.path}" if getattr(op, "path", None) else ""
    if kind == "FirstOrderOperand":
        name = FIRST_ORDER.get(op.quantity.name, op.quantity.name)
        details = path + _wavelength(op)
    elif kind == "RayOperand":
        name = f"Strahlhöhe {op.coordinate.name.lower()}"
        details = (f"{path}, Fläche {op.surface}, Feld {op.field}, Pupille ({_g(op.px)}, {_g(op.py)})"
                   + _wavelength(op))
    elif kind == "SpotRmsOperand":
        name = "RMS-Spot"
        colour = "polychromatisch" if op.polychromatic else f"Wellenlänge {op.wavelength}"
        details = (f"{path}, Feld {op.field}, {colour}, "
                   f"{SPOT_REFERENCE.get(op.reference.name, op.reference.name)}, {op.rings} Ringe")
    elif kind == "OpdRmsOperand":
        name = "RMS-Wellenfront"
        details = f"{path}, Feld {op.field}, Gitter {op.grid}" + _wavelength(op)
    elif kind == "ParamValueOperand":
        name, details = "Parameterwert", f"Parameter {op.parameter}"
    else:
        name, details = kind, path
    return {"Operand": name, "Details": details, "Ziel": op.target, "Gewicht": op.weight,
            "Konfiguration": op.configuration or ""}


def generator_row(gen) -> dict:
    """Kind, selection, sampling, weight and configuration of one generator (no target: it is 0)."""
    kind = type(gen).__name__

    def selection(values) -> str:
        return "alle" if values is None else ", ".join(str(v) for v in values)

    return {"Generator": GENERATORS.get(kind, kind), "Felder": selection(gen.fields),
            "Wellenlängen": selection(gen.wavelengths), "Abtastung": f"{gen.rings} Ringe × {gen.arms} Arme",
            "Gewicht": gen.weight, "Konfiguration": gen.configuration or ""}


def status_text(name: str) -> str:
    """German text of an OptimStatus name."""
    return STATUS.get(name, name)


def variable_label(pointer: str, row: str, configuration: int | None, config_names: Sequence[str],
                   surface_locations: Sequence[str] = (), surface_ids: Sequence[str] = ()) -> str:
    """Parameter row name (with configuration) if the variable is a row; for a value inside a surface
    ``SURFACE: attribute``; else its JSON pointer."""
    if not row:
        surface = surface_for_location(pointer, surface_locations, surface_ids)
        if surface is None:
            return pointer
        location = surface_locations[list(surface_ids).index(surface)]
        attribute = pointer[len(location):].strip("/").removesuffix("/value")
        return f"{surface}: {attribute}"
    if configuration is None:
        return row
    name = config_names[configuration] if 0 <= configuration < len(config_names) else str(configuration)
    return f"{row} ({name})"
