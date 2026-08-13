import json
from pathlib import Path

import pytest


@pytest.fixture
def example_raw():
    path = Path(__file__).parents[1] / "examples" / "phase1-periodic-vortex.json"
    return json.loads(path.read_text(encoding="utf-8"))
