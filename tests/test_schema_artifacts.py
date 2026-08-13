import json
from pathlib import Path

from ns_sim.schema import _TOP_LEVEL


def test_experiment_schema_required_fields_match_runtime_contract():
    schema = json.loads((Path(__file__).parents[1] / "schemas" / "experiment-v1.schema.json").read_text())
    assert set(schema["required"]) == _TOP_LEVEL
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == "ns-sim-experiment/1"


def test_receipt_schema_is_parseable():
    schema = json.loads((Path(__file__).parents[1] / "schemas" / "receipt-v1.schema.json").read_text())
    assert schema["properties"]["schema_version"]["const"] == "ns-sim-receipt/1"
