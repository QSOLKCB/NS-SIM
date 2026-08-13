from __future__ import annotations

from pathlib import Path

from .canonical import canonical_json_bytes, identity_hash, pretty_json
from .diagnostics import compute_diagnostics, enforce_hard_conditions
from .errors import ConfigurationError
from .provenance import environment_provenance, source_revision
from .receipt import build_receipt, write_receipt
from .schema import load_experiment, normalize_experiment
from .solver import advance_one_step
from .state import initialize_state, state_hash, write_checkpoint


def _prepare_output(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise ConfigurationError(f"output directory is not empty: {path}")
    path.mkdir(parents=True, exist_ok=True)


def _checkpoint_record(output: Path, state, experiment_hash: str) -> dict:
    rel = Path("checkpoints") / f"step-{state.step:08d}.nss"
    digest = write_checkpoint(output / rel, state, experiment_hash)
    return {"step": state.step, "path": rel.as_posix(), "sha256": digest}


def execute_experiment(experiment_or_path: dict | str | Path, output_dir: str | Path) -> dict:
    experiment = (
        normalize_experiment(experiment_or_path)
        if isinstance(experiment_or_path, dict)
        else load_experiment(experiment_or_path)
    )
    output = Path(output_dir)
    _prepare_output(output)
    experiment_hash = identity_hash(experiment)
    (output / "experiment.normalized.json").write_text(pretty_json(experiment), encoding="utf-8")
    (output / "experiment.identity.json").write_bytes(canonical_json_bytes(experiment) + b"\n")

    initial = initialize_state(experiment)
    initial_again = initialize_state(experiment)
    initial_hash = state_hash(initial, experiment_hash)
    if state_hash(initial_again, experiment_hash) != initial_hash:
        raise ConfigurationError("canonical initialization failed R1 byte-identity check")

    checkpoints: list[dict] = []
    checkpoint_steps: set[int] = set()
    policy = experiment["checkpoint_policy"]
    if policy["include_initial"]:
        record = _checkpoint_record(output, initial, experiment_hash)
        checkpoints.append(record)
        checkpoint_steps.add(0)

    state = initial
    history: list[dict] = []
    initial_diag = compute_diagnostics(state, experiment)
    enforce_hard_conditions(initial_diag, experiment)
    history.append(initial_diag)

    total_steps = experiment["stopping_condition"]["steps"]
    diag_interval = experiment["diagnostics"]["interval"]
    for _ in range(total_steps):
        pre_diag = compute_diagnostics(state, experiment)
        enforce_hard_conditions(pre_diag, experiment)
        state, pressure_info = advance_one_step(state, experiment)
        post_diag = compute_diagnostics(state, experiment, pressure_info)
        enforce_hard_conditions(post_diag, experiment)
        if state.step % diag_interval == 0 or state.step == total_steps:
            history.append(post_diag)
        if state.step % policy["interval"] == 0:
            record = _checkpoint_record(output, state, experiment_hash)
            checkpoints.append(record)
            checkpoint_steps.add(state.step)

    if policy["include_final"] and state.step not in checkpoint_steps:
        checkpoints.append(_checkpoint_record(output, state, experiment_hash))

    final_hash = state_hash(state, experiment_hash)
    env = environment_provenance()
    receipt = build_receipt(
        experiment=experiment,
        experiment_hash=experiment_hash,
        source_revision=source_revision(),
        environment=env,
        initial_state_hash=initial_hash,
        final_state_hash=final_hash,
        checkpoint_hashes=checkpoints,
        diagnostic_history=history,
    )
    write_receipt(output / "receipt.json", receipt)
    return receipt


def verify_repeat(experiment_or_path: dict | str | Path, output_dir: str | Path) -> dict:
    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise ConfigurationError(f"output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    receipt_a = execute_experiment(experiment_or_path, output / "run-a")
    receipt_b = execute_experiment(experiment_or_path, output / "run-b")

    checkpoint_a = [(item["step"], item["sha256"]) for item in receipt_a["checkpoint_hashes"]]
    checkpoint_b = [(item["step"], item["sha256"]) for item in receipt_b["checkpoint_hashes"]]
    comparisons = {
        "experiment_hash": receipt_a["experiment_hash"] == receipt_b["experiment_hash"],
        "environment_identity": (
            receipt_a["backend"]["environment"]["environment_identity"]
            == receipt_b["backend"]["environment"]["environment_identity"]
        ),
        "initial_state_hash": receipt_a["initial_state_hash"] == receipt_b["initial_state_hash"],
        "final_state_hash": receipt_a["final_state_hash"] == receipt_b["final_state_hash"],
        "checkpoint_hashes": checkpoint_a == checkpoint_b,
        "diagnostics": receipt_a["diagnostics"] == receipt_b["diagnostics"],
    }
    bitwise_match = all(comparisons.values())
    report = {
        "schema_version": "ns-sim-repeat-verification/1",
        "backend": "cpu-reference-v1",
        "environment_identity": receipt_a["backend"]["environment"]["environment_identity"],
        "experiment_hash": receipt_a["experiment_hash"],
        "comparisons": comparisons,
        "bitwise_match": bitwise_match,
        "reproducibility_class": "R2" if bitwise_match else "R1",
    }
    (output / "repeat-verification.json").write_text(pretty_json(report), encoding="utf-8")
    if not bitwise_match:
        raise ConfigurationError("repeat execution failed backend-local byte-identity comparison")
    return report
