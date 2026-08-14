import copy
from pathlib import Path

import pytest

from ns_sim.errors import NumericalError
from ns_sim.verification import (
    evaluate_cylinder_wake,
    evaluate_lid_driven_cavity,
    load_reference,
    observed_order,
    poiseuille_refinement,
    run_phase2_core_suite,
    taylor_green_spatial_refinement,
)


REFERENCE_DIR = Path(__file__).parents[1] / "verification" / "references"


def test_observed_order_recovers_second_order():
    assert observed_order(4.0, 1.0, 0.2, 0.1) == 2.0


def test_poiseuille_flow_rate_refines_at_second_order_and_declares_forcing():
    report = poiseuille_refinement([17, 33, 65])
    assert min(report["observed_orders"]) > 1.99
    assert report["samples"][-1]["profile_linf_error"] < 1e-12
    assert report["samples"][-1]["wall_slip_linf"] == 0.0
    assert report["parameters"]["forcing"] == {
        "representation": "specific_body_force_acceleration",
        "units_or_nondimensional_convention": "nondimensional",
        "value": 1.0,
    }


def _cavity_candidate(reference):
    return {
        "case": "lid-driven-cavity",
        "regime": copy.deepcopy(reference["regime"]),
        "u_centerline": {
            "coordinate": reference["profiles"]["u_centerline"]["coordinate"],
            "velocity": reference["profiles"]["u_centerline"]["velocity"],
        },
        "v_centerline": {
            "coordinate": reference["profiles"]["v_centerline"]["coordinate"],
            "velocity": reference["profiles"]["v_centerline"]["velocity"],
        },
    }


def test_lid_driven_cavity_reference_gate_passes_reference_and_rejects_large_error():
    reference = load_reference(REFERENCE_DIR / "lid-driven-cavity-re100.json")
    candidate = _cavity_candidate(reference)
    assert evaluate_lid_driven_cavity(candidate, reference)["passed"] is True
    bad = copy.deepcopy(candidate)
    bad["u_centerline"]["velocity"][8] += 0.2
    assert evaluate_lid_driven_cavity(bad, reference)["passed"] is False


def test_lid_driven_cavity_rejects_nonintegral_wrong_reynolds_number():
    reference = load_reference(REFERENCE_DIR / "lid-driven-cavity-re100.json")
    candidate = _cavity_candidate(reference)
    candidate["regime"]["reynolds_number"] = 100.9
    with pytest.raises(ValueError, match="Reynolds"):
        evaluate_lid_driven_cavity(candidate, reference)


def test_lid_driven_cavity_malformed_candidate_is_value_error():
    reference = load_reference(REFERENCE_DIR / "lid-driven-cavity-re100.json")
    candidate = _cavity_candidate(reference)
    del candidate["u_centerline"]
    with pytest.raises(ValueError, match="u_centerline"):
        evaluate_lid_driven_cavity(candidate, reference)


def _cylinder_candidate(reference):
    return {
        "case": "cylinder-wake",
        "regime": copy.deepcopy(reference["regime"]),
        "observable_definitions": copy.deepcopy(reference["observable_definitions"]),
        "metrics": copy.deepcopy(reference["metrics"]),
    }


def test_cylinder_wake_reference_gate_covers_strouhal_force_and_contract():
    reference = load_reference(REFERENCE_DIR / "cylinder-wake-re100.json")
    candidate = _cylinder_candidate(reference)
    assert evaluate_cylinder_wake(candidate, reference)["passed"] is True
    candidate["metrics"]["strouhal"] += 0.03
    assert evaluate_cylinder_wake(candidate, reference)["passed"] is False


def test_cylinder_wake_rejects_mismatched_regime_or_observable_definition():
    reference = load_reference(REFERENCE_DIR / "cylinder-wake-re100.json")
    candidate = _cylinder_candidate(reference)
    candidate["regime"]["reference_time_step"] = 0.01
    with pytest.raises(ValueError, match="regime"):
        evaluate_cylinder_wake(candidate, reference)

    candidate = _cylinder_candidate(reference)
    candidate["observable_definitions"]["cd_mean"] = "different force normalization"
    with pytest.raises(ValueError, match="observable_definitions"):
        evaluate_cylinder_wake(candidate, reference)


def test_taylor_green_spatial_refinement_requires_common_final_time(example_raw):
    with pytest.raises(ValueError, match="common final time"):
        taylor_green_spatial_refinement(
            example_raw,
            [
                {"n": 16, "dt": 0.000125, "steps": 8},
                {"n": 32, "dt": 0.000125, "steps": 9},
            ],
        )


def test_phase2_rejects_forced_taylor_green_contract(example_raw):
    case = copy.deepcopy(example_raw)
    case["forcing"]["value"] = [0.01, 0.0]
    with pytest.raises(ValueError, match="zero canonical body force"):
        run_phase2_core_suite(case, REFERENCE_DIR)


def test_taylor_green_refinement_enforces_declared_admissibility(example_raw):
    case = copy.deepcopy(example_raw)
    case["timestep_policy"]["max_diffusion_number"] = 1e-12
    with pytest.raises(NumericalError, match="diffusion number exceeded"):
        run_phase2_core_suite(case, REFERENCE_DIR)


def test_phase2_core_suite_runs_with_bound_regimes_richardson_order_and_provenance(example_raw):
    report = run_phase2_core_suite(example_raw, REFERENCE_DIR)
    assert report["passed"] is True
    assert report["cases"]["taylor_green"]["assessment"]["passed"] is True
    assert report["cases"]["poiseuille"]["assessment"]["passed"] is True
    temporal = report["cases"]["taylor_green"]["report"]["temporal"]
    assert len(temporal["successive_velocity_l2_differences"]) == 2
    assert min(temporal["observed_orders"]) >= 0.9
    assert report["cases"]["lid_driven_cavity"]["status"] == "reference_gate_ready"
    assert report["cases"]["cylinder_wake"]["status"] == "reference_gate_ready"
    provenance = report["provenance"]
    assert len(provenance["normalized_experiment_identity"]) == 64
    assert provenance["backend"] == "cpu-reference-v1"
    assert provenance["precision"] == {"dtype": "float64", "byte_order": "little"}
    assert set(provenance["reference_identities"]) == {
        "taylor_green",
        "poiseuille",
        "lid_driven_cavity",
        "cylinder_wake",
    }
    assert all(len(item["identity"]) == 64 for item in provenance["reference_identities"].values())
    assert provenance["environment"]["environment_identity"]
    assert report["validation_status"] == "not_claimed"
