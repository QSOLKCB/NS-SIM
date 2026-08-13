from __future__ import annotations

import math

import numpy as np

from .errors import NumericalError
from .numerics import derivative_centered_x, derivative_centered_y, divergence_backward
from .state import State, grid_spacing


def compute_diagnostics(
    state: State,
    experiment: dict,
    pressure_info: dict[str, float | int] | None = None,
) -> dict[str, float | int | bool]:
    dx, dy = grid_spacing(experiment)
    dt = experiment["timestep_policy"]["dt"]
    nu = experiment["material"]["nu"]
    div = divergence_backward(state.u, state.v, dx, dy)
    vort = derivative_centered_x(state.v, dx) - derivative_centered_y(state.u, dy)
    finite = bool(np.isfinite(state.u).all() and np.isfinite(state.v).all() and np.isfinite(state.p).all())
    max_u = float(np.max(np.abs(state.u)))
    max_v = float(np.max(np.abs(state.v)))
    pressure_info = pressure_info or {"pressure_iterations": 0, "pressure_residual_linf": 0.0}
    return {
        "step": state.step,
        "time": float(state.time),
        "finite_state": finite,
        "divergence_linf": float(np.max(np.abs(div))),
        "divergence_l2": float(np.sqrt(np.mean(div * div, dtype=np.float64))),
        "kinetic_energy_mean": float(0.5 * np.mean(state.u * state.u + state.v * state.v, dtype=np.float64)),
        "enstrophy_mean": float(0.5 * np.mean(vort * vort, dtype=np.float64)),
        "max_abs_u": max_u,
        "max_abs_v": max_v,
        "advective_cfl": float(dt * (max_u / dx + max_v / dy)),
        "diffusion_number": float(nu * dt * (1.0 / (dx * dx) + 1.0 / (dy * dy))),
        "pressure_iterations": int(pressure_info["pressure_iterations"]),
        "pressure_residual_linf": float(pressure_info["pressure_residual_linf"]),
    }


def enforce_hard_conditions(diag: dict, experiment: dict) -> None:
    if not diag["finite_state"]:
        raise NumericalError(f"non-finite canonical state at step {diag['step']}")
    max_cfl = experiment["timestep_policy"]["max_advective_cfl"]
    if diag["advective_cfl"] > max_cfl:
        raise NumericalError(
            f"advective CFL exceeded at step {diag['step']}: "
            f"{diag['advective_cfl']:.17g} > {max_cfl:.17g}"
        )
    max_diff = experiment["timestep_policy"]["max_diffusion_number"]
    if diag["diffusion_number"] > max_diff:
        raise NumericalError(
            f"diffusion number exceeded at step {diag['step']}: "
            f"{diag['diffusion_number']:.17g} > {max_diff:.17g}"
        )
    for key in ("divergence_linf", "kinetic_energy_mean", "enstrophy_mean"):
        if not math.isfinite(float(diag[key])):
            raise NumericalError(f"non-finite diagnostic {key} at step {diag['step']}")
