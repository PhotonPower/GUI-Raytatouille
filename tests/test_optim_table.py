"""Merit function and optimization results as table rows (pure logic; fakes stand in for rt objects)."""

from __future__ import annotations

from types import SimpleNamespace as NS

from rtt_explorer.optim_table import generator_row, operand_row, status_text, variable_label


class FirstOrderOperand:
    def __init__(self, quantity, target, weight=1.0, path="main", configuration=None, wavelength=None):
        self.quantity, self.target, self.weight = NS(name=quantity), target, weight
        self.path, self.configuration, self.wavelength = path, configuration, wavelength


class RayOperand:
    def __init__(self, coordinate, surface, target=0.0, field=0, px=0.0, py=1.0, weight=1.0):
        self.coordinate, self.surface, self.target, self.weight = NS(name=coordinate), surface, target, weight
        self.field, self.px, self.py, self.path, self.configuration = field, px, py, "main", None
        self.occurrence, self.wavelength = 0, None


class SpotRmsOperand:
    def __init__(self, target=0.0, field=1, polychromatic=True, reference="CENTROID", rings=6):
        self.target, self.weight, self.field, self.polychromatic = target, 1.0, field, polychromatic
        self.reference, self.rings, self.path, self.configuration = NS(name=reference), rings, "main", "tele"
        self.wavelength = None


class ParamValueOperand:
    def __init__(self, parameter, target):
        self.parameter, self.target, self.weight, self.configuration = parameter, target, 1.0, None


class SpotGenerator:
    def __init__(self, fields=None, wavelengths=None, rings=3, arms=6, weight=1.0, configuration=None):
        self.fields, self.wavelengths, self.rings, self.arms = fields, wavelengths, rings, arms
        self.weight, self.configuration, self.path, self.reference = weight, configuration, "main", NS(name="CENTROID")


class WavefrontGenerator(SpotGenerator):
    pass


def test_first_order_operand_row():
    row = operand_row(FirstOrderOperand("EFL", 100.0, weight=1e4))
    assert row == {"Operand": "Brennweite EFL", "Details": "Pfad main", "Ziel": 100.0, "Gewicht": 1e4,
                   "Konfiguration": ""}


def test_ray_operand_row_names_surface_field_and_pupil_point():
    row = operand_row(RayOperand("Y", "IMG"))
    assert row["Operand"] == "Strahlhöhe y"
    assert row["Details"] == "Pfad main, Fläche IMG, Feld 0, Pupille (0, 1)"
    assert row["Ziel"] == 0.0


def test_spot_operand_row_with_configuration():
    row = operand_row(SpotRmsOperand())
    assert row["Operand"] == "RMS-Spot"
    assert row["Details"] == "Pfad main, Feld 1, polychromatisch, um Schwerpunkt, 6 Ringe"
    assert row["Konfiguration"] == "tele"


def test_param_value_and_unknown_operand_rows():
    assert operand_row(ParamValueOperand("D", 12.0))["Details"] == "Parameter D"
    unknown = type("FancyOperand", (), {"target": 1.0, "weight": 2.0, "configuration": None})()
    assert operand_row(unknown)["Operand"] == "FancyOperand"


def test_generator_rows():
    assert generator_row(SpotGenerator()) == {"Generator": "RMS-Spot (Gauß)", "Felder": "alle",
                                              "Wellenlängen": "alle", "Abtastung": "3 Ringe × 6 Arme",
                                              "Gewicht": 1.0, "Konfiguration": ""}
    row = generator_row(WavefrontGenerator(fields=[0, 2], wavelengths=[1], configuration="wide"))
    assert (row["Generator"], row["Felder"], row["Wellenlängen"], row["Konfiguration"]) == \
        ("RMS-Wellenfront (Gauß)", "0, 2", "1", "wide")


def test_status_text():
    assert status_text("CONVERGED_STEP") == "konvergiert (Schrittweite)"
    assert status_text("MAX_ITERATIONS") == "Iterationsgrenze erreicht"
    assert status_text("SOMETHING_NEW") == "SOMETHING_NEW"


def test_variable_label_prefers_row_name_and_configuration():
    names = ["wide", "tele"]
    assert variable_label("/parameters/1/values/1", "G", 1, names) == "G (tele)"
    assert variable_label("/parameters/0/value", "D", None, names) == "D"
    assert variable_label("/root/children/0/surfaces/0/shape/base/radius", "", None, names) == \
        "/root/children/0/surfaces/0/shape/base/radius"
    assert variable_label("/x", "R", 3, names) == "R (3)"


def test_variable_label_names_the_surface_of_a_model_value():
    locations, ids = ["/root/children/0/surfaces/0", "/root/children/0/surfaces/1"], ["L1.S1", "L1.S2"]
    assert variable_label("/root/children/0/surfaces/1/shape/base/radius/value", "", None, [], locations, ids) == \
        "L1.S2: shape/base/radius"
    # an element pose is no surface: the pointer stays
    assert variable_label("/root/children/2/pose/position/2/value", "", None, [], locations, ids) == \
        "/root/children/2/pose/position/2/value"
