from math import asin, degrees, exp, isfinite, log10, radians, sin, sqrt


def intrinsic_axis_ratio(t: float) -> float:
    if t <= 8:
        q0 = 10 ** -(0.43 + 0.053 * t)
    elif t in (9, 10):
        q0 = 10 ** (-0.38)
    else:
        raise ValueError("Morphological type requires an explicit LV rule")

    if not 0 < q0 < 1:
        raise ValueError("Invalid intrinsic axial ratio")

    return q0


def inclination_degrees(q: float, q0: float) -> float:
    if not (0 < q <= 1):
        raise ValueError("Observed axial ratio must be in (0, 1]")
    if not (0 < q0 < 1):
        raise ValueError("Intrinsic axial ratio must be in (0, 1)")

    sin2_i = (1 - q**2) / (1 - q0**2)
    return degrees(asin(sqrt(min(1.0, max(0.0, sin2_i)))))


def internal_b_absorption(v_m: float, q: float) -> float:
    if not isfinite(v_m) or v_m < 0:
        raise ValueError("Invalid rotation amplitude")
    if not isfinite(q) or not 0 < q <= 1:
        raise ValueError("Invalid observed axial ratio")

    if 2 * v_m <= 78:
        return 0.0

    gamma_b = 1.54 + 2.54 * (log10(2 * v_m) - 2.5)
    return gamma_b * log10(1 / q)


_WT50_CANDIDATE = 24.0
_WC50_CANDIDATE = 120.0
_W50_FLOOR_CANDIDATE = 5.0


def corrected_w50_candidate(w50: float) -> float:
    if not isfinite(w50) or w50 <= 0:
        raise ValueError("W50 must be positive and finite")

    e = exp(-((w50 / _WC50_CANDIDATE) ** 2))
    corrected_sq = w50**2 + _WT50_CANDIDATE**2 * (1 - 2 * e) - 2 * w50 * _WT50_CANDIDATE * (1 - e)

    return max(_W50_FLOOR_CANDIDATE, sqrt(max(0.0, corrected_sq)))


def rotation_amplitude_candidate(w50: float, inclination_deg: float) -> float:
    if not isfinite(inclination_deg) or not 0 < inclination_deg <= 90:
        raise ValueError("Inclination must be in (0, 90] degrees")

    return corrected_w50_candidate(w50) / (2 * sin(radians(inclination_deg)))


def internal_b_from_w50_candidate(
    t: float,
    q: float,
    w50: float,
) -> float:
    q0 = intrinsic_axis_ratio(t)
    inclination = inclination_degrees(q, q0)
    vm = rotation_amplitude_candidate(w50, inclination)
    return internal_b_absorption(vm, q)


def internal_b_lvgdb_candidate(
    t: float | None,
    q: float | None,
    w50: float | None,
) -> float | None:
    if t is None or q is None:
        return None

    if not isfinite(q) or not 0 < q <= 1:
        raise ValueError("Invalid observed axial ratio")

    intrinsic_axis_ratio(t)

    if w50 is None:
        return 0.0

    return internal_b_from_w50_candidate(t, q, w50)
