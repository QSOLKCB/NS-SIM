import json
from pathlib import Path

from ns_sim.schema import _TOP_LEVEL


def test_experiment_schema_required_fields_match_runtime_contract():
    schema = json.loads((Path(__file__).parents[1] / "schemas" / "experiment-v1.schema.json").read_text())
    assert set(schema["required"]) == _TOP_LEVEL
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == "ns-sim-experiment/1"
    assert schema["properties"]["model"]["properties"]["version"]["const"] == "1"
    assert len(schema["allOf"]) == 2


def test_receipt_schema_requires_reproducibility_evidence():
    schema = json.loads((Path(__file__).parents[1] / "schemas" / "receipt-v1.schema.json").read_text())
    assert schema["properties"]["schema_version"]["const"] == "ns-sim-receipt/1"
    backend = schema["properties"]["backend"]
    assert backend["additionalProperties"] is False
    assert set(backend["required"]) == {"name", "precision", "environment"}
    reproducibility = schema["properties"]["reproducibility"]
    assert reproducibility["additionalProperties"] is False
    assert set(reproducibility["required"]) == {"target", "demonstrated", "R2_status"}
    environment = schema["$defs"]["environment"]
    assert "state_serialization_contract" in environment["required"]
    assert "precision_contract" in environment["required"]
    assert schema["$defs"]["checkpoint"]["additionalProperties"] is False
    assert schema["$defs"]["diagnostic"]["additionalProperties"] is False
