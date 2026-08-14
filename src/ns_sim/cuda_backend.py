from __future__ import annotations

from dataclasses import dataclass
import json
import math
import platform
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from .canonical import canonical_json_bytes, identity_hash, pretty_json
from .diagnostics import compute_diagnostics, enforce_hard_conditions
from .errors import ConfigurationError, NumericalError
from .provenance import environment_provenance, source_revision
from .schema import load_experiment, normalize_experiment
from .solver import advance_one_step
from .state import State, grid_spacing, initialize_state, state_hash, write_checkpoint

CUDA_BACKEND = "cuda-single-gpu-v1"
CUDA_RUN_SCHEMA = "ns-sim-cuda-run/1"
CUDA_REPEAT_SCHEMA = "ns-sim-cuda-repeat-verification/1"
CUDA_COMPARISON_SCHEMA = "ns-sim-backend-comparison/1"
CUDA_BENCHMARK_SCHEMA = "ns-sim-backend-performance/1"
CUDA_PROVENANCE_LOCK_SCHEMA = "ns-sim-cuda-provenance-lock/1"
CUDA_COMPARISON_CONTRACT_SCHEMA = "ns-sim-backend-comparison-contract/1"


@dataclass
class DeviceState:
    u: Any
    v: Any
    p: Any
    step: int
    time: float


