import copy
import json
from pathlib import Path

import numpy as np
import pytest

from ns_sim.canonical import identity_hash
from ns_sim.cuda_backend import (
    _assess_comparison_metrics,
    _run_array_backend,
    _run_cpu_reference_in_memory,
    enforce_cuda_provenance_lock,
    load_backend_comparison_contract,
)
from ns_sim.errors import ConfigurationError
from ns_sim.schema import normalize_experiment


CONTRACT = Path(__file__).parents[1] / "verification" / "backends" / "cuda-single-gpu-v1.json"


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


def test_backend_comparison_contract_has_explicit_nonnegative_tolerances():
    contract = load_backend_comparison_contract(CONTRACT)
    assert contract["reference_backend"] == "cpu-reference-v1"
    assert contract["candidate_backend"] == "cuda-single-gpu-v1"
    assert contract["metrics"]
    assert all(
        float(spec["absolute_tolerance"]) >= 0.0
        and float(spec["relative_tolerance"]) >= 0.0
        for spec in contract["metrics"].values()
    )


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


def test_cuda_provenance_lock_is_exact(tmp_path):
    environment = {
        "backend": "cuda-single-gpu-v1",
        "device_ordinal": 0,
        "gpu_name": "test-gpu",
        "compute_capability": [9, 0],
        "total_global_memory_bytes": 1,
        "cuda_driver_version": 13000,
        "cupy_linked_cuda_runtime_version": 13000,
        "local_cuda_runtime_version": 13000,
        "cupy_version": "14.1.1",
        "numpy_version": "2.0.0",
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
    lock = {
        "schema_version": "ns-sim-cuda-provenance-lock/1",
        "environment": environment,
    }
    lock_path = tmp_path / "cuda-lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")

    status = enforce_cuda_provenance_lock(environment, lock_path)
    assert status["matched"] is True

    changed = dict(environment)
    changed["cuda_driver_version"] += 1
    with pytest.raises(ConfigurationError, match="does not match"):
        enforce_cuda_provenance_lock(changed, lock_path)


def test_phase3_schema_artifacts_match_runtime_versions():
    root = Path(__file__).parents[1]
    provenance_schema = json.loads(
        (root / "schemas" / "cuda-provenance-lock-v1.schema.json").read_text()
    )
    comparison_schema = json.loads(
        (root / "schemas" / "backend-comparison-contract-v1.schema.json").read_text()
    )
    assert provenance_schema["properties"]["schema_version"]["const"] == "ns-sim-cuda-provenance-lock/1"
    assert provenance_schema["properties"]["environment"]["properties"]["backend"]["const"] == "cuda-single-gpu-v1"
    assert comparison_schema["properties"]["schema_version"]["const"] == "ns-sim-backend-comparison-contract/1"
    assert comparison_schema["properties"]["reference_backend"]["const"] == "cpu-reference-v1"
    assert comparison_schema["properties"]["candidate_backend"]["const"] == "cuda-single-gpu-v1"
