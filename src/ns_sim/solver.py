from __future__ import annotations

import numpy as np

from .errors import NumericalError
from .numerics import (
    derivative_centered_x,
    derivative_centered_y,
    divergence_backward,
    gradient_forward,
    laplacian_periodic,
)
from .state import State, grid_spacing


def solve_pressure_jacobi(
    rhs: np.ndarray,
    dx: float,
    dy: float,
    tolerance: float,
    max_iterations: int,
) -> tuple[np.ndarray, int, float]:
    rhs = np.asarray(rhs, dtype=np.float64)
    rhs = rhs - np.mean(rhs, dtype=np.float64)
    p = np.zeros_like(rhs, dtype=np.float64)
    inv_dx2 = 1.0 / (dx * dx)
    inv_dy2 = 1.0 / (dy * dy)
    denom = 2.0 * inv_dx2 + 2.0 * inv_dy2
    residual = float("inf")

    for iteration in range(1, max_iterations + 1):
        p_new = (
            (np.roll(p, -1, axis=1) + np.roll(p, 1, axis=1)) * inv_dx2
            + (np.roll(p, -1, axis=0) + np.roll(p, 1, axis=0)) * inv_dy2
            - rhs
        ) / denom
        p_new -= np.mean(p_new, dtype=np.float64)
        p = np.asarray(p_new, dtype=np.float64)
        residual_field = laplacian_periodic(p, dx, dy) - rhs
        residual = float(np.max(np.abs(residual_field)))
        if residual <= tolerance:
            return p, iteration, residual

    raise NumericalError(
        f"pressure solve failed to converge: residual={residual:.17g} "
        f"tolerance={tolerance:.17g} iterations={max_iterations}"
    )


def advance_one_step(state: State, experiment: dict) -> tuple[State, dict[str, float | int]]:
    dx, dy = grid_spacing(experiment)
    rho = experiment["material"]["rho"]
    nu = experiment["material"]["nu"]
    dt = experiment["timestep_policy"]["dt"]
    fx, fy = experiment["forcing"]["canonical_value"]

    u = state.u
    v = state.v
    adv_u = u * derivative_centered_x(u, dx) + v * derivative_centered_y(u, dy)
    adv_v = u * derivative_centered_x(v, dx) + v * derivative_centered_y(v, dy)
    u_star = u + dt * (-adv_u + nu * laplacian_periodic(u, dx, dy) + fx)
    v_star = v + dt * (-adv_v + nu * laplacian_periodic(v, dx, dy) + fy)

    rhs = (rho / dt) * divergence_backward(u_star, v_star, dx, dy)
    pressure_cfg = experiment["solver"]["pressure"]
    p, iterations, residual = solve_pressure_jacobi(
        rhs,
        dx,
        dy,
        pressure_cfg["tolerance"],
        pressure_cfg["max_iterations"],
    )
    grad_px, grad_py = gradient_forward(p, dx, dy)
    u_new = np.asarray(u_star - (dt / rho) * grad_px, dtype=np.float64)
    v_new = np.asarray(v_star - (dt / rho) * grad_py, dtype=np.float64)

    new_state = State(
        u=np.ascontiguousarray(u_new),
        v=np.ascontiguousarray(v_new),
        p=np.ascontiguousarray(p),
        step=state.step + 1,
        time=float(state.time + dt),
    )
    return new_state, {"pressure_iterations": iterations, "pressure_residual_linf": residual}
