import copy
from pathlib import Path

from ns_sim.verification import (
    evaluate_cylinder_wake,
    evaluate_lid_driven_cavity,
    load_reference,
    observed_order,
    poiseuille_refinement,
    run_phase2_core_suite,
)


REFERENCE_DIR = Path(__file__).parents[1] / "verification" / "references"


def test_observed_order_recovers_second_order():
    assert observed_order(4.0, 1.0, 0.2, 0.1) == 2.0


def test_poiseuille_flow_rate_refines_at_second_order():
    report = poiseuille_refinement([17, 33, 65])
    assert min(report["observed_orders"]) > 1.99
    assert report["samples"][-1]["profile_linf_error"] < 1e-12
    assert report["samples"][-1]["wall_slip_linf"] == 0.0


def test_lid_driven_cavity_reference_gate_passes_reference_and_rejects_large_error():
    reference = load_reference(REFERENCE_DIR / "lid-driven-cavity-re100.json")
    candidate = {
        "reynolds_number": 100,
        "u_centerline": {
            "coordinate": reference["profiles"]["u_centerline"]["coordinate"],
            "velocity": reference["profiles"]["u_centerline"]["velocity"],
        },
        "v_centerline": {
            "coordinate": reference["profiles"]["v_centerline"]["coordinate"],
            "velocity": reference["profiles"]["v_centerline"]["velocity"],
        },
    }
    assert evaluate_lid_driven_cavity(candidate, reference)["passed"] is True
    bad = copy.deepcopy(candidate)
    bad["u_centerline"]["velocity"][8] += 0.2
    assert evaluate_lid_driven_cavity(bad, reference)["passed"] is False


def test_cylinder_wake_reference_gate_covers_strouhal_and_force_metrics():
    reference = load_reference(REFERENCE_DIR / "cylinder-wake-re100.json")
    candidate = dict(reference["metrics"])
    assert evaluate_cylinder_wake(candidate, reference)["passed"] is True
    candidate["strouhal"] += 0.03
    assert evaluate_cylinder_wake(candidate, reference)["passed"] is False


def test_phase2_core_suite_runs_taylor_green_and_poiseuille(example_raw):
    report = run_phase2_core_suite(example_raw, REFERENCE_DIR)
    assert report["passed"] is True
    assert report["cases"]["taylor_green"]["assessment"]["passed"] is True
    assert report["cases"]["poiseuille"]["assessment"]["passed"] is True
    assert report["cases"]["lid_driven_cavity"]["status"] == "reference_gate_ready"
    assert report["cases"]["cylinder_wake"]["status"] == "reference_gate_ready"
    assert report["validation_status"] == "not_claimed"
