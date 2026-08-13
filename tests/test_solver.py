import copy
import math

import numpy as np

from ns_sim.diagnostics import compute_diagnostics
from ns_sim.schema import normalize_experiment
from ns_sim.solver import advance_one_step
from ns_sim.state import State, grid_spacing, initialize_state


def test_zero_flow_remains_zero(example_raw):
    case = copy.deepcopy(example_raw)
    case["initial_condition"] = {"type": "zero"}
    case["stopping_condition"]["steps"] = 1
    exp = normalize_experiment(case)
    state = initialize_state(exp)
    next_state, pressure = advance_one_step(state, exp)
    assert np.array_equal(next_state.u, state.u)
    assert np.array_equal(next_state.v, state.v)
    assert np.array_equal(next_state.p, state.p)
    assert pressure["pressure_residual_linf"] == 0.0


def test_projection_keeps_divergence_small(example_raw):
    exp = normalize_experiment(example_raw)
    state = initialize_state(exp)
    next_state, pressure = advance_one_step(state, exp)
    diag = compute_diagnostics(next_state, exp, pressure)
    assert diag["finite_state"]
    assert diag["divergence_linf"] < 1e-9
    assert pressure["pressure_residual_linf"] <= exp["solver"]["pressure"]["tolerance"]


def test_discrete_shear_wave_matches_forward_euler_diffusion(example_raw):
    case = copy.deepcopy(example_raw)
    case["initial_condition"] = {"type": "zero"}
    case["material"]["nu"] = 0.2
    case["timestep_policy"]["dt"] = 0.001
    case["stopping_condition"]["steps"] = 1
    exp = normalize_experiment(case)
    _, dy = grid_spacing(exp)
    ny, nx = exp["grid"]["ny"], exp["grid"]["nx"]
    y = (np.arange(ny, dtype=np.float64) + 0.5) * dy
    u_line = np.sin(y)
    u = np.repeat(u_line[:, None], nx, axis=1)
    state = State(
        u=np.ascontiguousarray(u),
        v=np.zeros((ny, nx), dtype=np.float64),
        p=np.zeros((ny, nx), dtype=np.float64),
        step=0,
        time=0.0,
    )

    next_state, pressure = advance_one_step(state, exp)
    discrete_eigenvalue = -4.0 * math.sin(0.5 * dy) ** 2 / (dy * dy)
    expected_factor = 1.0 + exp["material"]["nu"] * exp["timestep_policy"]["dt"] * discrete_eigenvalue
    assert np.allclose(next_state.u, expected_factor * state.u, rtol=0.0, atol=1e-14)
    assert np.array_equal(next_state.v, state.v)
    assert pressure["pressure_residual_linf"] == 0.0


def _taylor_green_error(example_raw, n: int, dt: float, steps: int) -> float:
    case = copy.deepcopy(example_raw)
    case["grid"] = {"nx": n, "ny": n, "layout": "cell-centered-uniform"}
    case["timestep_policy"]["dt"] = dt
    case["stopping_condition"]["steps"] = steps
    case["solver"]["pressure"]["max_iterations"] = 5000
    exp = normalize_experiment(case)
    state = initialize_state(exp)
    for _ in range(steps):
        state, _ = advance_one_step(state, exp)

    dx, dy = grid_spacing(exp)
    x = (np.arange(n, dtype=np.float64) + 0.5) * dx
    y = (np.arange(n, dtype=np.float64) + 0.5) * dy
    xx, yy = np.meshgrid(x, y, indexing="xy")
    amplitude = exp["initial_condition"]["amplitude"]
    mode = exp["initial_condition"]["mode"]
    k = 2.0 * math.pi * mode / exp["domain"]["x_length"]
    decay = math.exp(-2.0 * exp["material"]["nu"] * k * k * state.time)
    exact_u = amplitude * decay * np.sin(k * xx) * np.cos(k * yy)
    exact_v = -amplitude * decay * np.cos(k * xx) * np.sin(k * yy)
    return float(np.sqrt(np.mean((state.u - exact_u) ** 2 + (state.v - exact_v) ** 2, dtype=np.float64)))


def test_taylor_green_analytic_error_decreases_under_refinement(example_raw):
    coarse_error = _taylor_green_error(example_raw, n=16, dt=0.0005, steps=2)
    fine_error = _taylor_green_error(example_raw, n=32, dt=0.000125, steps=8)
    assert coarse_error > 0.0
    assert fine_error < 0.6 * coarse_error
