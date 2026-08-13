import copy

import pytest

from ns_sim.canonical import identity_hash
from ns_sim.errors import ConfigurationError
from ns_sim.schema import normalize_experiment


def test_normalization_is_order_insensitive(example_raw):
    normalized = normalize_experiment(example_raw)
    reversed_raw = dict(reversed(list(example_raw.items())))
    assert identity_hash(normalize_experiment(reversed_raw)) == identity_hash(normalized)


def test_unknown_field_fails_closed(example_raw):
    broken = copy.deepcopy(example_raw)
    broken["mystery"] = 123
    with pytest.raises(ConfigurationError, match="unknown fields"):
        normalize_experiment(broken)


def test_force_density_normalizes_per_unit_mass(example_raw):
    case = copy.deepcopy(example_raw)
    case["material"] = {"rho": 2.0, "nu": 0.01, "units": "SI"}
    case["domain"]["units"] = "m"
    case["forcing"] = {
        "representation": "force_density",
        "units_or_nondimensional_convention": "N/m^3",
        "value": [4.0, -2.0],
    }
    normalized = normalize_experiment(case)
    assert normalized["forcing"]["canonical_value"] == [2.0, -1.0]
    assert normalized["forcing"]["canonical_units"] == "m/s^2"
