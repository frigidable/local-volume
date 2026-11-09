from math import isfinite, log10

_KS_SOLAR_ABSOLUTE_MAG = 3.28
_KS_TO_B_EXTINCTION_RATIO = 0.085


def intrinsic_b_minus_ks(t: float) -> float:
    if not isfinite(t):
        raise ValueError("Morphological type must be finite")

    if t < 3:
        return 4.10
    if t <= 8:
        return 4.60 - 0.25 * t
    return 2.35


def estimated_ks_from_b(
    b_mag: float,
    t: float,
    a_b_galactic: float,
    a_b_internal: float,
) -> float:
    if not all(isfinite(value) for value in (b_mag, a_b_galactic, a_b_internal)):
        raise ValueError("Photometric inputs must be finite")

    a_b_total = a_b_galactic + a_b_internal
    intrinsic_color = intrinsic_b_minus_ks(t)

    return b_mag - intrinsic_color - (1 - _KS_TO_B_EXTINCTION_RATIO) * a_b_total


def log_ks_luminosity(
    ks_mag: float,
    distance_modulus: float,
    a_b_galactic: float,
    a_b_internal: float,
) -> float:
    if not all(
        isfinite(value)
        for value in (
            ks_mag,
            distance_modulus,
            a_b_galactic,
            a_b_internal,
        )
    ):
        raise ValueError("Photometric inputs must be finite")

    a_ks = _KS_TO_B_EXTINCTION_RATIO * (a_b_galactic + a_b_internal)

    return 0.4 * (_KS_SOLAR_ABSOLUTE_MAG - ks_mag + distance_modulus + a_ks)


def distance_modulus_from_mpc(distance_mpc: float) -> float:
    if not isfinite(distance_mpc) or distance_mpc <= 0:
        raise ValueError("Distance must be positive and finite")

    return 5 * log10(distance_mpc) + 25
