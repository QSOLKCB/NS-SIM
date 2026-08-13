from pathlib import Path

from ns_sim.runtime import execute_experiment, verify_repeat
from ns_sim.schema import load_experiment


def test_runtime_emits_receipt_and_checkpoints(tmp_path):
    experiment = Path(__file__).parents[1] / "examples" / "phase1-periodic-vortex.json"
    receipt = execute_experiment(experiment, tmp_path / "run")
    assert receipt["run_status"] == "completed"
    assert receipt["reproducibility"]["demonstrated"] == ["R0", "R1"]
    assert receipt["physical_validation_status"] == "not_claimed"
    assert receipt["backend"]["environment"]["state_serialization_contract"] == "ns-sim-state/1"
    assert (tmp_path / "run" / "receipt.json").is_file()
    assert [x["step"] for x in receipt["checkpoint_hashes"]] == [0, 2, 4]


def test_execute_accepts_load_experiment_result(tmp_path):
    path = Path(__file__).parents[1] / "examples" / "phase1-periodic-vortex.json"
    normalized = load_experiment(path)
    receipt = execute_experiment(normalized, tmp_path / "normalized-run")
    assert receipt["experiment_hash"]
    assert receipt["run_status"] == "completed"


def test_repeat_verification_demonstrates_r2(tmp_path):
    experiment = Path(__file__).parents[1] / "examples" / "phase1-periodic-vortex.json"
    report = verify_repeat(experiment, tmp_path / "repeat")
    assert report["bitwise_match"] is True
    assert report["reproducibility_class"] == "R2"
    assert all(report["comparisons"].values())
