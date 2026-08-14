from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .canonical import identity_hash
from .diagnostics import compute_diagnostics, enforce_hard_conditions
from .provenance import environment_provenance, source_revision
from .schema import normalize_experiment
from .solver import advance_one_step
from .state import State, grid_spacing, initialize_state

REFERENCE_SCHEMA = "ns-sim-verification-reference/1"
REPORT_SCHEMA = "ns-sim-verification-report/1"


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


def _finite_number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{path} must be a finite number")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{path} must be a finite number")
    return out


def _mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object")
    return value


def _sequence(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{path} must be an array")
    return value


def _assert_exact_contract(candidate: Any, reference: Any, path: str) -> None:
    if candidate != reference:
        raise ValueError(f"{path} does not match the archived reference contract")


def _taylor_green_regime(experiment: dict[str, Any]) -> dict[str, Any]:
    return {
        "domain": {
            "x_length": experiment["domain"]["x_length"],
            "y_length": experiment["domain"]["y_length"],
            "units": experiment["domain"]["units"],
        },
        "material": {
            "rho": experiment["material"]["rho"],
            "nu": experiment["material"]["nu"],
            "units": experiment["material"]["units"],
        },
        "initial_condition": {
            "type": experiment["initial_condition"]["type"],
            "amplitude": experiment["initial_condition"].get("amplitude"),
            "mode": experiment["initial_condition"].get("mode"),
        },
        "boundary_conditions": dict(experiment["boundary_conditions"]),
        "forcing": {
            "canonical_representation": experiment["forcing"]["canonical_representation"],
            "canonical_units": experiment["forcing"]["canonical_units"],
            "canonical_value": list(experiment["forcing"]["canonical_value"]),
        },
        "discretization": dict(experiment["discretization"]),
        "time_integration": dict(experiment["time_integration"]),
        "precision": dict(experiment["precision"]),
        "backend_request": dict(experiment["backend_request"]),
    }


def _validate_taylor_green_contract(experiment: dict[str, Any]) -> None:
    initial = experiment["initial_condition"]
    if initial.get("type") != "taylor_green":
        raise ValueError("Taylor-Green verification requires initial_condition.type='taylor_green'")
    if experiment["boundary_conditions"] != {"x": "periodic", "y": "periodic"}:
        raise ValueError("Taylor-Green verification requires periodic x/y boundaries")
    forcing = experiment["forcing"]
    if forcing["canonical_representation"] != "specific_body_force_acceleration":
        raise ValueError("Taylor-Green verification requires canonical specific body-force acceleration")
    if any(float(value) != 0.0 for value in forcing["canonical_value"]):
        raise ValueError("Taylor-Green analytic reference requires zero canonical body force")


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


def _run_taylor_green(
    base_experiment: dict[str, Any],
    n: int,
    dt: float,
    steps: int,
) -> tuple[State, dict[str, Any], list[dict[str, float | int | bool]]]:
    case = copy.deepcopy(base_experiment)
    case["grid"] = {"nx": int(n), "ny": int(n), "layout": "cell-centered-uniform"}
    case["timestep_policy"]["dt"] = float(dt)
    case["stopping_condition"]["steps"] = int(steps)
    case["solver"]["pressure"]["max_iterations"] = max(
        5000, int(case["solver"]["pressure"]["max_iterations"])
    )
    experiment = normalize_experiment(case)
    _validate_taylor_green_contract(experiment)
    state = initialize_state(experiment)
    diagnostics: list[dict[str, float | int | bool]] = []
    for _ in range(int(steps)):
        state, pressure_info = advance_one_step(state, experiment)
        diag = compute_diagnostics(state, experiment, pressure_info)
        enforce_hard_conditions(diag, experiment)
        diagnostics.append(diag)
    return state, experiment, diagnostics


def _common_final_time(levels: list[dict[str, int | float]], path: str) -> float:
    if len(levels) < 2:
        raise ValueError(f"{path} requires at least two refinement levels")
    times: list[float] = []
    for index, level in enumerate(levels):
        dt = _finite_number(level.get("dt"), f"{path}[{index}].dt")
        steps_raw = level.get("steps")
        if isinstance(steps_raw, bool) or not isinstance(steps_raw, int) or steps_raw < 1:
            raise ValueError(f"{path}[{index}].steps must be an integer >= 1")
        if dt <= 0.0:
            raise ValueError(f"{path}[{index}].dt must be > 0")
        times.append(dt * steps_raw)
    target = times[0]
    if not all(math.isclose(value, target, rel_tol=1e-12, abs_tol=1e-15) for value in times[1:]):
        raise ValueError(f"{path} levels must end at a common final time")
    return target


def taylor_green_spatial_refinement(
    base_experiment: dict[str, Any],
    levels: Iterable[dict[str, int | float]],
) -> dict[str, Any]:
    normalized_base = normalize_experiment(base_experiment)
    _validate_taylor_green_contract(normalized_base)
    level_list = [dict(level) for level in levels]
    final_time = _common_final_time(level_list, "spatial refinement")
    samples: list[dict[str, Any]] = []
    for level in level_list:
        n = int(level["n"])
        dt = float(level["dt"])
        steps = int(level["steps"])
        state, experiment, diagnostics = _run_taylor_green(base_experiment, n=n, dt=dt, steps=steps)
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
                "diagnostics": diagnostics,
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
    return {
        "kind": "spatial",
        "regime": _taylor_green_regime(normalized_base),
        "final_time": final_time,
        "samples": samples,
        "observed_orders": orders,
    }


def taylor_green_temporal_refinement(
    base_experiment: dict[str, Any],
    n: int,
    levels: Iterable[dict[str, int | float]],
    reference_dt: float,
    reference_steps: int,
) -> dict[str, Any]:
    normalized_base = normalize_experiment(base_experiment)
    _validate_taylor_green_contract(normalized_base)
    level_list = [dict(level) for level in levels]
    if len(level_list) < 3:
        raise ValueError("temporal refinement requires at least three levels for Richardson order")
    final_time = _common_final_time(level_list, "temporal refinement")
    reference_time = float(reference_dt) * int(reference_steps)
    if not math.isclose(reference_time, final_time, rel_tol=1e-12, abs_tol=1e-15):
        raise ValueError("temporal refinement levels and reference must end at the same time")

    runs: list[tuple[dict[str, Any], State]] = []
    for level in level_list:
        state, _, diagnostics = _run_taylor_green(
            base_experiment, n=int(n), dt=float(level["dt"]), steps=int(level["steps"])
        )
        runs.append(
            (
                {
                    "n": int(n),
                    "dt": float(level["dt"]),
                    "steps": int(level["steps"]),
                    "time": state.time,
                    "scale": float(level["dt"]),
                    "diagnostics": diagnostics,
                },
                state,
            )
        )
    runs.sort(key=lambda item: float(item[0]["dt"]), reverse=True)
    ratios = [
        float(coarse[0]["dt"]) / float(fine[0]["dt"])
        for coarse, fine in zip(runs, runs[1:])
    ]
    if not all(math.isclose(ratio, ratios[0], rel_tol=1e-12, abs_tol=1e-15) for ratio in ratios[1:]):
        raise ValueError("temporal Richardson order requires a constant timestep refinement ratio")

    reference, _, reference_diagnostics = _run_taylor_green(
        base_experiment, n=int(n), dt=float(reference_dt), steps=int(reference_steps)
    )
    if float(reference_dt) >= float(runs[-1][0]["dt"]):
        raise ValueError("temporal reference_dt must be finer than the finest candidate timestep")

    samples: list[dict[str, Any]] = []
    for sample, state in runs:
        sample = dict(sample)
        sample["velocity_l2_error_to_fine_reference"] = vector_l2_error(
            state.u, state.v, reference.u, reference.v
        )
        samples.append(sample)

    successive_differences = [
        {
            "coarse_dt": float(coarse_sample["dt"]),
            "fine_dt": float(fine_sample["dt"]),
            "velocity_l2_difference": vector_l2_error(
                coarse_state.u, coarse_state.v, fine_state.u, fine_state.v
            ),
        }
        for (coarse_sample, coarse_state), (fine_sample, fine_state) in zip(runs, runs[1:])
    ]
    orders = [
        observed_order(
            float(coarse["velocity_l2_difference"]),
            float(fine["velocity_l2_difference"]),
            float(coarse["coarse_dt"]),
            float(fine["coarse_dt"]),
        )
        for coarse, fine in zip(successive_differences, successive_differences[1:])
    ]
    return {
        "kind": "temporal",
        "regime": _taylor_green_regime(normalized_base),
        "final_time": final_time,
        "refinement_ratio": ratios[0],
        "reference": {
            "n": int(n),
            "dt": float(reference_dt),
            "steps": int(reference_steps),
            "time": reference.time,
            "diagnostics": reference_diagnostics,
        },
        "samples": samples,
        "successive_velocity_l2_differences": successive_differences,
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
    forcing_units: str = "nondimensional",
) -> dict[str, Any]:
    if not isinstance(forcing_units, str) or not forcing_units:
        raise ValueError("forcing_units must be a non-empty string")
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
    if len(samples) < 2:
        raise ValueError("Poiseuille refinement requires at least two resolutions")
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
        "parameters": {
            "height": float(height),
            "nu": float(nu),
            "forcing": {
                "representation": "specific_body_force_acceleration",
                "units_or_nondimensional_convention": forcing_units,
                "value": float(acceleration),
            },
        },
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
    if candidate_x.size < 2 or not np.isfinite(candidate_x).all() or not np.isfinite(candidate_y).all():
        raise ValueError("candidate profile coordinates and values must be finite and contain at least two points")
    if np.any(np.diff(candidate_x) <= 0.0):
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


def _candidate_profile(candidate: dict[str, Any], name: str) -> tuple[list[Any], list[Any]]:
    profile = _mapping(candidate.get(name), f"candidate.{name}")
    coordinates = _sequence(profile.get("coordinate"), f"candidate.{name}.coordinate")
    velocity = _sequence(profile.get("velocity"), f"candidate.{name}.velocity")
    return coordinates, velocity


def evaluate_lid_driven_cavity(candidate: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    if reference.get("case") != "lid-driven-cavity":
        raise ValueError("reference is not a lid-driven-cavity archive")
    candidate = _mapping(candidate, "candidate")
    if candidate.get("case") != reference["case"]:
        raise ValueError("candidate case does not match lid-driven-cavity reference")
    candidate_regime = _mapping(candidate.get("regime"), "candidate.regime")
    reference_regime = _mapping(reference.get("regime"), "reference.regime")
    candidate_re = _finite_number(candidate_regime.get("reynolds_number"), "candidate.regime.reynolds_number")
    reference_re = _finite_number(reference_regime.get("reynolds_number"), "reference.regime.reynolds_number")
    if candidate_re != reference_re:
        raise ValueError("candidate Reynolds number does not match reference")
    _assert_exact_contract(candidate_regime, reference_regime, "candidate.regime")

    u_coordinates, u_velocity = _candidate_profile(candidate, "u_centerline")
    v_coordinates, v_velocity = _candidate_profile(candidate, "v_centerline")
    profiles = _mapping(reference.get("profiles"), "reference.profiles")
    u_reference = _mapping(profiles.get("u_centerline"), "reference.profiles.u_centerline")
    v_reference = _mapping(profiles.get("v_centerline"), "reference.profiles.v_centerline")
    u_error = _profile_error(
        u_coordinates,
        u_velocity,
        _sequence(u_reference.get("coordinate"), "reference.profiles.u_centerline.coordinate"),
        _sequence(u_reference.get("velocity"), "reference.profiles.u_centerline.velocity"),
    )
    v_error = _profile_error(
        v_coordinates,
        v_velocity,
        _sequence(v_reference.get("coordinate"), "reference.profiles.v_centerline.coordinate"),
        _sequence(v_reference.get("velocity"), "reference.profiles.v_centerline.velocity"),
    )
    tolerance = _mapping(reference.get("tolerances"), "reference.tolerances")
    passed = (
        u_error["linf"] <= _finite_number(tolerance.get("u_centerline_linf"), "reference.tolerances.u_centerline_linf")
        and v_error["linf"] <= _finite_number(tolerance.get("v_centerline_linf"), "reference.tolerances.v_centerline_linf")
    )
    return {
        "case": reference["case"],
        "passed": passed,
        "candidate_identity": identity_hash(candidate),
        "reference_identity": identity_hash(reference),
        "regime": candidate_regime,
        "u_centerline": u_error,
        "v_centerline": v_error,
    }


def evaluate_cylinder_wake(candidate: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    if reference.get("case") != "cylinder-wake":
        raise ValueError("reference is not a cylinder-wake archive")
    candidate = _mapping(candidate, "candidate")
    if candidate.get("case") != reference["case"]:
        raise ValueError("candidate case does not match cylinder-wake reference")
    candidate_regime = _mapping(candidate.get("regime"), "candidate.regime")
    reference_regime = _mapping(reference.get("regime"), "reference.regime")
    _finite_number(candidate_regime.get("reynolds_number"), "candidate.regime.reynolds_number")
    _finite_number(reference_regime.get("reynolds_number"), "reference.regime.reynolds_number")
    _assert_exact_contract(candidate_regime, reference_regime, "candidate.regime")

    candidate_definitions = _mapping(candidate.get("observable_definitions"), "candidate.observable_definitions")
    reference_definitions = _mapping(reference.get("observable_definitions"), "reference.observable_definitions")
    _assert_exact_contract(
        candidate_definitions,
        reference_definitions,
        "candidate.observable_definitions",
    )
    candidate_metrics = _mapping(candidate.get("metrics"), "candidate.metrics")
    metrics = _mapping(reference.get("metrics"), "reference.metrics")
    tolerances = _mapping(reference.get("tolerances"), "reference.tolerances")
    errors: dict[str, float] = {}
    passed = True
    for name, reference_value in metrics.items():
        if name not in candidate_metrics:
            raise ValueError(f"candidate missing cylinder-wake metric {name!r}")
        observed = _finite_number(candidate_metrics[name], f"candidate.metrics.{name}")
        error = abs(observed - _finite_number(reference_value, f"reference.metrics.{name}"))
        errors[name] = error
        passed = passed and error <= _finite_number(tolerances.get(name), f"reference.tolerances.{name}")
    return {
        "case": reference["case"],
        "passed": passed,
        "candidate_identity": identity_hash(candidate),
        "reference_identity": identity_hash(reference),
        "regime": candidate_regime,
        "observable_definitions": candidate_definitions,
        "absolute_errors": errors,
    }


def assess_taylor_green(report: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    if reference.get("case") != "taylor-green-vortex":
        raise ValueError("reference is not a Taylor-Green archive")
    _assert_exact_contract(report.get("regime"), reference.get("regime"), "Taylor-Green regime")
    _assert_exact_contract(report.get("study"), reference.get("study"), "Taylor-Green study")
    tolerances = _mapping(reference.get("tolerances"), "reference.tolerances")
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
        "reference_identity": identity_hash(reference),
        "spatial_monotone": spatial_monotone,
        "finest_spatial_velocity_l2_error": errors[-1],
        "spatial_order_floor": spatial_order_floor,
        "temporal_order_floor": temporal_order_floor,
    }


def assess_poiseuille(report: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    if reference.get("case") != "poiseuille-channel":
        raise ValueError("reference is not a Poiseuille archive")
    _assert_exact_contract(report.get("parameters"), reference.get("regime"), "Poiseuille regime")
    resolutions = [int(sample["ny"]) for sample in report["samples"]]
    _assert_exact_contract(resolutions, reference.get("study", {}).get("resolutions"), "Poiseuille resolutions")
    tolerances = _mapping(reference.get("tolerances"), "reference.tolerances")
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
        "reference_identity": identity_hash(reference),
        "finest_profile_linf_error": float(finest["profile_linf_error"]),
        "finest_wall_slip_linf": float(finest["wall_slip_linf"]),
        "flow_rate_order_floor": order_floor,
    }


def run_phase2_core_suite(base_experiment: dict[str, Any], reference_directory: str | Path) -> dict[str, Any]:
    reference_directory = Path(reference_directory)
    reference_paths = {
        "taylor_green": reference_directory / "taylor-green.json",
        "poiseuille": reference_directory / "poiseuille.json",
        "lid_driven_cavity": reference_directory / "lid-driven-cavity-re100.json",
        "cylinder_wake": reference_directory / "cylinder-wake-re100.json",
    }
    references = {name: load_reference(path) for name, path in reference_paths.items()}
    taylor_reference = references["taylor_green"]
    poiseuille_reference = references["poiseuille"]
    normalized_base = normalize_experiment(base_experiment)
    _validate_taylor_green_contract(normalized_base)
    _assert_exact_contract(
        _taylor_green_regime(normalized_base),
        taylor_reference.get("regime"),
        "base Taylor-Green regime",
    )

    taylor_study = _mapping(taylor_reference.get("study"), "Taylor-Green reference.study")
    spatial_levels = _sequence(taylor_study.get("spatial_levels"), "Taylor-Green study.spatial_levels")
    temporal_spec = _mapping(taylor_study.get("temporal"), "Taylor-Green study.temporal")
    temporal_levels = _sequence(temporal_spec.get("levels"), "Taylor-Green study.temporal.levels")
    spatial = taylor_green_spatial_refinement(normalized_base, spatial_levels)
    temporal = taylor_green_temporal_refinement(
        normalized_base,
        n=int(temporal_spec["n"]),
        levels=temporal_levels,
        reference_dt=float(temporal_spec["reference_dt"]),
        reference_steps=int(temporal_spec["reference_steps"]),
    )
    taylor_report = {
        "regime": _taylor_green_regime(normalized_base),
        "study": taylor_study,
        "spatial": spatial,
        "temporal": temporal,
    }

    poiseuille_regime = _mapping(poiseuille_reference.get("regime"), "Poiseuille reference.regime")
    forcing = _mapping(poiseuille_regime.get("forcing"), "Poiseuille reference.regime.forcing")
    if forcing.get("representation") != "specific_body_force_acceleration":
        raise ValueError("Poiseuille reference forcing must be specific_body_force_acceleration")
    poiseuille_study = _mapping(poiseuille_reference.get("study"), "Poiseuille reference.study")
    poiseuille_report = poiseuille_refinement(
        _sequence(poiseuille_study.get("resolutions"), "Poiseuille study.resolutions"),
        height=float(poiseuille_regime["height"]),
        nu=float(poiseuille_regime["nu"]),
        acceleration=float(forcing["value"]),
        forcing_units=str(forcing["units_or_nondimensional_convention"]),
    )

    taylor_assessment = assess_taylor_green(taylor_report, taylor_reference)
    poiseuille_assessment = assess_poiseuille(poiseuille_report, poiseuille_reference)
    environment = environment_provenance()
    reference_identities = {
        name: {
            "path": str(reference_paths[name]),
            "identity": identity_hash(reference),
        }
        for name, reference in references.items()
    }
    return {
        "schema_version": REPORT_SCHEMA,
        "suite": "phase2-core",
        "passed": bool(taylor_assessment["passed"] and poiseuille_assessment["passed"]),
        "provenance": {
            "source_revision": source_revision(),
            "normalized_experiment_identity": identity_hash(normalized_base),
            "backend": normalized_base["backend_request"]["name"],
            "precision": normalized_base["precision"],
            "environment": environment,
            "reference_identities": reference_identities,
        },
        "cases": {
            "taylor_green": {"assessment": taylor_assessment, "report": taylor_report},
            "poiseuille": {"assessment": poiseuille_assessment, "report": poiseuille_report},
            "lid_driven_cavity": {
                "status": "reference_gate_ready",
                "reference_case": references["lid_driven_cavity"]["case"],
                "reference_identity": reference_identities["lid_driven_cavity"]["identity"],
                "candidate_required": True,
            },
            "cylinder_wake": {
                "status": "reference_gate_ready",
                "reference_case": references["cylinder_wake"]["case"],
                "reference_identity": reference_identities["cylinder_wake"]["identity"],
                "candidate_required": True,
            },
        },
        "validation_status": "not_claimed",
    }
