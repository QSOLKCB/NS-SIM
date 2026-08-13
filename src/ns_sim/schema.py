from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .errors import ConfigurationError

SCHEMA_VERSION = "ns-sim-experiment/1"
MODEL_NAME = "incompressible-navier-stokes-2d"
MODEL_VERSION = "1"
BACKEND_NAME = "cpu-reference-v1"

_TOP_LEVEL = {
    "schema_version",
    "experiment_name",
    "model",
    "domain",
    "grid",
    "material",
    "initial_condition",
    "boundary_conditions",
    "forcing",
    "discretization",
    "time_integration",
    "timestep_policy",
    "solver",
    "precision",
    "stopping_condition",
    "diagnostics",
    "checkpoint_policy",
    "backend_request",
    "reproducibility_policy",
}


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{path} must be an object")
    return value


def _strict(obj: dict[str, Any], allowed: set[str], path: str, required: set[str] | None = None) -> None:
    required = allowed if required is None else required
    missing = required - set(obj)
    unknown = set(obj) - allowed
    if missing:
        raise ConfigurationError(f"{path} missing required fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ConfigurationError(f"{path} contains unknown fields: {', '.join(sorted(unknown))}")


def _number(value: Any, path: str, *, minimum: float | None = None, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(f"{path} must be a finite number")
    out = float(value)
    if not math.isfinite(out):
        raise ConfigurationError(f"{path} must be finite")
    if positive and out <= 0.0:
        raise ConfigurationError(f"{path} must be > 0")
    if minimum is not None and out < minimum:
        raise ConfigurationError(f"{path} must be >= {minimum}")
    return out


def _integer(value: Any, path: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigurationError(f"{path} must be an integer")
    if value < minimum:
        raise ConfigurationError(f"{path} must be >= {minimum}")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{path} must be a non-empty string")
    return value


def _bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigurationError(f"{path} must be boolean")
    return value


def _vector2(value: Any, path: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 2:
        raise ConfigurationError(f"{path} must be a two-element array")
    return [_number(value[0], f"{path}[0]"), _number(value[1], f"{path}[1]")]


def load_experiment(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if path.suffix.lower() != ".json":
        raise ConfigurationError("Phase 1 accepts JSON experiment files only")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"cannot read experiment {path}: {exc}") from exc
    return normalize_experiment(raw)


def normalize_experiment(raw: dict[str, Any]) -> dict[str, Any]:
    top = _object(raw, "experiment")
    _strict(top, _TOP_LEVEL, "experiment")
    if top["schema_version"] != SCHEMA_VERSION:
        raise ConfigurationError(f"schema_version must be {SCHEMA_VERSION!r}")

    model = _object(top["model"], "model")
    _strict(model, {"name", "version"}, "model")
    if model["name"] != MODEL_NAME or str(model["version"]) != MODEL_VERSION:
        raise ConfigurationError(f"Phase 1 supports model {MODEL_NAME!r} version {MODEL_VERSION!r} only")

    domain = _object(top["domain"], "domain")
    _strict(domain, {"x_length", "y_length", "units"}, "domain")
    domain_units = domain["units"]
    if domain_units not in {"nondimensional", "m"}:
        raise ConfigurationError("domain.units must be 'nondimensional' or 'm'")
    x_length = _number(domain["x_length"], "domain.x_length", positive=True)
    y_length = _number(domain["y_length"], "domain.y_length", positive=True)

    grid = _object(top["grid"], "grid")
    _strict(grid, {"nx", "ny", "layout"}, "grid")
    if grid["layout"] != "cell-centered-uniform":
        raise ConfigurationError("grid.layout must be 'cell-centered-uniform'")
    nx = _integer(grid["nx"], "grid.nx", minimum=8)
    ny = _integer(grid["ny"], "grid.ny", minimum=8)

    material = _object(top["material"], "material")
    _strict(material, {"rho", "nu", "units"}, "material")
    if material["units"] not in {"nondimensional", "SI"}:
        raise ConfigurationError("material.units must be 'nondimensional' or 'SI'")
    rho = _number(material["rho"], "material.rho", positive=True)
    nu = _number(material["nu"], "material.nu", minimum=0.0)

    initial = _object(top["initial_condition"], "initial_condition")
    initial_type = initial.get("type")
    if initial_type == "zero":
        _strict(initial, {"type"}, "initial_condition")
        normalized_initial = {"type": "zero"}
    elif initial_type == "taylor_green":
        _strict(initial, {"type", "amplitude", "mode"}, "initial_condition")
        if not math.isclose(x_length, y_length, rel_tol=0.0, abs_tol=0.0):
            raise ConfigurationError("taylor_green initialization requires a square domain in Phase 1")
        normalized_initial = {
            "type": "taylor_green",
            "amplitude": _number(initial["amplitude"], "initial_condition.amplitude", minimum=0.0),
            "mode": _integer(initial["mode"], "initial_condition.mode", minimum=1),
        }
    else:
        raise ConfigurationError("initial_condition.type must be 'zero' or 'taylor_green'")

    boundary = _object(top["boundary_conditions"], "boundary_conditions")
    _strict(boundary, {"x", "y"}, "boundary_conditions")
    if boundary["x"] != "periodic" or boundary["y"] != "periodic":
        raise ConfigurationError("Phase 1 canonical backend supports periodic x/y boundaries only")

    forcing = _object(top["forcing"], "forcing")
    _strict(forcing, {"representation", "units_or_nondimensional_convention", "value"}, "forcing")
    representation = forcing["representation"]
    units = forcing["units_or_nondimensional_convention"]
    input_value = _vector2(forcing["value"], "forcing.value")
    if material["units"] == "nondimensional":
        if units != "nondimensional":
            raise ConfigurationError("nondimensional material requires nondimensional forcing")
    elif representation == "specific_body_force_acceleration" and units != "m/s^2":
        raise ConfigurationError("SI specific body-force acceleration must use 'm/s^2'")
    elif representation == "force_density" and units != "N/m^3":
        raise ConfigurationError("SI force density must use 'N/m^3'")
    if representation == "specific_body_force_acceleration":
        canonical_value = input_value
        canonical_units = "nondimensional" if material["units"] == "nondimensional" else "m/s^2"
    elif representation == "force_density":
        canonical_value = [input_value[0] / rho, input_value[1] / rho]
        canonical_units = "nondimensional" if material["units"] == "nondimensional" else "m/s^2"
    else:
        raise ConfigurationError(
            "forcing.representation must be 'specific_body_force_acceleration' or 'force_density'"
        )

    discretization = _object(top["discretization"], "discretization")
    _strict(
        discretization,
        {"name", "advection", "diffusion", "divergence_gradient_pair"},
        "discretization",
    )
    expected_discretization = {
        "name": "finite_difference_projection_v1",
        "advection": "centered_second_order",
        "diffusion": "centered_second_order",
        "divergence_gradient_pair": "backward_forward_v1",
    }
    if discretization != expected_discretization:
        raise ConfigurationError(f"Phase 1 discretization must equal {expected_discretization!r}")

    time_integration = _object(top["time_integration"], "time_integration")
    _strict(time_integration, {"name"}, "time_integration")
    if time_integration["name"] != "forward_euler_projection_v1":
        raise ConfigurationError("time_integration.name must be 'forward_euler_projection_v1'")

    timestep = _object(top["timestep_policy"], "timestep_policy")
    _strict(timestep, {"type", "dt", "max_advective_cfl", "max_diffusion_number"}, "timestep_policy")
    if timestep["type"] != "fixed":
        raise ConfigurationError("Phase 1 timestep_policy.type must be 'fixed'")
    dt = _number(timestep["dt"], "timestep_policy.dt", positive=True)
    max_cfl = _number(timestep["max_advective_cfl"], "timestep_policy.max_advective_cfl", positive=True)
    max_diff = _number(
        timestep["max_diffusion_number"], "timestep_policy.max_diffusion_number", positive=True
    )

    solver = _object(top["solver"], "solver")
    _strict(solver, {"pressure"}, "solver")
    pressure = _object(solver["pressure"], "solver.pressure")
    _strict(pressure, {"method", "tolerance", "max_iterations"}, "solver.pressure")
    if pressure["method"] != "jacobi_periodic_v1":
        raise ConfigurationError("solver.pressure.method must be 'jacobi_periodic_v1'")
    pressure_tolerance = _number(pressure["tolerance"], "solver.pressure.tolerance", positive=True)
    pressure_max_iterations = _integer(pressure["max_iterations"], "solver.pressure.max_iterations", minimum=1)

    precision = _object(top["precision"], "precision")
    _strict(precision, {"dtype", "byte_order"}, "precision")
    if precision != {"dtype": "float64", "byte_order": "little"}:
        raise ConfigurationError("Phase 1 precision must be float64/little-endian")

    stopping = _object(top["stopping_condition"], "stopping_condition")
    _strict(stopping, {"steps"}, "stopping_condition")
    steps = _integer(stopping["steps"], "stopping_condition.steps", minimum=1)

    diagnostics = _object(top["diagnostics"], "diagnostics")
    _strict(diagnostics, {"interval"}, "diagnostics")
    diagnostic_interval = _integer(diagnostics["interval"], "diagnostics.interval", minimum=1)

    checkpoint = _object(top["checkpoint_policy"], "checkpoint_policy")
    _strict(checkpoint, {"interval", "include_initial", "include_final"}, "checkpoint_policy")
    checkpoint_interval = _integer(checkpoint["interval"], "checkpoint_policy.interval", minimum=1)
    include_initial = _bool(checkpoint["include_initial"], "checkpoint_policy.include_initial")
    include_final = _bool(checkpoint["include_final"], "checkpoint_policy.include_final")

    backend = _object(top["backend_request"], "backend_request")
    _strict(backend, {"name"}, "backend_request")
    if backend["name"] != BACKEND_NAME:
        raise ConfigurationError(f"Phase 1 backend_request.name must be {BACKEND_NAME!r}")

    reproducibility = _object(top["reproducibility_policy"], "reproducibility_policy")
    _strict(reproducibility, {"target"}, "reproducibility_policy")
    if reproducibility["target"] not in {"R1", "R2"}:
        raise ConfigurationError("reproducibility_policy.target must be 'R1' or 'R2'")

    return {
        "schema_version": SCHEMA_VERSION,
        "experiment_name": _string(top["experiment_name"], "experiment_name"),
        "model": {"name": MODEL_NAME, "version": MODEL_VERSION},
        "domain": {"x_length": x_length, "y_length": y_length, "units": domain_units},
        "grid": {"nx": nx, "ny": ny, "layout": "cell-centered-uniform"},
        "material": {"rho": rho, "nu": nu, "units": material["units"]},
        "initial_condition": normalized_initial,
        "boundary_conditions": {"x": "periodic", "y": "periodic"},
        "forcing": {
            "input_representation": representation,
            "input_units": units,
            "input_value": input_value,
            "canonical_representation": "specific_body_force_acceleration",
            "canonical_units": canonical_units,
            "canonical_value": canonical_value,
        },
        "discretization": expected_discretization,
        "time_integration": {"name": "forward_euler_projection_v1"},
        "timestep_policy": {
            "type": "fixed",
            "dt": dt,
            "max_advective_cfl": max_cfl,
            "max_diffusion_number": max_diff,
        },
        "solver": {
            "pressure": {
                "method": "jacobi_periodic_v1",
                "tolerance": pressure_tolerance,
                "max_iterations": pressure_max_iterations,
            }
        },
        "precision": {"dtype": "float64", "byte_order": "little"},
        "stopping_condition": {"steps": steps},
        "diagnostics": {"interval": diagnostic_interval},
        "checkpoint_policy": {
            "interval": checkpoint_interval,
            "include_initial": include_initial,
            "include_final": include_final,
        },
        "backend_request": {"name": BACKEND_NAME},
        "reproducibility_policy": {"target": reproducibility["target"]},
    }