def _prepare_output(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise ConfigurationError(f"output directory is not empty: {path}")
    path.mkdir(parents=True, exist_ok=True)


def _load_cupy():
    try:
        import cupy as cp
    except ImportError as exc:
        raise ConfigurationError(
            "CUDA backend requires CuPy; install exactly one supported CuPy wheel "
            "(for example the NS-SIM cuda12 or cuda13 optional dependency)"
        ) from exc
    return cp


def _scalar(value: Any) -> float:
    if hasattr(value, "item"):
        return float(value.item())
    return float(value)


def _bool_scalar(value: Any) -> bool:
    if hasattr(value, "item"):
        return bool(value.item())
    return bool(value)


def _decode_device_name(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _property(props: dict[Any, Any], name: str, default: Any = None) -> Any:
    if name in props:
        return props[name]
    encoded = name.encode("utf-8")
    if encoded in props:
        return props[encoded]
    return default


def _validate_cuda_candidate_contract(experiment: dict[str, Any]) -> None:
    if experiment["backend_request"]["name"] != "cpu-reference-v1":
        raise ConfigurationError(
            "Phase 3 CUDA execution consumes the canonical cpu-reference-v1 experiment contract "
            "as a candidate backend comparison; it does not reinterpret backend_request"
        )
    if experiment["precision"] != {"dtype": "float64", "byte_order": "little"}:
        raise ConfigurationError("cuda-single-gpu-v1 supports the Phase 1 float64 precision contract only")
    if experiment["boundary_conditions"] != {"x": "periodic", "y": "periodic"}:
        raise ConfigurationError("cuda-single-gpu-v1 currently supports periodic x/y boundaries only")
    expected = {
        "name": "finite_difference_projection_v1",
        "advection": "centered_second_order",
        "diffusion": "centered_second_order",
        "divergence_gradient_pair": "backward_forward_v1",
    }
    if experiment["discretization"] != expected:
        raise ConfigurationError("cuda-single-gpu-v1 supports finite_difference_projection_v1 only")
    if experiment["time_integration"] != {"name": "forward_euler_projection_v1"}:
        raise ConfigurationError("cuda-single-gpu-v1 supports forward_euler_projection_v1 only")
    if experiment["solver"]["pressure"]["method"] != "jacobi_periodic_v1":
        raise ConfigurationError("cuda-single-gpu-v1 supports jacobi_periodic_v1 only")


def _derivative_centered_x(xp, a, dx: float):
    return (xp.roll(a, -1, axis=1) - xp.roll(a, 1, axis=1)) / (2.0 * dx)


def _derivative_centered_y(xp, a, dy: float):
    return (xp.roll(a, -1, axis=0) - xp.roll(a, 1, axis=0)) / (2.0 * dy)


def _divergence_backward(xp, u, v, dx: float, dy: float):
    return (u - xp.roll(u, 1, axis=1)) / dx + (v - xp.roll(v, 1, axis=0)) / dy


def _gradient_forward(xp, p, dx: float, dy: float):
    return (xp.roll(p, -1, axis=1) - p) / dx, (xp.roll(p, -1, axis=0) - p) / dy


def _laplacian_periodic(xp, a, dx: float, dy: float):
    return (
        (xp.roll(a, -1, axis=1) - 2.0 * a + xp.roll(a, 1, axis=1)) / (dx * dx)
        + (xp.roll(a, -1, axis=0) - 2.0 * a + xp.roll(a, 1, axis=0)) / (dy * dy)
    )


def _solve_pressure_jacobi_array(
    xp,
    rhs,
    dx: float,
    dy: float,
    tolerance: float,
    max_iterations: int,
):
    rhs = xp.asarray(rhs, dtype=xp.float64)
    rhs = rhs - xp.mean(rhs, dtype=xp.float64)
    p = xp.zeros_like(rhs, dtype=xp.float64)
    inv_dx2 = 1.0 / (dx * dx)
    inv_dy2 = 1.0 / (dy * dy)
    denom = 2.0 * inv_dx2 + 2.0 * inv_dy2
    residual = float("inf")

    for iteration in range(1, max_iterations + 1):
        p_new = (
            (xp.roll(p, -1, axis=1) + xp.roll(p, 1, axis=1)) * inv_dx2
            + (xp.roll(p, -1, axis=0) + xp.roll(p, 1, axis=0)) * inv_dy2
            - rhs
        ) / denom
        p_new = p_new - xp.mean(p_new, dtype=xp.float64)
        p = xp.asarray(p_new, dtype=xp.float64)
        residual_field = _laplacian_periodic(xp, p, dx, dy) - rhs
        residual = _scalar(xp.max(xp.abs(residual_field)))
        if residual <= tolerance:
            return p, iteration, residual

    raise NumericalError(
        f"CUDA pressure solve failed to converge: residual={residual:.17g} "
        f"tolerance={tolerance:.17g} iterations={max_iterations}"
    )


def _advance_array_step(
    xp,
    state: DeviceState,
    experiment: dict[str, Any],
) -> tuple[DeviceState, dict[str, float | int]]:
    dx, dy = grid_spacing(experiment)
    rho = experiment["material"]["rho"]
    nu = experiment["material"]["nu"]
    dt = experiment["timestep_policy"]["dt"]
    fx, fy = experiment["forcing"]["canonical_value"]

    u = state.u
    v = state.v
    adv_u = u * _derivative_centered_x(xp, u, dx) + v * _derivative_centered_y(xp, u, dy)
    adv_v = u * _derivative_centered_x(xp, v, dx) + v * _derivative_centered_y(xp, v, dy)
    u_star = u + dt * (-adv_u + nu * _laplacian_periodic(xp, u, dx, dy) + fx)
    v_star = v + dt * (-adv_v + nu * _laplacian_periodic(xp, v, dx, dy) + fy)

    rhs = (rho / dt) * _divergence_backward(xp, u_star, v_star, dx, dy)
    pressure_cfg = experiment["solver"]["pressure"]
    p, iterations, residual = _solve_pressure_jacobi_array(
        xp,
        rhs,
        dx,
        dy,
        pressure_cfg["tolerance"],
        pressure_cfg["max_iterations"],
    )
    grad_px, grad_py = _gradient_forward(xp, p, dx, dy)
    u_new = xp.asarray(u_star - (dt / rho) * grad_px, dtype=xp.float64)
    v_new = xp.asarray(v_star - (dt / rho) * grad_py, dtype=xp.float64)
    return (
        DeviceState(
            u=xp.ascontiguousarray(u_new),
            v=xp.ascontiguousarray(v_new),
            p=xp.ascontiguousarray(p),
            step=state.step + 1,
            time=float(state.time + dt),
        ),
        {"pressure_iterations": iterations, "pressure_residual_linf": residual},
    )


def _compute_array_diagnostics(
    xp,
    state: DeviceState,
    experiment: dict[str, Any],
    pressure_info: dict[str, float | int] | None = None,
) -> dict[str, float | int | bool]:
    dx, dy = grid_spacing(experiment)
    dt = experiment["timestep_policy"]["dt"]
    nu = experiment["material"]["nu"]
    div = _divergence_backward(xp, state.u, state.v, dx, dy)
    vort = _derivative_centered_x(xp, state.v, dx) - _derivative_centered_y(xp, state.u, dy)
    finite = _bool_scalar(xp.isfinite(state.u).all() & xp.isfinite(state.v).all() & xp.isfinite(state.p).all())
    max_u = _scalar(xp.max(xp.abs(state.u)))
    max_v = _scalar(xp.max(xp.abs(state.v)))
    pressure_info = pressure_info or {"pressure_iterations": 0, "pressure_residual_linf": 0.0}
    return {
        "step": state.step,
        "time": float(state.time),
        "finite_state": finite,
        "divergence_linf": _scalar(xp.max(xp.abs(div))),
        "divergence_l2": _scalar(xp.sqrt(xp.mean(div * div, dtype=xp.float64))),
        "kinetic_energy_mean": _scalar(
            0.5 * xp.mean(state.u * state.u + state.v * state.v, dtype=xp.float64)
        ),
        "enstrophy_mean": _scalar(0.5 * xp.mean(vort * vort, dtype=xp.float64)),
        "max_abs_u": max_u,
        "max_abs_v": max_v,
        "advective_cfl": float(dt * (max_u / dx + max_v / dy)),
        "diffusion_number": float(nu * dt * (1.0 / (dx * dx) + 1.0 / (dy * dy))),
        "pressure_iterations": int(pressure_info["pressure_iterations"]),
        "pressure_residual_linf": float(pressure_info["pressure_residual_linf"]),
    }


def _host_state(xp, state: DeviceState) -> State:
    if xp is np:
        to_host = np.asarray
    else:
        to_host = xp.asnumpy
    return State(
        u=np.ascontiguousarray(to_host(state.u), dtype=np.float64),
        v=np.ascontiguousarray(to_host(state.v), dtype=np.float64),
        p=np.ascontiguousarray(to_host(state.p), dtype=np.float64),
        step=state.step,
        time=state.time,
    )


def _run_array_backend(
    experiment: dict[str, Any],
    xp,
    *,
    collect_history: bool = True,
    checkpoint_steps: set[int] | None = None,
    checkpoint_callback: Callable[[State], None] | None = None,
) -> tuple[State, list[dict[str, float | int | bool]]]:
    experiment = normalize_experiment(experiment)
    _validate_cuda_candidate_contract(experiment)
    initial = initialize_state(experiment)
    state = DeviceState(
        u=xp.asarray(initial.u, dtype=xp.float64),
        v=xp.asarray(initial.v, dtype=xp.float64),
        p=xp.asarray(initial.p, dtype=xp.float64),
        step=initial.step,
        time=initial.time,
    )
    history: list[dict[str, float | int | bool]] = []
    checkpoint_steps = set() if checkpoint_steps is None else set(checkpoint_steps)
    if checkpoint_callback is not None and 0 in checkpoint_steps:
        checkpoint_callback(_host_state(xp, state))
    initial_diag = _compute_array_diagnostics(xp, state, experiment)
    enforce_hard_conditions(initial_diag, experiment)
    if collect_history:
        history.append(initial_diag)

    total_steps = experiment["stopping_condition"]["steps"]
    interval = experiment["diagnostics"]["interval"]
    for _ in range(total_steps):
        pre_diag = _compute_array_diagnostics(xp, state, experiment)
        enforce_hard_conditions(pre_diag, experiment)
        state, pressure_info = _advance_array_step(xp, state, experiment)
        post_diag = _compute_array_diagnostics(xp, state, experiment, pressure_info)
        enforce_hard_conditions(post_diag, experiment)
        if collect_history and (state.step % interval == 0 or state.step == total_steps):
            history.append(post_diag)
        if checkpoint_callback is not None and state.step in checkpoint_steps:
            checkpoint_callback(_host_state(xp, state))
    return _host_state(xp, state), history


def _run_cpu_reference_in_memory(
    experiment: dict[str, Any],
    *,
    collect_history: bool = True,
) -> tuple[State, list[dict[str, float | int | bool]]]:
    experiment = normalize_experiment(experiment)
    state = initialize_state(experiment)
    history: list[dict[str, float | int | bool]] = []
    initial_diag = compute_diagnostics(state, experiment)
    enforce_hard_conditions(initial_diag, experiment)
    if collect_history:
        history.append(initial_diag)

    total_steps = experiment["stopping_condition"]["steps"]
    interval = experiment["diagnostics"]["interval"]
    for _ in range(total_steps):
        pre_diag = compute_diagnostics(state, experiment)
        enforce_hard_conditions(pre_diag, experiment)
        state, pressure_info = advance_one_step(state, experiment)
        post_diag = compute_diagnostics(state, experiment, pressure_info)
        enforce_hard_conditions(post_diag, experiment)
        if collect_history and (state.step % interval == 0 or state.step == total_steps):
            history.append(post_diag)
    return state, history


def capture_cuda_provenance(device_id: int = 0, cp=None) -> dict[str, Any]:
    cp = _load_cupy() if cp is None else cp
    count = int(cp.cuda.runtime.getDeviceCount())
    if device_id < 0 or device_id >= count:
        raise ConfigurationError(f"CUDA device {device_id} is outside available range 0..{count - 1}")
    device = cp.cuda.Device(device_id)
    device.use()
    props = cp.cuda.runtime.getDeviceProperties(device_id)
    local_runtime = None
    try:
        local_runtime = cp.cuda.get_local_runtime_version()
    except Exception:
        local_runtime = None
    environment = {
        "backend": CUDA_BACKEND,
        "device_ordinal": int(device_id),
        "gpu_name": _decode_device_name(_property(props, "name", "unknown")),
        "compute_capability": [
            int(_property(props, "major", -1)),
            int(_property(props, "minor", -1)),
        ],
        "total_global_memory_bytes": int(_property(props, "totalGlobalMem", 0)),
        "cuda_driver_version": int(cp.cuda.runtime.driverGetVersion()),
        "cupy_linked_cuda_runtime_version": int(cp.cuda.runtime.runtimeGetVersion()),
        "local_cuda_runtime_version": None if local_runtime is None else int(local_runtime),
        "cupy_version": str(cp.__version__),
        "numpy_version": np.__version__,
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "machine": platform.machine(),
        "byteorder": sys.byteorder,
        "precision_contract": {"dtype": "float64", "byte_order": "little"},
        "single_gpu": True,
        "tf32_or_mixed_precision": False,
    }
    environment["environment_identity"] = identity_hash(environment)
    return environment


def write_cuda_provenance_lock(path: str | Path, device_id: int = 0) -> dict[str, Any]:
    environment = capture_cuda_provenance(device_id)
    document = {
        "schema_version": CUDA_PROVENANCE_LOCK_SCHEMA,
        "environment": environment,
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(document), encoding="utf-8")
    return document


def _load_provenance_lock(path: str | Path) -> dict[str, Any]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if document.get("schema_version") != CUDA_PROVENANCE_LOCK_SCHEMA:
        raise ConfigurationError(f"CUDA provenance lock schema must be {CUDA_PROVENANCE_LOCK_SCHEMA!r}")
    environment = document.get("environment")
    if not isinstance(environment, dict):
        raise ConfigurationError("CUDA provenance lock environment must be an object")
    expected_identity = environment.get("environment_identity")
    if not isinstance(expected_identity, str) or identity_hash(
        {key: value for key, value in environment.items() if key != "environment_identity"}
    ) != expected_identity:
        raise ConfigurationError("CUDA provenance lock environment identity is invalid")
    return document


def enforce_cuda_provenance_lock(
    current: dict[str, Any],
    lock_path: str | Path | None,
) -> dict[str, Any]:
    if lock_path is None:
        return {"required": False, "matched": None, "lock_identity": None}
    lock = _load_provenance_lock(lock_path)
    expected = lock["environment"]
    matched = current == expected
    if not matched:
        raise ConfigurationError(
            "current CUDA GPU/software provenance does not match the pinned provenance lock"
        )
    return {
        "required": True,
        "matched": True,
        "lock_identity": identity_hash(lock),
    }


def execute_cuda_experiment(
    experiment_or_path: dict[str, Any] | str | Path,
    output_dir: str | Path,
    *,
    device_id: int = 0,
    provenance_lock: str | Path | None = None,
) -> dict[str, Any]:
    experiment = (
        normalize_experiment(experiment_or_path)
        if isinstance(experiment_or_path, dict)
        else load_experiment(experiment_or_path)
    )
    _validate_cuda_candidate_contract(experiment)
    output = Path(output_dir)
    _prepare_output(output)
    cp = _load_cupy()
    cp.cuda.Device(device_id).use()
    environment = capture_cuda_provenance(device_id, cp)
    lock_status = enforce_cuda_provenance_lock(environment, provenance_lock)
    experiment_hash = identity_hash(experiment)
    (output / "experiment.normalized.json").write_text(pretty_json(experiment), encoding="utf-8")
    (output / "experiment.identity.json").write_bytes(canonical_json_bytes(experiment) + b"\n")

    initial = initialize_state(experiment)
    initial_again = initialize_state(experiment)
    initial_hash = state_hash(initial, experiment_hash)
    if state_hash(initial_again, experiment_hash) != initial_hash:
        raise ConfigurationError("canonical initialization failed R1 byte-identity check")

    policy = experiment["checkpoint_policy"]
    total_steps = experiment["stopping_condition"]["steps"]
    checkpoint_steps: set[int] = set()
    if policy["include_initial"]:
        checkpoint_steps.add(0)
    checkpoint_steps.update(
        step for step in range(policy["interval"], total_steps + 1, policy["interval"])
    )
    if policy["include_final"]:
        checkpoint_steps.add(total_steps)

    checkpoints: list[dict[str, Any]] = []

    def record_checkpoint(state: State) -> None:
        rel = Path("checkpoints") / f"step-{state.step:08d}.nss"
        digest = write_checkpoint(output / rel, state, experiment_hash)
        checkpoints.append({"step": state.step, "path": rel.as_posix(), "sha256": digest})

    final_state, history = _run_array_backend(
        experiment,
        cp,
        checkpoint_steps=checkpoint_steps,
        checkpoint_callback=record_checkpoint,
    )
    checkpoints.sort(key=lambda item: int(item["step"]))
    final_hash = state_hash(final_state, experiment_hash)
    report = {
        "schema_version": CUDA_RUN_SCHEMA,
        "run_status": "completed",
        "source_revision": source_revision(),
        "experiment_hash": experiment_hash,
        "canonical_reference_backend": "cpu-reference-v1",
        "execution_backend": CUDA_BACKEND,
        "device_ordinal": int(device_id),
        "environment": environment,
        "provenance_lock": lock_status,
        "precision": experiment["precision"],
        "initial_state_hash": initial_hash,
        "final_state_hash": final_hash,
        "checkpoint_hashes": checkpoints,
        "diagnostics": history,
        "reproducibility": {
            "demonstrated": ["R0", "R1"],
            "R2_status": "not_assessed_by_single_execution",
            "R3_status": "not_assessed_by_single_execution",
        },
        "numerical_verification_status": "candidate_backend_run_only",
        "physical_validation_status": "not_claimed",
    }
    report["run_id"] = identity_hash(
        {
            "experiment_hash": experiment_hash,
            "environment_identity": environment["environment_identity"],
            "final_state_hash": final_hash,
            "source_revision": report["source_revision"],
        }
    )
    (output / "cuda-run.json").write_text(pretty_json(report), encoding="utf-8")
    return report


def verify_cuda_repeat(
    experiment_or_path: dict[str, Any] | str | Path,
    output_dir: str | Path,
    *,
    device_id: int = 0,
    provenance_lock: str | Path | None = None,
) -> dict[str, Any]:
    experiment = (
        normalize_experiment(experiment_or_path)
        if isinstance(experiment_or_path, dict)
        else load_experiment(experiment_or_path)
    )
    output = Path(output_dir)
    _prepare_output(output)
    run_a = execute_cuda_experiment(
        experiment,
        output / "run-a",
        device_id=device_id,
        provenance_lock=provenance_lock,
    )
    run_b = execute_cuda_experiment(
        experiment,
        output / "run-b",
        device_id=device_id,
        provenance_lock=provenance_lock,
    )
    comparisons = {
        "experiment_hash": run_a["experiment_hash"] == run_b["experiment_hash"],
        "environment_identity": (
            run_a["environment"]["environment_identity"]
            == run_b["environment"]["environment_identity"]
        ),
        "initial_state_hash": run_a["initial_state_hash"] == run_b["initial_state_hash"],
        "final_state_hash": run_a["final_state_hash"] == run_b["final_state_hash"],
        "checkpoint_hashes": run_a["checkpoint_hashes"] == run_b["checkpoint_hashes"],
        "diagnostics": run_a["diagnostics"] == run_b["diagnostics"],
    }
    bitwise_match = all(comparisons.values())
    report = {
        "schema_version": CUDA_REPEAT_SCHEMA,
        "backend": CUDA_BACKEND,
        "source_revision": source_revision(),
        "experiment_hash": run_a["experiment_hash"],
        "environment_identity": run_a["environment"]["environment_identity"],
        "comparisons": comparisons,
        "bitwise_match": bitwise_match,
        "reproducibility_classification": {
            "R2_status": "demonstrated" if bitwise_match else "not_demonstrated",
            "R3_status": "not_assessed",
        },
        "physical_validation_status": "not_claimed",
    }
    (output / "cuda-repeat-verification.json").write_text(pretty_json(report), encoding="utf-8")
    return report


def load_backend_comparison_contract(path: str | Path) -> dict[str, Any]:
    contract = json.loads(Path(path).read_text(encoding="utf-8"))
    if contract.get("schema_version") != CUDA_COMPARISON_CONTRACT_SCHEMA:
        raise ConfigurationError(
            f"backend comparison contract schema must be {CUDA_COMPARISON_CONTRACT_SCHEMA!r}"
        )
    if contract.get("reference_backend") != "cpu-reference-v1":
        raise ConfigurationError("backend comparison reference must be cpu-reference-v1")
    if contract.get("candidate_backend") != CUDA_BACKEND:
        raise ConfigurationError(f"backend comparison candidate must be {CUDA_BACKEND}")
    if contract.get("precision") != {"dtype": "float64", "byte_order": "little"}:
        raise ConfigurationError("backend comparison contract precision must be float64/little")
    metrics = contract.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        raise ConfigurationError("backend comparison contract metrics must be a non-empty object")
    for name, spec in metrics.items():
        if not isinstance(spec, dict):
            raise ConfigurationError(f"comparison metric {name!r} must be an object")
        for key in ("absolute_tolerance", "relative_tolerance"):
            tolerance = spec.get(key)
            if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
                raise ConfigurationError(f"comparison metric {name!r} {key} must be numeric")
            if not math.isfinite(float(tolerance)) or float(tolerance) < 0.0:
                raise ConfigurationError(
                    f"comparison metric {name!r} {key} must be finite and >= 0"
                )
    return contract


def _final_diagnostic(history: list[dict[str, Any]]) -> dict[str, Any]:
    if not history:
        raise ConfigurationError("backend run produced no diagnostic history")
    return history[-1]


def _state_comparison_metrics(
    cpu_state: State,
    cuda_state: State,
    cpu_history: list[dict[str, Any]],
    cuda_history: list[dict[str, Any]],
) -> dict[str, dict[str, float]]:
    du = np.asarray(cuda_state.u - cpu_state.u, dtype=np.float64)
    dv = np.asarray(cuda_state.v - cpu_state.v, dtype=np.float64)
    dp = np.asarray(cuda_state.p - cpu_state.p, dtype=np.float64)
    cpu_diag = _final_diagnostic(cpu_history)
    cuda_diag = _final_diagnostic(cuda_history)

    def metric(error: float, reference_scale: float) -> dict[str, float]:
        return {
            "absolute_error": float(error),
            "reference_scale": abs(float(reference_scale)),
        }

    cpu_velocity_rms = float(
        np.sqrt(np.mean(cpu_state.u * cpu_state.u + cpu_state.v * cpu_state.v, dtype=np.float64))
    )
    return {
        "u_linf": metric(
            float(np.max(np.abs(du))),
            float(np.max(np.abs(cpu_state.u))),
        ),
        "v_linf": metric(
            float(np.max(np.abs(dv))),
            float(np.max(np.abs(cpu_state.v))),
        ),
        "p_linf": metric(
            float(np.max(np.abs(dp))),
            float(np.max(np.abs(cpu_state.p))),
        ),
        "velocity_l2": metric(
            float(np.sqrt(np.mean(du * du + dv * dv, dtype=np.float64))),
            cpu_velocity_rms,
        ),
        "divergence_linf_abs_diff": metric(
            abs(float(cuda_diag["divergence_linf"]) - float(cpu_diag["divergence_linf"])),
            float(cpu_diag["divergence_linf"]),
        ),
        "kinetic_energy_abs_diff": metric(
            abs(float(cuda_diag["kinetic_energy_mean"]) - float(cpu_diag["kinetic_energy_mean"])),
            float(cpu_diag["kinetic_energy_mean"]),
        ),
        "enstrophy_abs_diff": metric(
            abs(float(cuda_diag["enstrophy_mean"]) - float(cpu_diag["enstrophy_mean"])),
            float(cpu_diag["enstrophy_mean"]),
        ),
        "pressure_residual_linf_abs_diff": metric(
            abs(
                float(cuda_diag["pressure_residual_linf"])
                - float(cpu_diag["pressure_residual_linf"])
            ),
            float(cpu_diag["pressure_residual_linf"]),
        ),
    }


def _assess_comparison_metrics(
    observed: dict[str, dict[str, float]],
    contract: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    assessments: dict[str, Any] = {}
    passed = True
    for name, spec in contract["metrics"].items():
        if name not in observed:
            raise ConfigurationError(f"comparison implementation does not provide required metric {name!r}")
        atol = float(spec["absolute_tolerance"])
        rtol = float(spec["relative_tolerance"])
        error = float(observed[name]["absolute_error"])
        scale = float(observed[name]["reference_scale"])
        threshold = atol + rtol * scale
        metric_passed = (
            math.isfinite(error)
            and math.isfinite(scale)
            and scale >= 0.0
            and error <= threshold
        )
        assessments[name] = {
            "absolute_error": error,
            "reference_scale": scale,
            "absolute_tolerance": atol,
            "relative_tolerance": rtol,
            "effective_threshold": threshold,
            "passed": metric_passed,
        }
        passed = passed and metric_passed
    return passed, assessments


def compare_cpu_cuda(
    experiment_or_path: dict[str, Any] | str | Path,
    comparison_contract_path: str | Path,
    *,
    output_path: str | Path | None = None,
    device_id: int = 0,
    provenance_lock: str | Path | None = None,
) -> dict[str, Any]:
    experiment = (
        normalize_experiment(experiment_or_path)
        if isinstance(experiment_or_path, dict)
        else load_experiment(experiment_or_path)
    )
    _validate_cuda_candidate_contract(experiment)
    contract = load_backend_comparison_contract(comparison_contract_path)
    cp = _load_cupy()
    cp.cuda.Device(device_id).use()
    cuda_environment = capture_cuda_provenance(device_id, cp)
    lock_status = enforce_cuda_provenance_lock(cuda_environment, provenance_lock)
    cpu_environment = environment_provenance()

    cpu_state, cpu_history = _run_cpu_reference_in_memory(experiment)
    cuda_state, cuda_history = _run_array_backend(experiment, cp)
    observed = _state_comparison_metrics(cpu_state, cuda_state, cpu_history, cuda_history)
    passed, assessments = _assess_comparison_metrics(observed, contract)
    experiment_hash = identity_hash(experiment)
    report = {
        "schema_version": CUDA_COMPARISON_SCHEMA,
        "passed": passed,
        "source_revision": source_revision(),
        "experiment_hash": experiment_hash,
        "comparison_contract_identity": identity_hash(contract),
        "comparison_contract": contract,
        "reference_backend": {
            "name": "cpu-reference-v1",
            "environment": cpu_environment,
            "final_state_hash": state_hash(cpu_state, experiment_hash),
            "final_diagnostic": _final_diagnostic(cpu_history),
        },
        "candidate_backend": {
            "name": CUDA_BACKEND,
            "environment": cuda_environment,
            "provenance_lock": lock_status,
            "final_state_hash": state_hash(cuda_state, experiment_hash),
            "final_diagnostic": _final_diagnostic(cuda_history),
        },
        "metrics": assessments,
        "reproducibility_classification": {
            "R2_status": "not_assessed",
            "R3_status": "demonstrated" if passed else "not_demonstrated",
        },
        "numerical_verification_status": (
            "cross_backend_comparison_passed" if passed else "cross_backend_comparison_failed"
        ),
        "physical_validation_status": "not_claimed",
    }
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(pretty_json(report), encoding="utf-8")
    return report


def benchmark_cpu_cuda(
    experiment_or_path: dict[str, Any] | str | Path,
    comparison_contract_path: str | Path,
    *,
    output_path: str | Path | None = None,
    device_id: int = 0,
    provenance_lock: str | Path | None = None,
    warmup: int = 1,
    repeats: int = 5,
) -> dict[str, Any]:
    if warmup < 0 or repeats < 1:
        raise ConfigurationError("benchmark warmup must be >= 0 and repeats must be >= 1")
    experiment = (
        normalize_experiment(experiment_or_path)
        if isinstance(experiment_or_path, dict)
        else load_experiment(experiment_or_path)
    )
    comparison = compare_cpu_cuda(
        experiment,
        comparison_contract_path,
        device_id=device_id,
        provenance_lock=provenance_lock,
    )
    if not comparison["passed"]:
        raise NumericalError(
            "performance benchmark refused because CPU/CUDA numerical comparison did not pass"
        )

    cp = _load_cupy()
    cp.cuda.Device(device_id).use()
    for _ in range(warmup):
        _run_array_backend(experiment, cp, collect_history=False)
        cp.cuda.Stream.null.synchronize()

    cuda_seconds: list[float] = []
    for _ in range(repeats):
        cp.cuda.Stream.null.synchronize()
        start = time.perf_counter()
        _run_array_backend(experiment, cp, collect_history=False)
        cp.cuda.Stream.null.synchronize()
        cuda_seconds.append(time.perf_counter() - start)

    cpu_seconds: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        _run_cpu_reference_in_memory(experiment, collect_history=False)
        cpu_seconds.append(time.perf_counter() - start)

    cpu_median = float(np.median(np.asarray(cpu_seconds, dtype=np.float64)))
    cuda_median = float(np.median(np.asarray(cuda_seconds, dtype=np.float64)))
    report = {
        "schema_version": CUDA_BENCHMARK_SCHEMA,
        "source_revision": source_revision(),
        "experiment_hash": identity_hash(experiment),
        "verification_gate": {
            "required": True,
            "passed": True,
            "comparison_schema": comparison["schema_version"],
            "comparison_contract_identity": comparison["comparison_contract_identity"],
            "R3_status": comparison["reproducibility_classification"]["R3_status"],
        },
        "reference_backend": {
            "name": "cpu-reference-v1",
            "environment": comparison["reference_backend"]["environment"],
            "durations_seconds": cpu_seconds,
            "median_seconds": cpu_median,
        },
        "candidate_backend": {
            "name": CUDA_BACKEND,
            "environment": comparison["candidate_backend"]["environment"],
            "durations_seconds": cuda_seconds,
            "median_seconds": cuda_median,
        },
        "warmup_runs": int(warmup),
        "timed_repeats": int(repeats),
        "observed_speedup_cpu_over_cuda": (
            None if cuda_median == 0.0 else float(cpu_median / cuda_median)
        ),
        "performance_scope": (
            "observed only for this experiment hash, source revision, and recorded environments"
        ),
        "physical_validation_status": "not_claimed",
    }
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(pretty_json(report), encoding="utf-8")
    return report
