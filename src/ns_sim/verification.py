from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .schema import normalize_experiment
from .solver import advance_one_step
from .state import State, grid_spacing, initialize_state

REFERENCE_SCHEMA = "ns-sim-verification-reference/1"


def vector_l2_error(
    u: np.ndarray,
    v: np.ndarray,
    reference_u: np.ndarray,
    reference_v: np.ndarray,
) -> float:
    return float(
        np.sqrt(
            np.mean(
                (np.asarray(u, dtype=np.float64) - np.asarray(reference_u, dtype=np.float64)) ** 2
                + (np.asarray(v, dtype=np.float64) - np.asarray(reference_v, dtype=np.float64)) ** 2,
                dtype=np.float64,
            )
        )
    )


def observed_order(coarse_error: float, fine_error: float, coarse_scale: float, fine_scale: float) -> float:
    values = (coarse_error, fine_error, coarse_scale, fine_scale)
    if not all(math.isfinite(value) and value > 0.0 for value in values):
        raise ValueError("errors and refinement scales must be finite and > 0")
    if coarse_scale <= fine_scale:
        raise ValueError("coarse_scale must be greater than fine_scale")
    return math.log(coarse_error / fine_error) / math.log(coarse_scale / fine_scale)


def _taylor_green_exact(experiment: dict[str, Any], time: float) -> tuple[np.ndarray, np.ndarray]:
    nx = experiment["grid"]["nx"]
    ny = experiment["grid"]["ny"]
    lx = experiment["domain"]["x_length"]
    dx, dy = grid_spacing(experiment)
    x = (np.arange(nx, dtype=np.float64) + 0.5) * dx
    y = (np.arange(ny, dtype=np.float64) + 0.5) * dy
    xx, yy = np.meshgrid(x, y, indexing="xy")
    amplitude = experiment["initial_condition"]["amplitude"]
    mode = experiment["initial_condition"]["mode"]
    k = 2.0 * math.pi * mode / lx
    decay = math.exp(-2.0 * experiment["material"]["nu"] * k * k * time)
    u = amplitude * decay * np.sin(k * xx) * np.cos(k * yy)
    v = -amplitude * decay * np.cos(k * xx) * np.sin(k * yy)
    return np.asarray(u, dtype=np.float64), np.asarray(v, dtype=np.float64)


def _run_taylor_green(base_experiment: dict[str, Any], n: int, dt: float, steps: int) -> State:
    case = copy.deepcopy(base_experiment)
    case["grid"] = {"nx": n, "ny": n, "layout": "cell-centered-uniform"}
    case["timestep_policy"]["dt"] = dt
    case["stopping_condition"]["steps"] = steps
    case["solver"]["pressure"]["max_iterations"] = max(
        5000, int(case["solver"]["pressure"]["max_iterations"])
    )
    experiment = normalize_experiment(case)
    state = initialize_state(experiment)
    for _ in range(steps):
        state, _ = advance_one_step(state, experiment)
    return state


def taylor_green_spatial_refinement(
    base_experiment: dict[str, Any],
    levels: Iterable[dict[str, int | float]],
) -> dict[str, Any]:
    samples: list[dict[str, float | int]] = []
    for level in levels:
        n = int(level["n"])
        dt = float(level["dt"])
        steps = int(level["steps"])
        case = copy.deepcopy(base_experiment)
        case["grid"] = {"nx": n, "ny": n, "layout": "cell-centered-uniform"}
        case["timestep_policy"]["dt"] = dt
        case["stopping_condition"]["steps"] = steps
        experiment = normalize_experiment(case)
        state = _run_taylor_green(base_experiment, n=n, dt=dt, steps=steps)
        exact_u, exact_v = _taylor_green_exact(experiment, state.time)
        dx, dy = grid_spacing(experiment)
        samples.append(
            {
                "n": n,
                "dt": dt,
                "steps": steps,
                "time": state.time,
                "scale": max(dx, dy),
                "velocity_l2_error": vector_l2_error(state.u, state.v, exact_u, exact_v),
            }
        )
    samples.sort(key=lambda item: float(item["scale"]), reverse=True)
    orders = [
        observed_order(
            float(coarse["velocity_l2_error"]),
            float(fine["velocity_l2_error"]),
            float(coarse["scale"]),
            float(fine["scale"]),
        )
        for coarse, fine in zip(samples, samples[1:])
    ]
    return {"kind": "spatial", "samples": samples, "observed_orders": orders}


