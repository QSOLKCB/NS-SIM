import copy

import numpy as np

from ns_sim.diagnostics import compute_diagnostics
from ns_sim.schema import normalize_experiment
from ns_sim.solver import advance_one_step
from ns_sim.state import initialize_state


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
