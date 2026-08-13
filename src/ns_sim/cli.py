from __future__ import annotations

import argparse
import json
import sys

from .canonical import canonical_json_bytes, identity_hash, pretty_json
from .errors import NSSimError
from .runtime import execute_experiment, verify_repeat
from .schema import load_experiment


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
    except NSSimError as exc:
        print(f"ns-sim: error: {exc}", file=sys.stderr)
        return 2
    return 1