def taylor_green_temporal_refinement(
    base_experiment: dict[str, Any],
    n: int,
    levels: Iterable[dict[str, int | float]],
    reference_dt: float,
    reference_steps: int,
) -> dict[str, Any]:
    reference = _run_taylor_green(
        base_experiment,
        n=n,
        dt=float(reference_dt),
        steps=int(reference_steps),
    )
    samples: list[dict[str, float | int]] = []
    for level in levels:
        dt = float(level["dt"])
        steps = int(level["steps"])
        candidate = _run_taylor_green(base_experiment, n=n, dt=dt, steps=steps)
        if not math.isclose(candidate.time, reference.time, rel_tol=0.0, abs_tol=1e-15):
            raise ValueError("temporal refinement levels and reference must end at the same time")
        samples.append(
            {
                "n": n,
                "dt": dt,
                "steps": steps,
                "time": candidate.time,
                "scale": dt,
                "velocity_l2_error_to_fine_reference": vector_l2_error(
                    candidate.u, candidate.v, reference.u, reference.v
                ),
            }
        )
    samples.sort(key=lambda item: float(item["dt"]), reverse=True)
    orders = [
        observed_order(
            float(coarse["velocity_l2_error_to_fine_reference"]),
            float(fine["velocity_l2_error_to_fine_reference"]),
            float(coarse["dt"]),
            float(fine["dt"]),
        )
        for coarse, fine in zip(samples, samples[1:])
    ]
    return {
        "kind": "temporal",
        "reference": {"n": n, "dt": reference_dt, "steps": reference_steps, "time": reference.time},
        "samples": samples,
        "observed_orders": orders,
    }


def poiseuille_analytic_profile(
    y: np.ndarray,
    *,
    height: float,
    nu: float,
    acceleration: float,
) -> np.ndarray:
    if not (height > 0.0 and nu > 0.0):
        raise ValueError("height and nu must be > 0")
    y = np.asarray(y, dtype=np.float64)
    return np.asarray((acceleration / (2.0 * nu)) * y * (height - y), dtype=np.float64)


