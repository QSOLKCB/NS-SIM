import numpy as np

from ns_sim.canonical import identity_hash
from ns_sim.schema import normalize_experiment
from ns_sim.state import deserialize_state, initialize_state, serialize_state, state_hash


def test_state_serialization_round_trip(example_raw):
    exp = normalize_experiment(example_raw)
    exp_hash = identity_hash(exp)
    state = initialize_state(exp)
    payload = serialize_state(state, exp_hash)
    restored, header = deserialize_state(payload)
    assert header["experiment_hash"] == exp_hash
    assert restored.step == 0
    assert restored.time == 0.0
    assert np.array_equal(restored.u, state.u)
    assert np.array_equal(restored.v, state.v)
    assert np.array_equal(restored.p, state.p)


def test_initialization_is_byte_deterministic(example_raw):
    exp = normalize_experiment(example_raw)
    exp_hash = identity_hash(exp)
    assert state_hash(initialize_state(exp), exp_hash) == state_hash(initialize_state(exp), exp_hash)
