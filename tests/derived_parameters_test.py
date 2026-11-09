from unittest.mock import patch

import pytest

from lv_backend.data import objects as data_objects
from lv_backend.domain import derived_parameters
from lv_backend.domain import objects as domain_objects


def by_key(**kwargs):
    return {row.key: row for row in derived_parameters.calculate(**kwargs)}


def test_missing_values_are_not_zero() -> None:
    rows = by_key(distance_mpc=None)
    assert len(rows) == 7
    assert all(row.value is None for row in rows.values())
    assert rows["a_b_internal"].status == "missing_inputs"
    assert rows["theta1"].status == "not_calculated"


def test_distance_modulus_not_listed_as_derived() -> None:
    rows = by_key(distance_mpc=10.0)
    assert "mu" not in rows
    assert "dist" not in rows
    assert rows["log_lk"].value is None


def test_source_modulus_not_reported_as_derived() -> None:
    rows = by_key(distance_mpc=10.0, distance_modulus=30.0)
    assert "mu" not in rows
    assert "dist" not in rows


def test_complete_calibrated_photometry() -> None:
    rows = by_key(
        distance_mpc=10, b_magnitude=15, morphological_t=5,
        axis_ratio=0.22, w50=213, galactic_b_extinction=0.2,
    )
    assert rows["b_minus_ks_0"].value == pytest.approx(3.35)
    assert rows["a_b_internal"].value == pytest.approx(0.646137, abs=1e-5)
    assert rows["ks_est"].status == "available"
    assert rows["log_lk"].status == "available"


def test_missing_w50_does_not_imply_zero_attenuation() -> None:
    rows = by_key(distance_mpc=3, morphological_t=5, axis_ratio=0.2)
    assert rows["a_b_internal"].value is None
    assert rows["ks_est"].value is None


def test_invalid_distance_does_not_create_calculated_modulus() -> None:
    rows = by_key(distance_mpc=0)
    assert "mu" not in rows
    assert rows["log_lk"].value is None


def test_neighbor_completeness_guard() -> None:
    neighbors = [(str(i), 10.0 - i, 1.0) for i in range(5)]
    incomplete = by_key(distance_mpc=1, neighbors=neighbors)
    assert incomplete["theta1"].value is None
    complete = by_key(distance_mpc=1, neighbors=neighbors, neighbors_complete=True)
    assert complete["main_disturber"].value == "0"
    assert complete["theta1"].value == pytest.approx(-0.96)
    assert complete["theta5"].value is not None


def test_fewer_than_five_neighbors() -> None:
    rows = by_key(distance_mpc=1, neighbors=[("PGC1", 10, 1)], neighbors_complete=True)
    assert rows["theta1"].status == "available"
    assert rows["theta5"].value is None


def test_object_response_does_not_guess_science_inputs() -> None:
    row = dict.fromkeys(data_objects.DETAIL_COLUMNS)
    row.update(pgc=1, name="Example", type_name="Sc", dist=10.0,
               bt=15.0, a50=30.0, b50=10.0, names=[])
    with (
        patch.object(data_objects, "select_object", return_value=row),
        patch.object(data_objects, "select_schema", return_value={}),
    ):
        response = domain_objects.get_object(None, 1)
    assert response is not None
    derived = {item.key: item for item in response.derived}
    assert "mu" not in derived
    assert derived["a_b_internal"].value is None
    assert derived["ks_est"].value is None
    payload = response.model_dump(by_alias=True, exclude_none=True)
    assert payload["derived"][0]["key"] == "b_minus_ks_0"
    assert "value" not in payload["derived"][0]
