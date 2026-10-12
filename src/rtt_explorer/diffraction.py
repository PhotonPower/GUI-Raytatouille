"""Pure helpers of the views "OPD / Wellenfront" and "Beugung": display approximations, sampling of
radii and focus shifts, Zernike names. No streamlit, no raytatouille; the physics comes from the library.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

# Low-order Zernike terms (n, m) -> German name; for m != 0 the pair is (cosine, sine) after Noll.
_NAMES: dict[tuple[int, int], tuple[str, str]] = {
    (0, 0): ("Kolben (Piston)", ""),
    (1, 1): ("Kippung x", "Kippung y"),
    (2, 0): ("Defokus", ""),
    (2, 2): ("Astigmatismus 0°", "Astigmatismus 45°"),
    (3, 1): ("Koma x", "Koma y"),
    (3, 3): ("Dreiblatt x", "Dreiblatt y"),
    (4, 0): ("Sphärische Aberration", ""),
    (6, 0): ("Sphärische Aberration 2. Ordnung", ""),
}


def _finite_positive(value: float | None) -> bool:
    return value is not None and math.isfinite(value) and value > 0.0


def airy_radius_um(wavelength_um: float, working_fnumber: float | None) -> float | None:
    """Radius of the first dark ring of the Airy disc in µm, a display approximation.

    Formula: r = 1.22 · λ · N_w with the paraxial working f-number N_w = 1 / (2 |n' u'|) of the
    library (valid for finite conjugates too, unlike |EFL| / EPD). None without a finite N_w.
    """
    if not _finite_positive(working_fnumber):
        return None
    return 1.22 * wavelength_um * working_fnumber


def rayleigh_depth_mm(wavelength_um: float, working_fnumber: float | None) -> float | None:
    """Rayleigh depth of focus ±δz in mm, a display approximation to scale the focus range.

    Formula: δz = 2 · λ · N_w² (quarter-wave defocus); None without a finite N_w.
    """
    if not _finite_positive(working_fnumber):
        return None
    return 2.0 * wavelength_um * 1e-3 * working_fnumber**2


def marechal_strehl(rms_waves: float, reference_um: float, wavelength_um: float) -> float:
    """Strehl ratio after Maréchal, a display approximation for libraries without a Zernike fit.

    Formula: S = exp(−(2π · σ · λ_ref / λ)²) with σ the RMS wavefront error in waves at the
    reference wavelength λ_ref (the phase at λ is 2π W λ_ref / λ); good down to about S = 0.1.
    """
    return math.exp(-((2.0 * math.pi * rms_waves * reference_um / wavelength_um) ** 2))


def focus_shifts(half_range_mm: float, steps: int) -> list[float]:
    """``steps`` focus shifts evenly from −half_range to +half_range (mm); odd counts contain 0."""
    if not (math.isfinite(half_range_mm) and half_range_mm > 0.0):
        raise ValueError("Der Fokusbereich muss größer als 0 sein.")
    if steps < 2:
        raise ValueError("Es braucht mindestens zwei Fokuslagen.")
    step = 2.0 * half_range_mm / (steps - 1)
    return [0.0 if 2 * k == steps - 1 else -half_range_mm + k * step for k in range(steps)]


def ee_radii(radius_max_mm: float, count: int) -> list[float]:
    """``count`` radii from radius_max / count up to radius_max (mm), for the encircled energy."""
    # the last radius is radius_max itself: the library rejects anything above it, even by one ulp
    return [radius_max_mm * (k + 1) / count for k in range(count - 1)] + [radius_max_mm]


def radius_at_energy(radii: Sequence[float], energy: Sequence[float], level: float) -> float | None:
    """Smallest radius where the encircled energy reaches ``level``, interpolated linearly from EE(0) = 0.

    None if the energy stays below ``level`` up to the last radius.
    """
    r0, e0 = 0.0, 0.0
    for r, e in zip(radii, energy):
        if e >= level:
            return r0 + (level - e0) * (r - r0) / (e - e0) if e > e0 else r
        r0, e0 = r, e
    return None


def zernike_name(j: int, n: int, m: int) -> str:
    """Name of the Noll term j = (n, m): even j is the cosine, odd j the sine term for m != 0."""
    names = _NAMES.get((n, m))
    if m == 0:
        return names[0] if names else f"Z({n}, 0)"
    sine = j % 2 == 1
    if names:
        return names[1] if sine else names[0]
    return f"Z({n}, {m}) {'sin' if sine else 'cos'}"


def zernike_rows(coefficients: Sequence[float], nm: Sequence[tuple[int, int]]) -> list[dict]:
    """Table rows of a Zernike fit: Noll index, (n, m), name and coefficient in waves."""
    return [{"j": j, "n": n, "m": m, "Term": zernike_name(j, n, m), "Koeffizient (Wellen)": float(c)}
            for j, (c, (n, m)) in enumerate(zip(coefficients, nm), start=1)]
