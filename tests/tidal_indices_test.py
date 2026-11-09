from math import log10, sqrt

import pytest

from lv_backend.domain.tidal_indices import (
    single_neighbor_tidal_index,
    spatial_separation_mpc,
    tidal_indices_from_neighbors,
    tidal_log_strength,
)


def test_same_sky_direction() -> None:
    assert spatial_separation_mpc(0, 0, 1, 0, 0, 2) == pytest.approx(1.0)


def test_perpendicular_directions() -> None:
    assert spatial_separation_mpc(0, 0, 1, 90, 0, 1) == pytest.approx(sqrt(2))


def test_opposite_directions() -> None:
    assert spatial_separation_mpc(0, 0, 1, 180, 0, 2) == pytest.approx(3.0)


def test_identical_positions() -> None:
    assert spatial_separation_mpc(40, 30, 5, 40, 30, 5) == pytest.approx(0.0, abs=1e-12)


def test_tidal_strength_at_one_mpc() -> None:
    assert tidal_log_strength(10, 1) == pytest.approx(10.0)


def test_inverse_cube_dependence() -> None:
    difference = tidal_log_strength(10, 2) - tidal_log_strength(10, 1)
    assert difference == pytest.approx(-3 * log10(2))


def test_single_neighbor_index() -> None:
    assert single_neighbor_tidal_index(11, 1) == pytest.approx(0.04)


@pytest.mark.parametrize(
    "values",
    [
        (-1, 0, 1, 0, 0, 2),
        (0, 91, 1, 0, 0, 2),
        (0, 0, 0, 0, 0, 2),
        (0, 0, 1, float("nan"), 0, 2),
    ],
)
def test_invalid_geometry(values: tuple[float, ...]) -> None:
    with pytest.raises(ValueError):
        spatial_separation_mpc(*values)


@pytest.mark.parametrize(
    ("luminosity", "separation"),
    [
        (10, 0),
        (10, -1),
        (float("nan"), 1),
        (10, float("inf")),
    ],
)
def test_invalid_tidal_strength(
    luminosity: float,
    separation: float,
) -> None:
    with pytest.raises(ValueError):
        tidal_log_strength(luminosity, separation)


def test_main_disturber_is_not_necessarily_nearest() -> None:
    neighbors = [
        ("near_dwarf", 8.0, 0.5),
        ("far_giant", 12.0, 2.0),
        ("other", 9.0, 1.0),
    ]

    md, theta1, theta5 = tidal_indices_from_neighbors(neighbors)

    assert md == "far_giant"
    assert theta1 == pytest.approx(12 - 3 * log10(2) - 10.96)
    assert theta5 is None


def test_five_neighbor_tidal_index() -> None:
    neighbors = [
        ("A", 11.0, 1.0),
        ("B", 10.0, 1.0),
        ("C", 9.0, 1.0),
        ("D", 8.0, 1.0),
        ("E", 7.0, 1.0),
    ]

    md, theta1, theta5 = tidal_indices_from_neighbors(neighbors)

    expected = log10(sum(10**value for value in (11, 10, 9, 8, 7))) - 10.96

    assert md == "A"
    assert theta1 == pytest.approx(0.04)
    assert theta5 == pytest.approx(expected)
    assert theta5 > theta1


def test_only_five_strongest_neighbors_are_used() -> None:
    neighbors = [
        ("A", 11.0, 1.0),
        ("B", 10.0, 1.0),
        ("C", 9.0, 1.0),
        ("D", 8.0, 1.0),
        ("E", 7.0, 1.0),
        ("F", 6.0, 1.0),
    ]

    full = tidal_indices_from_neighbors(neighbors)
    top_five = tidal_indices_from_neighbors(neighbors[:5])

    assert full == top_five


def test_neighbor_order_does_not_change_results() -> None:
    neighbors = [
        ("A", 11.0, 1.0),
        ("B", 10.0, 1.0),
        ("C", 9.0, 1.0),
        ("D", 8.0, 1.0),
        ("E", 7.0, 1.0),
    ]

    assert tidal_indices_from_neighbors(neighbors) == tidal_indices_from_neighbors(list(reversed(neighbors)))


def test_equal_strengths_have_deterministic_selection() -> None:
    neighbors = [
        ("B", 10.0, 1.0),
        ("A", 10.0, 1.0),
    ]

    md, theta1, theta5 = tidal_indices_from_neighbors(neighbors)

    assert md == "A"
    assert theta1 == pytest.approx(-0.96)
    assert theta5 is None


def test_empty_neighbor_sample() -> None:
    with pytest.raises(ValueError):
        tidal_indices_from_neighbors([])


def test_duplicate_neighbor_identifier() -> None:
    with pytest.raises(ValueError):
        tidal_indices_from_neighbors(
            [
                ("A", 10.0, 1.0),
                ("A", 9.0, 2.0),
            ]
        )


def test_stable_tidal_sum_at_large_luminosity() -> None:
    neighbors = [(str(i), float(1000 - i), 1.0) for i in range(5)]

    _, theta1, theta5 = tidal_indices_from_neighbors(neighbors)

    assert theta1 == pytest.approx(989.04)
    assert theta5 is not None
    assert theta5 > theta1
