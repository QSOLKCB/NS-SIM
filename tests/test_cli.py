from pathlib import Path

from ns_sim.cli import main


def test_normalize_cli(capsys):
    experiment = Path(__file__).parents[1] / "examples" / "phase1-periodic-vortex.json"
    assert main(["normalize", str(experiment)]) == 0
    out = capsys.readouterr().out
    assert "experiment_hash" in out
