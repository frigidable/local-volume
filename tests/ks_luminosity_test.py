import pytest

from lv_backend.domain.ks_luminosity import (
    distance_modulus_from_mpc,
    estimated_ks_from_b,
    intrinsic_b_minus_ks,
    log_ks_luminosity,
)


@pytest.mark.parametrize(
    ("t", "expected"),
    [
        (-5, 4.10),
        (0, 4.10),
        (2, 4.10),
        (3, 3.85),
        (5, 3.35),
        (8, 2.60),
        (9, 2.35),
        (10, 2.35),
    ],
)
def test_intrinsic_color(t: float, expected: float) -> None:
    assert intrinsic_b_minus_ks(t) == pytest.approx(expected)


def test_estimated_ks_without_extinction() -> None:
    assert estimated_ks_from_b(15, 5, 0, 0) == pytest.approx(11.65)


def test_estimated_ks_with_extinction() -> None:
    assert estimated_ks_from_b(15, 5, 0.2, 0.1) == pytest.approx(11.3755)


def test_ks_luminosity_without_extinction() -> None:
    assert log_ks_luminosity(11, 30, 0, 0) == pytest.approx(8.912)


def test_ks_luminosity_with_extinction() -> None:
    assert log_ks_luminosity(11.3755, 30, 0.2, 0.1) == pytest.approx(8.772)


def test_estimation_and_luminosity_consistency() -> None:
    ks = estimated_ks_from_b(15, 5, 0.2, 0.1)
    result = log_ks_luminosity(ks, 30, 0.2, 0.1)

    assert result == pytest.approx(8.772)


@pytest.mark.parametrize(
    "t",
    [float("nan"), float("inf"), float("-inf")],
)
def test_invalid_morphological_type(t: float) -> None:
    with pytest.raises(ValueError):
        intrinsic_b_minus_ks(t)


def test_invalid_photometry() -> None:
    with pytest.raises(ValueError):
        estimated_ks_from_b(float("nan"), 5, 0, 0)


def test_invalid_distance_modulus() -> None:
    with pytest.raises(ValueError):
        log_ks_luminosity(12, float("inf"), 0, 0)


def test_hizss003_archival_ks() -> None:
    ks = estimated_ks_from_b(18.0, 10, 4.66, 0.0)

    assert ks == pytest.approx(11.4, abs=0.05)
    assert log_ks_luminosity(ks, 29.11, 4.66, 0.0) == pytest.approx(8.56, abs=0.025)


def test_ngc0024_archival_luminosity() -> None:
    result = log_ks_luminosity(9.0, 29.32, 0.08, 0.64)

    assert result == pytest.approx(9.48, abs=0.025)


@pytest.mark.parametrize(
    ("distance", "ks", "a_b_g", "expected"),
    [
        (22.93, 14.6, 0.25, 8.19),
        (49.45, 13.3, 0.30, 9.40),
    ],
)
def test_archival_distance_fallback(
    distance: float,
    ks: float,
    a_b_g: float,
    expected: float,
) -> None:
    modulus = distance_modulus_from_mpc(distance)
    result = log_ks_luminosity(ks, modulus, a_b_g, 0.0)

    assert result == pytest.approx(expected, abs=0.025)


@pytest.mark.parametrize(
    "distance",
    [0.0, -1.0, float("nan"), float("inf")],
)
def test_invalid_distance(distance: float) -> None:
    with pytest.raises(ValueError):
        distance_modulus_from_mpc(distance)
