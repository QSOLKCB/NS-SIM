import copy
import json
from pathlib import Path

import numpy as np
import pytest
from jsonschema import Draft202012Validator

import ns_sim.cuda_backend as cuda_backend
from ns_sim.canonical import identity_hash
from ns_sim.cuda_backend import (
    MANDATORY_COMPARISON_METRICS,
    _assess_comparison_metrics,
    _run_array_backend,
    _run_cpu_reference_in_memory,
    _validate_comparison_scope,
    benchmark_cpu_cuda,
    capture_cuda_provenance,
    compare_cpu_cuda,
    enforce_cuda_provenance_lock,
    execute_cuda_experiment,
    load_backend_comparison_contract,
    verify_cuda_repeat,
)
from ns_sim.errors import ConfigurationError
from ns_sim.provenance import environment_provenance
from ns_sim.schema import normalize_experiment
from ns_sim.state import initialize_state


ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "verification" / "backends" / "cuda-single-gpu-v1.json"


def _cuda_environment() -> dict:
    environment = {
        "backend": "cuda-single-gpu-v1",
        "device_ordinal": 0,
        "device_uuid": "01234567-89ab-cdef-0123-456789abcdef",
        "pci_bus_id": "0000:01:00.0",
        "gpu_name": "test-gpu",
        "compute_capability": [9, 0],
        "total_global_memory_bytes": 16 * 1024**3,
        "cuda_driver_version": 13000,
        "cupy_linked_cuda_runtime_version": 13000,
        "local_cuda_runtime_version": 13000,
        "cupy_version": "14.1.1",
        "numpy_version": np.__version__,
        "python_implementation": "CPython",
        "python_version": "3.11.0",
        "platform_system": "Linux",
        "platform_release": "test",
        "machine": "x86_64",
        "byteorder": "little",
        "precision_contract": {"dtype": "float64", "byte_order": "little"},
        "single_gpu": True,
        "tf32_or_mixed_precision": False,
    }
    environment["environment_identity"] = identity_hash(environment)
    return environment


class _NullStream:
    @staticmethod
    def synchronize():
        return None


class _Stream:
    null = _NullStream()


class _CudaForTiming:
    Stream = _Stream


class _FakeCP:
    cuda = _CudaForTiming()


def _install_emulated_cuda(monkeypatch):
    environment = _cuda_environment()

    def fake_run(experiment, xp, *, collect_history=True, checkpoint_steps=None, checkpoint_callback=None):
        state, history = _run_cpu_reference_in_memory(experiment, collect_history=collect_history)
        checkpoint_steps = set() if checkpoint_steps is None else set(checkpoint_steps)
        if checkpoint_callback is not None and 0 in checkpoint_steps:
            checkpoint_callback(initialize_state(normalize_experiment(experiment)))
        if checkpoint_callback is not None and state.step in checkpoint_steps and state.step != 0:
            checkpoint_callback(state)
        return state, history

    monkeypatch.setattr(cuda_backend, "_load_cupy", lambda: _FakeCP())
    monkeypatch.setattr(cuda_backend, "capture_cuda_provenance", lambda device_id=0, cp=None: dict(environment))
    monkeypatch.setattr(cuda_backend, "_run_array_backend", fake_run)
    monkeypatch.setattr(cuda_backend, "_resolved_source_revision", lambda: ("a" * 40, True))
    return environment


def test_numpy_emulation_of_cuda_kernel_matches_cpu_reference(example_raw):
    experiment = normalize_experiment(example_raw)
    cpu_state, cpu_history = _run_cpu_reference_in_memory(experiment)
    emulated_state, emulated_history = _run_array_backend(experiment, np)

    assert np.array_equal(emulated_state.u, cpu_state.u)
    assert np.array_equal(emulated_state.v, cpu_state.v)
    assert np.array_equal(emulated_state.p, cpu_state.p)
    assert emulated_state.step == cpu_state.step
    assert emulated_state.time == cpu_state.time
    assert emulated_history == cpu_history


def test_cuda_candidate_keeps_cpu_reference_request_as_canonical_contract(example_raw):
    case = copy.deepcopy(example_raw)
    case["backend_request"]["name"] = "cuda-single-gpu-v1"
    with pytest.raises(ConfigurationError, match="cpu-reference-v1"):
        _run_array_backend(case, np)


def test_backend_comparison_contract_requires_complete_metric_set():
    contract = load_backend_comparison_contract(CONTRACT)
    assert set(contract["metrics"]) == set(MANDATORY_COMPARISON_METRICS)
    assert all(
        float(spec["absolute_tolerance"]) >= 0.0
        and float(spec["relative_tolerance"]) >= 0.0
        for spec in contract["metrics"].values()
    )


def test_backend_comparison_contract_rejects_missing_metric(tmp_path):
    contract = json.loads(CONTRACT.read_text())
    contract["metrics"].pop("pressure_residual_linf_abs_diff")
    path = tmp_path / "incomplete-contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="complete versioned metric set"):
        load_backend_comparison_contract(path)


def test_backend_comparison_scope_must_match_experiment(example_raw):
    experiment = normalize_experiment(example_raw)
    contract = load_backend_comparison_contract(CONTRACT)
    _validate_comparison_scope(contract, experiment)
    changed = copy.deepcopy(contract)
    changed["scope"]["pressure_solver"] = "some-other-solver"
    with pytest.raises(ConfigurationError, match="scope does not match"):
        _validate_comparison_scope(changed, experiment)


