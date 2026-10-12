"""Tests of the pure helpers of the diffraction and wavefront views."""

from __future__ import annotations

import math

import pytest

from rtt_explorer.diffraction import (
    airy_radius_um,
    ee_radii,
    focus_shifts,
    marechal_strehl,
    radius_at_energy,
    rayleigh_depth_mm,
    zernike_name,
    zernike_rows,
)


def test_airy_radius_uses_the_working_f_number():
    assert airy_radius_um(0.5, 4.0) == pytest.approx(1.22 * 0.5 * 4.0)
    assert airy_radius_um(0.5876, 10.0) == pytest.approx(7.16872)


@pytest.mark.parametrize("fnumber", [None, 0.0, -1.0, math.inf, math.nan])
def test_airy_radius_is_none_without_a_finite_f_number(fnumber):
    assert airy_radius_um(0.5, fnumber) is None


def test_rayleigh_depth_is_two_lambda_n_squared_in_mm():
    # 2 * 0.5 um * 5^2 = 25 um
    assert rayleigh_depth_mm(0.5, 5.0) == pytest.approx(0.025)
    assert rayleigh_depth_mm(0.5, None) is None


def test_marechal_strehl_scales_with_the_wavelength():
    # RMS in waves at the reference wavelength; at lambda the phase is 2 pi W lambda_ref / lambda
    assert marechal_strehl(0.05, 0.5876, 0.5876) == pytest.approx(math.exp(-((2 * math.pi * 0.05) ** 2)))
    assert marechal_strehl(0.05, 0.5876, 0.4861) == pytest.approx(
        math.exp(-((2 * math.pi * 0.05 * 0.5876 / 0.4861) ** 2)))
    assert marechal_strehl(0.0, 0.5, 0.6) == 1.0


def test_focus_shifts_are_symmetric_and_contain_zero():
    shifts = focus_shifts(0.1, 21)
    assert len(shifts) == 21
    assert shifts[0] == pytest.approx(-0.1)
    assert shifts[-1] == pytest.approx(0.1)
    assert shifts[10] == 0.0


def test_focus_shifts_reject_bad_input():
    with pytest.raises(ValueError):
        focus_shifts(0.0, 11)
    with pytest.raises(ValueError):
        focus_shifts(0.1, 1)


def test_ee_radii_end_at_the_largest_allowed_radius():
    radii = ee_radii(0.02, 40)
    assert len(radii) == 40
    assert radii[0] > 0.0
    assert radii[-1] == pytest.approx(0.02)
    assert all(b > a for a, b in zip(radii, radii[1:]))
    assert radii[-1] <= 0.02  # the library rejects radii above radius_max


def test_radius_at_energy_interpolates_linearly():
    radii = [0.001, 0.002, 0.003, 0.004]
    energy = [0.2, 0.6, 0.8, 0.9]
    assert radius_at_energy(radii, energy, 0.5) == pytest.approx(0.00175)
    assert radius_at_energy(radii, energy, 0.8) == pytest.approx(0.003)
    assert radius_at_energy(radii, energy, 0.1) == pytest.approx(0.0005)  # from EE(0) = 0
    assert radius_at_energy(radii, energy, 0.95) is None  # not reached within radius_max


@pytest.mark.parametrize(("j", "n", "m", "name"), [
    (1, 0, 0, "Kolben (Piston)"),
    (2, 1, 1, "Kippung x"),
    (3, 1, 1, "Kippung y"),
    (4, 2, 0, "Defokus"),
    (5, 2, 2, "Astigmatismus 45°"),
    (6, 2, 2, "Astigmatismus 0°"),
    (7, 3, 1, "Koma y"),
    (8, 3, 1, "Koma x"),
    (9, 3, 3, "Dreiblatt y"),
    (10, 3, 3, "Dreiblatt x"),
    (11, 4, 0, "Sphärische Aberration"),
    (22, 6, 0, "Sphärische Aberration 2. Ordnung"),
    (16, 5, 1, "Z(5, 1) cos"),
    (17, 5, 1, "Z(5, 1) sin"),
])
def test_zernike_names_follow_noll(j, n, m, name):
    # Noll: for m != 0 even j is the cosine term, odd j the sine term
    assert zernike_name(j, n, m) == name


def test_zernike_rows_list_every_term_with_its_coefficient():
    rows = zernike_rows([0.0, 0.01, -0.02, 0.3], [(0, 0), (1, 1), (1, 1), (2, 0)])
    assert [r["j"] for r in rows] == [1, 2, 3, 4]
    assert rows[3] == {"j": 4, "n": 2, "m": 0, "Term": "Defokus", "Koeffizient (Wellen)": 0.3}
