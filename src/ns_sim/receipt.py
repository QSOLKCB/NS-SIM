from __future__ import annotations

from pathlib import Path

from .canonical import identity_hash, pretty_json

RECEIPT_SCHEMA_VERSION = "ns-sim-receipt/1"


def build_receipt(
    *,
    experiment: dict,
    experiment_hash: str,
    source_revision: str,
    environment: dict,
    initial_state_hash: str,
    final_state_hash: str,
    checkpoint_hashes: list[dict],
    diagnostic_history: list[dict],
) -> dict:
    target = experiment["reproducibility_policy"]["target"]
    result_identity = {
        "experiment_hash": experiment_hash,
        "environment_identity": environment["environment_identity"],
        "initial_state_hash": initial_state_hash,
        "final_state_hash": final_state_hash,
        "checkpoint_hashes": checkpoint_hashes,
    }
    return {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "run_id": identity_hash(result_identity),
        "run_status": "completed",
        "ns_sim_version": "0.1.0",
        "source_revision": source_revision,
        "experiment_name": experiment["experiment_name"],
        "experiment_hash": experiment_hash,
        "model": experiment["model"],
        "backend": {
            "name": "cpu-reference-v1",
            "precision": experiment["precision"],
            "environment": environment,
        },
        "reproducibility": {
            "target": target,
            "demonstrated": ["R0", "R1"],
            "R2_status": "not_demonstrated_by_single_execution",
        },
        "initial_state_hash": initial_state_hash,
        "final_state_hash": final_state_hash,
        "checkpoint_hashes": checkpoint_hashes,
        "diagnostics": diagnostic_history,
        "numerical_verification_status": "not_run_phase_1_runtime_only",
        "physical_validation_status": "not_claimed",
    }


def write_receipt(path: str | Path, receipt: dict) -> None:
    Path(path).write_text(pretty_json(receipt), encoding="utf-8")