def solve_poiseuille_steady_fd(
    ny: int,
    *,
    height: float = 1.0,
    nu: float = 0.1,
    acceleration: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    if ny < 3:
        raise ValueError("ny must be >= 3")
    if not (height > 0.0 and nu > 0.0):
        raise ValueError("height and nu must be > 0")
    dy = height / (ny - 1)
    interior = ny - 2
    rhs_value = -(acceleration * dy * dy) / nu
    lower = np.ones(interior - 1, dtype=np.float64)
    diagonal = np.full(interior, -2.0, dtype=np.float64)
    upper = np.ones(interior - 1, dtype=np.float64)
    rhs = np.full(interior, rhs_value, dtype=np.float64)

    # Deterministic Thomas solve; avoids backend-dependent dense BLAS for this reference case.
    for index in range(1, interior):
        factor = lower[index - 1] / diagonal[index - 1]
        diagonal[index] -= factor * upper[index - 1]
        rhs[index] -= factor * rhs[index - 1]
    interior_u = np.empty(interior, dtype=np.float64)
    interior_u[-1] = rhs[-1] / diagonal[-1]
    for index in range(interior - 2, -1, -1):
        interior_u[index] = (rhs[index] - upper[index] * interior_u[index + 1]) / diagonal[index]

    y = np.linspace(0.0, height, ny, dtype=np.float64)
    u = np.zeros(ny, dtype=np.float64)
    u[1:-1] = interior_u
    return y, u


def poiseuille_refinement(
    resolutions: Iterable[int],
    *,
    height: float = 1.0,
    nu: float = 0.1,
    acceleration: float = 1.0,
) -> dict[str, Any]:
    analytic_flow_rate = acceleration * height**3 / (12.0 * nu)
    samples: list[dict[str, float | int]] = []
    for ny in resolutions:
        y, u = solve_poiseuille_steady_fd(
            int(ny), height=height, nu=nu, acceleration=acceleration
        )
        exact = poiseuille_analytic_profile(y, height=height, nu=nu, acceleration=acceleration)
        dy = height / (int(ny) - 1)
        numerical_flow_rate = dy * (
            0.5 * u[0] + float(np.sum(u[1:-1], dtype=np.float64)) + 0.5 * u[-1]
        )
        samples.append(
            {
                "ny": int(ny),
                "scale": dy,
                "profile_linf_error": float(np.max(np.abs(u - exact))),
                "wall_slip_linf": float(max(abs(u[0]), abs(u[-1]))),
                "flow_rate": float(numerical_flow_rate),
                "flow_rate_error": abs(float(numerical_flow_rate) - analytic_flow_rate),
            }
        )
    samples.sort(key=lambda item: float(item["scale"]), reverse=True)
    orders = [
        observed_order(
            float(coarse["flow_rate_error"]),
            float(fine["flow_rate_error"]),
            float(coarse["scale"]),
            float(fine["scale"]),
        )
        for coarse, fine in zip(samples, samples[1:])
    ]
    return {
        "kind": "poiseuille_spatial",
        "parameters": {"height": height, "nu": nu, "acceleration": acceleration},
        "analytic_flow_rate": analytic_flow_rate,
        "samples": samples,
        "observed_orders": orders,
    }


def load_reference(path: str | Path) -> dict[str, Any]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if document.get("schema_version") != REFERENCE_SCHEMA:
        raise ValueError(f"reference schema must be {REFERENCE_SCHEMA!r}")
    if not isinstance(document.get("case"), str) or not document["case"]:
        raise ValueError("reference case must be a non-empty string")
    if not isinstance(document.get("source"), dict):
        raise ValueError("reference source must be an object")
    return document


def _profile_error(
    candidate_coordinates: Iterable[float],
    candidate_values: Iterable[float],
    reference_coordinates: Iterable[float],
    reference_values: Iterable[float],
) -> dict[str, float]:
    candidate_x = np.asarray(list(candidate_coordinates), dtype=np.float64)
    candidate_y = np.asarray(list(candidate_values), dtype=np.float64)
    reference_x = np.asarray(list(reference_coordinates), dtype=np.float64)
    reference_y = np.asarray(list(reference_values), dtype=np.float64)
    if candidate_x.ndim != 1 or candidate_y.ndim != 1 or candidate_x.size != candidate_y.size:
        raise ValueError("candidate profile coordinates and values must be equal-length one-dimensional arrays")
    if candidate_x.size < 2 or np.any(np.diff(candidate_x) <= 0.0):
        raise ValueError("candidate profile coordinates must be strictly increasing")
    if reference_x.size != reference_y.size or reference_x.size == 0:
        raise ValueError("reference profile coordinates and values must be equal-length non-empty arrays")
    if reference_x[0] < candidate_x[0] or reference_x[-1] > candidate_x[-1]:
        raise ValueError("candidate profile does not span the complete reference coordinate range")
    interpolated = np.interp(reference_x, candidate_x, candidate_y)
    delta = interpolated - reference_y
    return {
        "linf": float(np.max(np.abs(delta))),
        "rmse": float(np.sqrt(np.mean(delta * delta, dtype=np.float64))),
    }


def evaluate_lid_driven_cavity(candidate: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    if reference.get("case") != "lid-driven-cavity":
        raise ValueError("reference is not a lid-driven-cavity archive")
    if int(candidate.get("reynolds_number", -1)) != int(reference["regime"]["reynolds_number"]):
        raise ValueError("candidate Reynolds number does not match reference")
    u_error = _profile_error(
        candidate["u_centerline"]["coordinate"],
        candidate["u_centerline"]["velocity"],
        reference["profiles"]["u_centerline"]["coordinate"],
        reference["profiles"]["u_centerline"]["velocity"],
    )
    v_error = _profile_error(
        candidate["v_centerline"]["coordinate"],
        candidate["v_centerline"]["velocity"],
        reference["profiles"]["v_centerline"]["coordinate"],
        reference["profiles"]["v_centerline"]["velocity"],
    )
    tolerance = reference["tolerances"]
    passed = (
        u_error["linf"] <= float(tolerance["u_centerline_linf"])
        and v_error["linf"] <= float(tolerance["v_centerline_linf"])
    )
    return {"case": reference["case"], "passed": passed, "u_centerline": u_error, "v_centerline": v_error}


def evaluate_cylinder_wake(candidate: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    if reference.get("case") != "cylinder-wake":
        raise ValueError("reference is not a cylinder-wake archive")
    metrics = reference["metrics"]
    tolerances = reference["tolerances"]
    errors: dict[str, float] = {}
    passed = True
    for name, reference_value in metrics.items():
        if name not in candidate:
            raise ValueError(f"candidate missing cylinder-wake metric {name!r}")
        observed = float(candidate[name])
        if not math.isfinite(observed):
            raise ValueError(f"candidate metric {name!r} must be finite")
        error = abs(observed - float(reference_value))
        errors[name] = error
        passed = passed and error <= float(tolerances[name])
    return {"case": reference["case"], "passed": passed, "absolute_errors": errors}


def assess_taylor_green(report: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    tolerances = reference["tolerances"]
    errors = [float(sample["velocity_l2_error"]) for sample in report["spatial"]["samples"]]
    spatial_monotone = all(fine < coarse for coarse, fine in zip(errors, errors[1:]))
    spatial_order_floor = min(report["spatial"]["observed_orders"])
    temporal_order_floor = min(report["temporal"]["observed_orders"])
    passed = (
        spatial_monotone
        and errors[-1] <= float(tolerances["finest_spatial_velocity_l2_max"])
        and spatial_order_floor >= float(tolerances["spatial_order_min"])
        and temporal_order_floor >= float(tolerances["temporal_order_min"])
    )
    return {
        "case": "taylor-green-vortex",
        "passed": passed,
        "spatial_monotone": spatial_monotone,
        "finest_spatial_velocity_l2_error": errors[-1],
        "spatial_order_floor": spatial_order_floor,
        "temporal_order_floor": temporal_order_floor,
    }


def assess_poiseuille(report: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    tolerances = reference["tolerances"]
    finest = report["samples"][-1]
    order_floor = min(report["observed_orders"])
    passed = (
        float(finest["profile_linf_error"]) <= float(tolerances["profile_linf_max"])
        and float(finest["wall_slip_linf"]) <= float(tolerances["wall_slip_linf_max"])
        and order_floor >= float(tolerances["flow_rate_order_min"])
    )
    return {
        "case": "poiseuille-channel",
        "passed": passed,
        "finest_profile_linf_error": float(finest["profile_linf_error"]),
        "finest_wall_slip_linf": float(finest["wall_slip_linf"]),
        "flow_rate_order_floor": order_floor,
    }


def run_phase2_core_suite(base_experiment: dict[str, Any], reference_directory: str | Path) -> dict[str, Any]:
    reference_directory = Path(reference_directory)
    taylor_reference = load_reference(reference_directory / "taylor-green.json")
    poiseuille_reference = load_reference(reference_directory / "poiseuille.json")
    cavity_reference = load_reference(reference_directory / "lid-driven-cavity-re100.json")
    cylinder_reference = load_reference(reference_directory / "cylinder-wake-re100.json")

    spatial = taylor_green_spatial_refinement(
        base_experiment,
        [
            {"n": 16, "dt": 0.000125, "steps": 8},
            {"n": 24, "dt": 0.000125, "steps": 8},
            {"n": 32, "dt": 0.000125, "steps": 8},
        ],
    )
    temporal = taylor_green_temporal_refinement(
        base_experiment,
        n=16,
        levels=[
            {"dt": 0.001, "steps": 4},
            {"dt": 0.0005, "steps": 8},
            {"dt": 0.00025, "steps": 16},
        ],
        reference_dt=0.0000625,
        reference_steps=64,
    )
    taylor_report = {"spatial": spatial, "temporal": temporal}
    poiseuille_report = poiseuille_refinement([17, 33, 65])

    taylor_assessment = assess_taylor_green(taylor_report, taylor_reference)
    poiseuille_assessment = assess_poiseuille(poiseuille_report, poiseuille_reference)
    return {
        "schema_version": "ns-sim-verification-report/1",
        "suite": "phase2-core",
        "passed": bool(taylor_assessment["passed"] and poiseuille_assessment["passed"]),
        "cases": {
            "taylor_green": {"assessment": taylor_assessment, "report": taylor_report},
            "poiseuille": {"assessment": poiseuille_assessment, "report": poiseuille_report},
            "lid_driven_cavity": {
                "status": "reference_gate_ready",
                "reference_case": cavity_reference["case"],
                "candidate_required": True,
            },
            "cylinder_wake": {
                "status": "reference_gate_ready",
                "reference_case": cylinder_reference["case"],
                "candidate_required": True,
            },
        },
        "validation_status": "not_claimed",
    }
