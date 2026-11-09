import pytest

from lv_backend.domain.internal_attenuation import (
    corrected_w50_candidate,
    inclination_degrees,
    internal_b_absorption,
    internal_b_from_w50_candidate,
    internal_b_lvgdb_candidate,
    intrinsic_axis_ratio,
    rotation_amplitude_candidate,
)


def test_ngc0024_inclination() -> None:
    q0 = intrinsic_axis_ratio(5)

    assert q0 == pytest.approx(0.201837, abs=1e-6)
    assert round(inclination_degrees(0.22, q0)) == 85


def test_face_on_galaxy() -> None:
    assert inclination_degrees(1.0, 0.2) == pytest.approx(0.0)


def test_edge_on_limit() -> None:
    assert inclination_degrees(0.2, 0.2) == pytest.approx(90.0)


def test_invalid_axis_ratio() -> None:
    with pytest.raises(ValueError):
        inclination_degrees(0.0, 0.2)


def test_axis_ratio_below_intrinsic_limit() -> None:
    assert inclination_degrees(0.1, 0.2) == pytest.approx(90.0)


def test_wlm_inclination_from_ungc() -> None:

    q0 = intrinsic_axis_ratio(9)
    assert inclination_degrees(0.35, q0) == pytest.approx(90.0)


def test_late_type_intrinsic_axis_ratio() -> None:
    assert intrinsic_axis_ratio(9) == pytest.approx(10 ** (-0.38))
    assert intrinsic_axis_ratio(10) == pytest.approx(10 ** (-0.38))


def test_late_type_inclination() -> None:
    q0 = intrinsic_axis_ratio(10)
    assert inclination_degrees(0.5, q0) == pytest.approx(72.31828, abs=1e-4)


def test_unsupported_morphological_type() -> None:
    with pytest.raises(ValueError):
        intrinsic_axis_ratio(11)


def test_ngc0024_internal_absorption() -> None:
    assert internal_b_absorption(95, 0.22) == pytest.approx(0.643133, abs=1e-5)


def test_ngc0045_internal_absorption() -> None:
    assert internal_b_absorption(103, 0.69) == pytest.approx(0.171984, abs=1e-5)


def test_wlm_internal_absorption() -> None:
    assert internal_b_absorption(22, 0.35) == 0.0


def test_agc748778_internal_absorption() -> None:
    assert internal_b_absorption(3, 0.52) == 0.0


def test_absorption_velocity_threshold() -> None:
    assert internal_b_absorption(39, 0.3) == 0.0
    assert internal_b_absorption(40, 0.3) > 0


@pytest.mark.parametrize(
    ("v_m", "q"),
    [(95, 0), (95, 1.1), (-1, 0.5), (float("nan"), 0.5)],
)
def test_invalid_absorption_input(v_m: float, q: float) -> None:
    with pytest.raises(ValueError):
        internal_b_absorption(v_m, q)


def test_narrow_w50_candidate_floor() -> None:
    assert corrected_w50_candidate(16) == pytest.approx(5.0)


def test_ngc0024_candidate_rotation() -> None:
    q0 = intrinsic_axis_ratio(5)
    i = inclination_degrees(0.22, q0)

    assert rotation_amplitude_candidate(213, i) == pytest.approx(95.394252, abs=1e-5)


def test_wlm_candidate_rotation() -> None:
    q0 = intrinsic_axis_ratio(9)
    i = inclination_degrees(0.35, q0)

    assert rotation_amplitude_candidate(53, i) == pytest.approx(22.283998, abs=1e-5)


def test_eso318013_known_discrepancy() -> None:
    q0 = intrinsic_axis_ratio(8)
    i = inclination_degrees(0.14, q0)

    assert rotation_amplitude_candidate(54, i) == pytest.approx(22.781862, abs=1e-5)


@pytest.mark.parametrize("w50", [0, -1, float("nan"), float("inf")])
def test_invalid_w50_candidate(w50: float) -> None:
    with pytest.raises(ValueError):
        corrected_w50_candidate(w50)


def test_face_on_rotation_amplitude_is_undefined() -> None:
    with pytest.raises(ValueError):
        rotation_amplitude_candidate(100, 0)


def test_complete_ngc0024_candidate() -> None:
    assert internal_b_from_w50_candidate(5, 0.22, 213) == pytest.approx(0.64, abs=0.01)


def test_complete_wlm_candidate() -> None:
    assert internal_b_from_w50_candidate(9, 0.35, 53) == 0.0


def test_complete_rejects_unsupported_type() -> None:
    with pytest.raises(ValueError):
        internal_b_from_w50_candidate(11, 0.5, 50)


def test_complete_rejects_face_on_undefined_rotation() -> None:
    with pytest.raises(ValueError):
        internal_b_from_w50_candidate(5, 1.0, 100)


def test_catalog_missing_geometry_returns_none() -> None:
    assert internal_b_lvgdb_candidate(11, None, 50) is None
    assert internal_b_lvgdb_candidate(None, 0.5, 50) is None


def test_catalog_missing_width_returns_zero() -> None:
    assert internal_b_lvgdb_candidate(-2, 1.0, None) == 0.0


def test_catalog_early_type_nonzero_absorption() -> None:
    assert internal_b_lvgdb_candidate(-2, 0.71, 207) == pytest.approx(0.18, abs=0.01)


def test_catalog_invalid_axis_ratio() -> None:
    with pytest.raises(ValueError):
        internal_b_lvgdb_candidate(5, 0.0, None)
