from collections.abc import Sequence
from math import cos, fsum, hypot, isfinite, log10, radians, sin

_TIDAL_ZERO_POINT = 10.96


def spatial_separation_mpc(
    ra1: float,
    dec1: float,
    distance1: float,
    ra2: float,
    dec2: float,
    distance2: float,
) -> float:
    if not all(isfinite(value) for value in (ra1, dec1, distance1, ra2, dec2, distance2)):
        raise ValueError("Coordinates and distances must be finite")

    if not (0 <= ra1 < 360 and 0 <= ra2 < 360):
        raise ValueError("Right ascension must be in [0, 360)")

    if not (-90 <= dec1 <= 90 and -90 <= dec2 <= 90):
        raise ValueError("Declination must be in [-90, 90]")

    if distance1 <= 0 or distance2 <= 0:
        raise ValueError("Distances must be positive")

    def position(ra: float, dec: float, distance: float):
        alpha = radians(ra)
        delta = radians(dec)
        return (
            distance * cos(delta) * cos(alpha),
            distance * cos(delta) * sin(alpha),
            distance * sin(delta),
        )

    x1, y1, z1 = position(ra1, dec1, distance1)
    x2, y2, z2 = position(ra2, dec2, distance2)

    return hypot(x1 - x2, y1 - y2, z1 - z2)


def tidal_log_strength(
    log_lk: float,
    separation_mpc: float,
) -> float:
    if not isfinite(log_lk):
        raise ValueError("K-band luminosity must be finite")

    if not isfinite(separation_mpc) or separation_mpc <= 0:
        raise ValueError("Separation must be positive and finite")

    return log_lk - 3 * log10(separation_mpc)


def single_neighbor_tidal_index(
    log_lk: float,
    separation_mpc: float,
) -> float:
    return tidal_log_strength(log_lk, separation_mpc) - _TIDAL_ZERO_POINT


def tidal_indices_from_neighbors(
    neighbors: Sequence[tuple[str, float, float]],
) -> tuple[str, float, float | None]:
    if not neighbors:
        raise ValueError("At least one neighbor is required")

    strengths = []
    identifiers = set()

    for identifier, log_lk, separation in neighbors:
        if not identifier or identifier in identifiers:
            raise ValueError("Neighbor identifiers must be unique and nonempty")

        identifiers.add(identifier)
        strength = tidal_log_strength(log_lk, separation)
        strengths.append((identifier, strength))

    strengths.sort(key=lambda item: (-item[1], item[0]))

    main_disturber, strongest = strengths[0]
    theta1 = strongest - _TIDAL_ZERO_POINT

    theta5 = None

    if len(strengths) >= 5:
        normalized_sum = fsum(10 ** (strength - strongest) for _, strength in strengths[:5])
        theta5 = strongest + log10(normalized_sum) - _TIDAL_ZERO_POINT

    return main_disturber, theta1, theta5
