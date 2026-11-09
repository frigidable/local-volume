from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Literal

from lv_backend.domain import internal_attenuation, ks_luminosity, tidal_indices

Status = Literal["available", "missing_inputs", "invalid_input", "not_calculated"]


@dataclass(frozen=True)
class CalculatedParameter:
    key: str
    label: str
    unit: str | None
    method: str
    value: float | str | None
    status: Status
    reason: str | None


def _missing(
    key: str, label: str, unit: str | None, method: str, reason: str,
    status: Status = "missing_inputs",
) -> CalculatedParameter:
    return CalculatedParameter(key, label, unit, method, None, status, reason)


def _number(
    key: str,
    label: str,
    unit: str | None,
    required: dict[str, float | None],
    calculate: Callable[[], float],
    method: str,
) -> CalculatedParameter:
    missing = [name for name, value in required.items() if value is None]
    if missing:
        return _missing(key, label, unit, method, "Missing: " + ", ".join(missing))
    try:
        result = calculate()
        if not isfinite(result):
            raise ValueError("Non-finite result")
    except (ValueError, ArithmeticError) as error:
        return _missing(key, label, unit, method, str(error), "invalid_input")
    return CalculatedParameter(key, label, unit, method, result, "available", None)


def _required(value: float | None) -> float:
    if value is None:
        raise ValueError("Missing required science input")
    return value


def _numeric(item: CalculatedParameter) -> float | None:
    return item.value if isinstance(item.value, float) else None


def calculate(
    *,
    distance_mpc: float | None,
    b_magnitude: float | None = None,
    morphological_t: float | None = None,
    axis_ratio: float | None = None,
    w50: float | None = None,
    galactic_b_extinction: float | None = None,
    ks_magnitude: float | None = None,
    neighbors: Sequence[tuple[str, float, float]] | None = None,
    neighbors_complete: bool = False,
) -> list[CalculatedParameter]:
    modulus = _number(
        "mu", "Distance modulus", "mag", {"distance (Mpc)": distance_mpc},
        lambda: ks_luminosity.distance_modulus_from_mpc(_required(distance_mpc)),
        "5 log10(dist / Mpc) + 25",
    )
    color = _number(
        "b_minus_ks_0", "Intrinsic B−Ks colour", "mag", {"morphological T": morphological_t},
        lambda: ks_luminosity.intrinsic_b_minus_ks(_required(morphological_t)),
        "LVGDB morphology–colour calibration",
    )
    attenuation = _number(
        "a_b_internal", "Internal B attenuation", "mag",
        {"morphological T": morphological_t, "axis ratio b/a": axis_ratio, "HI W50": w50},
        lambda: internal_attenuation.internal_b_from_w50_candidate(
            _required(morphological_t), _required(axis_ratio), _required(w50)
        ),
        "LVGDB internal attenuation (W50 candidate)",
    )
    estimated_ks = _number(
        "ks_est", "Estimated Ks magnitude", "mag",
        {
            "B magnitude": b_magnitude,
            "morphological T": morphological_t,
            "Galactic B extinction": galactic_b_extinction,
            "internal B attenuation": _numeric(attenuation),
        },
        lambda: ks_luminosity.estimated_ks_from_b(
            _required(b_magnitude), _required(morphological_t),
            _required(galactic_b_extinction), _required(_numeric(attenuation))
        ),
        "LVGDB B-to-Ks estimate",
    )
    usable_ks = ks_magnitude if ks_magnitude is not None else _numeric(estimated_ks)
    log_lk = _number(
        "log_lk", "Ks luminosity", "dex(L☉)",
        {
            "distance modulus": _numeric(modulus),
            "verified Ks magnitude": usable_ks,
            "Galactic B extinction": galactic_b_extinction,
            "internal B attenuation": _numeric(attenuation),
        },
        lambda: ks_luminosity.log_ks_luminosity(
            _required(usable_ks), _required(_numeric(modulus)),
            _required(galactic_b_extinction), _required(_numeric(attenuation))
        ),
        "LVGDB Ks luminosity",
    )

    labels = (
        ("main_disturber", "Main Disturber", "PGC"),
        ("theta1", "Tidal index Θ₁", None),
        ("theta5", "Tidal index Θ₅", None),
    )
    if not neighbors_complete:
        tidal = [
            _missing(key, label, unit, "LVGDB tidal indices",
                     "Complete, versioned neighbor sample is unavailable", "not_calculated")
            for key, label, unit in labels
        ]
    elif not neighbors:
        tidal = [
            _missing(key, label, unit, "LVGDB tidal indices", "No validated neighbors")
            for key, label, unit in labels
        ]
    else:
        try:
            disturber, theta1, theta5 = tidal_indices.tidal_indices_from_neighbors(neighbors)
        except (ValueError, ArithmeticError) as error:
            tidal = [
                _missing(key, label, unit, "LVGDB tidal indices", str(error), "invalid_input")
                for key, label, unit in labels
            ]
        else:
            tidal = [
                CalculatedParameter("main_disturber", "Main Disturber", "PGC",
                                    "LVGDB tidal indices", disturber, "available", None),
                CalculatedParameter("theta1", "Tidal index Θ₁", None,
                                    "LVGDB tidal indices", theta1, "available", None),
                (
                    CalculatedParameter("theta5", "Tidal index Θ₅", None, "LVGDB tidal indices",
                                        theta5, "available", None)
                    if theta5 is not None
                    else _missing("theta5", "Tidal index Θ₅", None, "LVGDB tidal indices",
                                  "Fewer than five validated neighbors")
                ),
            ]
    return [modulus, color, attenuation, estimated_ks, log_lk, *tidal]
