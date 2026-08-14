from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .canonical import canonical_json_bytes, identity_hash, pretty_json
from .errors import NSSimError
from .runtime import execute_experiment, verify_repeat
from .schema import load_experiment
from .verification import (
    evaluate_cylinder_wake,
    evaluate_lid_driven_cavity,
    load_reference,
    run_phase2_core_suite,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ns-sim", description="NS-SIM canonical CPU reference runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    normalize = sub.add_parser("normalize", help="validate, normalize, and hash an experiment")
    normalize.add_argument("experiment")
    normalize.add_argument("--identity", action="store_true", help="emit the exact hash identity document")

    run = sub.add_parser("run", help="execute one canonical CPU run")
    run.add_argument("experiment")
    run.add_argument("--output", required=True)

    repeat = sub.add_parser("verify-repeat", help="execute twice and test R2 backend-local byte identity")
    repeat.add_argument("experiment")
    repeat.add_argument("--output", required=True)

    phase2 = sub.add_parser("verify-phase2", help="run the executable Phase 2 numerical-verification core")
    phase2.add_argument("experiment", help="Taylor-Green-compatible canonical experiment used as the base contract")
    phase2.add_argument(
        "--references",
        required=True,
        help="archived reference directory (required; no cwd-dependent implicit default)",
    )
    phase2.add_argument("--output", help="optional JSON report path")

    benchmark = sub.add_parser(
        "verify-benchmark",
        help="compare a non-periodic benchmark candidate to an archived reference",
    )
    benchmark.add_argument("candidate", help="candidate JSON containing benchmark contract and observables")
    benchmark.add_argument("reference", help="archived reference JSON")
    benchmark.add_argument("--output", help="optional JSON assessment path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "normalize":
            exp = load_experiment(args.experiment)
            if args.identity:
                sys.stdout.buffer.write(canonical_json_bytes(exp) + b"\n")
            else:
                sys.stdout.write(pretty_json({"experiment_hash": identity_hash(exp), "experiment": exp}))
            return 0
        if args.command == "run":
            receipt = execute_experiment(args.experiment, args.output)
            print(json.dumps({"run_id": receipt["run_id"], "receipt": f"{args.output}/receipt.json"}))
            return 0
        if args.command == "verify-repeat":
            report = verify_repeat(args.experiment, args.output)
            print(json.dumps(report, sort_keys=True))
            return 0
        if args.command == "verify-phase2":
            experiment = load_experiment(args.experiment)
            report = run_phase2_core_suite(experiment, args.references)
            rendered = json.dumps(report, sort_keys=True, indent=2) + "\n"
            if args.output:
                output = Path(args.output)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(rendered, encoding="utf-8")
            sys.stdout.write(rendered)
            return 0 if report["passed"] else 3
        if args.command == "verify-benchmark":
            candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
            if not isinstance(candidate, dict):
                raise ValueError("benchmark candidate must be a JSON object")
            reference = load_reference(args.reference)
            if reference["case"] == "lid-driven-cavity":
                report = evaluate_lid_driven_cavity(candidate, reference)
            elif reference["case"] == "cylinder-wake":
                report = evaluate_cylinder_wake(candidate, reference)
            else:
                raise ValueError(f"verify-benchmark does not support reference case {reference['case']!r}")
            rendered = json.dumps(report, sort_keys=True, indent=2) + "\n"
            if args.output:
                output = Path(args.output)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(rendered, encoding="utf-8")
            sys.stdout.write(rendered)
            return 0 if report["passed"] else 3
    except (NSSimError, OSError, ValueError) as exc:
        print(f"ns-sim: error: {exc}", file=sys.stderr)
        return 2
    return 1