def test_backend_metric_assessment_fails_over_declared_tolerance():
    contract = load_backend_comparison_contract(CONTRACT)
    observed = {
        name: {"absolute_error": 0.0, "reference_scale": 1.0}
        for name in contract["metrics"]
    }
    passed, assessment = _assess_comparison_metrics(observed, contract)
    assert passed is True
    observed["u_linf"] = {
        "absolute_error": (
            float(contract["metrics"]["u_linf"]["absolute_tolerance"])
            + float(contract["metrics"]["u_linf"]["relative_tolerance"]) * 1.0
        ) * 2.0,
        "reference_scale": 1.0,
    }
    passed, assessment = _assess_comparison_metrics(observed, contract)
    assert passed is False
    assert assessment["u_linf"]["passed"] is False


def test_invalid_cuda_ordinal_fails_before_device_selection():
    class Runtime:
        @staticmethod
        def getDeviceCount():
            return 1

    class Cuda:
        runtime = Runtime()

    class CP:
        cuda = Cuda()

    with pytest.raises(ConfigurationError, match="outside available range"):
        capture_cuda_provenance(3, CP())


def test_cuda_provenance_lock_is_exact_and_binds_device_uuid(tmp_path):
    environment = _cuda_environment()
    lock = {
        "schema_version": "ns-sim-cuda-provenance-lock/1",
        "environment": environment,
    }
    lock_path = tmp_path / "cuda-lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")

    status = enforce_cuda_provenance_lock(environment, lock_path)
    assert status["matched"] is True

    changed = dict(environment)
    changed["device_uuid"] = "fedcba98-7654-3210-fedc-ba9876543210"
    changed["environment_identity"] = identity_hash(
        {key: value for key, value in changed.items() if key != "environment_identity"}
    )
    with pytest.raises(ConfigurationError, match="does not match"):
        enforce_cuda_provenance_lock(changed, lock_path)


def test_unknown_source_revision_withholds_r3(monkeypatch, example_raw):
    environment = _install_emulated_cuda(monkeypatch)
    monkeypatch.setattr(cuda_backend, "_resolved_source_revision", lambda: ("unknown", False))
    report = compare_cpu_cuda(example_raw, CONTRACT)
    assert report["numerical_gate_passed"] is True
    assert report["provenance_complete"] is False
    assert report["passed"] is False
    assert report["reproducibility_classification"]["R3_status"] == "withheld_missing_source_revision"
    assert report["candidate_backend"]["environment"] == environment


def test_cuda_run_records_cpu_initialization_environment(monkeypatch, tmp_path, example_raw):
    _install_emulated_cuda(monkeypatch)
    report = execute_cuda_experiment(example_raw, tmp_path / "run")
    cpu_environment = report["initialization_environment"]
    assert cpu_environment["backend"] == "cpu-reference-v1"
    assert report["reproducibility"]["R1_initialization_environment_identity"] == cpu_environment["environment_identity"]


def test_phase3_json_schemas_are_valid_and_validate_emitted_reports(monkeypatch, tmp_path, example_raw):
    _install_emulated_cuda(monkeypatch)
    schema_paths = {
        "provenance": ROOT / "schemas" / "cuda-provenance-lock-v1.schema.json",
        "contract": ROOT / "schemas" / "backend-comparison-contract-v1.schema.json",
        "run": ROOT / "schemas" / "cuda-run-v1.schema.json",
        "repeat": ROOT / "schemas" / "cuda-repeat-verification-v1.schema.json",
        "comparison": ROOT / "schemas" / "backend-comparison-report-v1.schema.json",
        "performance": ROOT / "schemas" / "backend-performance-v1.schema.json",
    }
    schemas = {name: json.loads(path.read_text()) for name, path in schema_paths.items()}
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)

    contract = json.loads(CONTRACT.read_text())
    Draft202012Validator(schemas["contract"]).validate(contract)

    provenance = {
        "schema_version": "ns-sim-cuda-provenance-lock/1",
        "environment": _cuda_environment(),
    }
    Draft202012Validator(schemas["provenance"]).validate(provenance)

    run = execute_cuda_experiment(example_raw, tmp_path / "cuda-run")
    Draft202012Validator(schemas["run"]).validate(run)

    repeat = verify_cuda_repeat(example_raw, tmp_path / "cuda-repeat")
    Draft202012Validator(schemas["repeat"]).validate(repeat)
    assert repeat["reproducibility_classification"]["R2_status"] == "demonstrated"

    comparison = compare_cpu_cuda(example_raw, CONTRACT)
    Draft202012Validator(schemas["comparison"]).validate(comparison)
    assert comparison["reproducibility_classification"]["R3_status"] == "demonstrated"

    performance = benchmark_cpu_cuda(example_raw, CONTRACT, warmup=0, repeats=1)
    Draft202012Validator(schemas["performance"]).validate(performance)


def test_output_schema_versions_match_runtime_constants():
    expected = {
        "cuda-run-v1.schema.json": "ns-sim-cuda-run/1",
        "cuda-repeat-verification-v1.schema.json": "ns-sim-cuda-repeat-verification/1",
        "backend-comparison-report-v1.schema.json": "ns-sim-backend-comparison/1",
        "backend-performance-v1.schema.json": "ns-sim-backend-performance/1",
    }
    for filename, version in expected.items():
        schema = json.loads((ROOT / "schemas" / filename).read_text())
        assert schema["properties"]["schema_version"]["const"] == version
