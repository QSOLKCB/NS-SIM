import copy

import pytest

from ns_sim.canonical import identity_hash
from ns_sim.errors import ConfigurationError
from ns_sim.schema import normalize_experiment


def test_normalization_is_order_insensitive(example_raw):
    normalized = normalize_experiment(example_raw)
    reversed_raw = dict(reversed(list(example_raw.items())))
    assert identity_hash(normalize_experiment(reversed_raw)) == identity_hash(normalized)


def test_normalization_is_idempotent_for_canonical_contract(example_raw):
    normalized = normalize_experiment(example_raw)
    assert normalize_experiment(normalized) == normalized


def test_tampered_normalized_forcing_fails_closed(example_raw):
    normalized = normalize_experiment(example_raw)
    normalized["forcing"]["canonical_value"][0] += 1.0
    with pytest.raises(ConfigurationError, match="canonical normalized form"):
        normalize_experiment(normalized)


def test_unknown_field_fails_closed(example_raw):
    broken = copy.deepcopy(example_raw)
    broken["mystery"] = 123
    with pytest.raises(ConfigurationError, match="unknown fields"):
        normalize_experiment(broken)


def test_model_version_requires_published_string_form(example_raw):
    broken = copy.deepcopy(example_raw)
    broken["model"]["version"] = 1
    with pytest.raises(ConfigurationError, match="supports model"):
        normalize_experiment(broken)


def test_mixed_dimensional_contract_fails_closed(example_raw):
    broken = copy.deepcopy(example_raw)
    broken["domain"]["units"] = "m"
    with pytest.raises(ConfigurationError, match="paired units"):
        normalize_experiment(broken)


def test_numeric_overflow_is_configuration_error(example_raw):
    broken = copy.deepcopy(example_raw)
    broken["material"]["rho"] = 10**400
    with pytest.raises(ConfigurationError, match="binary64"):
        normalize_experiment(broken)


def test_taylor_green_mode_must_be_below_nyquist(example_raw):
    broken = copy.deepcopy(example_raw)
    broken["grid"]["nx"] = 16
    broken["grid"]["ny"] = 16
    broken["initial_condition"]["mode"] = 8
    with pytest.raises(ConfigurationError, match="Nyquist"):
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
