from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .canonical import canonical_json_bytes, identity_hash, pretty_json
from .cuda_backend import (
    benchmark_cpu_cuda,
    compare_cpu_cuda,
    execute_cuda_experiment,
    verify_cuda_repeat,
    write_cuda_provenance_lock,
)
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
    parser = argparse.ArgumentParser(prog="ns-sim", description="NS-SIM deterministic fluid-dynamics runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    normalize = sub.add_parser("normalize", help="validate, normalize, and hash an experiment")
    normalize.add_argument("experiment")
    normalize.add_argument("--identity", action="store_true", help="emit the exact hash identity document")

    run = sub.add_parser("run", help="execute one canonical CPU run")
    run.add_argument("experiment")
    run.add_argument("--output", required=True)

    repeat = sub.add_parser("verify-repeat", help="execute twice and test CPU R2 backend-local byte identity")
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

    provenance = sub.add_parser(
        "cuda-provenance",
        help="capture the exact single-GPU CUDA/CuPy environment as a provenance lock",
    )
    provenance.add_argument("--output", required=True, help="provenance-lock JSON path")
    provenance.add_argument("--device", type=int, default=0, help="CUDA device ordinal")

    run_cuda = sub.add_parser(
        "run-cuda",
        help="execute cuda-single-gpu-v1 against the canonical periodic float64 contract",
    )
    run_cuda.add_argument("experiment")
    run_cuda.add_argument("--output", required=True, help="empty output directory")
    run_cuda.add_argument("--device", type=int, default=0, help="CUDA device ordinal")
    run_cuda.add_argument("--provenance-lock", help="require an exact previously captured CUDA environment")

    cuda_repeat = sub.add_parser(
        "verify-cuda-repeat",
        help="execute the CUDA backend twice and classify backend-local R2 reproducibility",
    )
    cuda_repeat.add_argument("experiment")
    cuda_repeat.add_argument("--output", required=True, help="empty output directory")
    cuda_repeat.add_argument("--device", type=int, default=0, help="CUDA device ordinal")
    cuda_repeat.add_argument("--provenance-lock", help="require an exact previously captured CUDA environment")

    compare = sub.add_parser(
        "compare-backends",
        help="run CPU and CUDA and evaluate the declared R3 numerical comparison contract",
    )
    compare.add_argument("experiment")
    compare.add_argument("--contract", required=True, help="backend-comparison contract JSON")
    compare.add_argument("--output", required=True, help="comparison report JSON path")
    compare.add_argument("--device", type=int, default=0, help="CUDA device ordinal")
    compare.add_argument("--provenance-lock", help="require an exact previously captured CUDA environment")

    performance = sub.add_parser(
        "benchmark-backends",
        help="benchmark CPU versus CUDA only after the R3 comparison gate passes",
    )
    performance.add_argument("experiment")
    performance.add_argument("--contract", required=True, help="backend-comparison contract JSON")
    performance.add_argument("--output", required=True, help="performance report JSON path")
    performance.add_argument("--device", type=int, default=0, help="CUDA device ordinal")
    performance.add_argument("--provenance-lock", help="require an exact previously captured CUDA environment")
    performance.add_argument("--warmup", type=int, default=1, help="CUDA warmup runs")
    performance.add_argument("--repeats", type=int, default=5, help="timed runs for each backend")
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
        if args.command == "cuda-provenance":
            report = write_cuda_provenance_lock(args.output, device_id=args.device)
            print(
                json.dumps(
                    {
                        "provenance_lock": str(args.output),
                        "environment_identity": report["environment"]["environment_identity"],
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "run-cuda":
            report = execute_cuda_experiment(
                args.experiment,
                args.output,
                device_id=args.device,
                provenance_lock=args.provenance_lock,
            )
            print(json.dumps({"run_id": report["run_id"], "report": f"{args.output}/cuda-run.json"}))
            return 0
        if args.command == "verify-cuda-repeat":
            report = verify_cuda_repeat(
                args.experiment,
                args.output,
                device_id=args.device,
                provenance_lock=args.provenance_lock,
            )
            print(json.dumps(report, sort_keys=True))
            return 0 if report["bitwise_match"] else 3
        if args.command == "compare-backends":
            report = compare_cpu_cuda(
                args.experiment,
                args.contract,
                output_path=args.output,
                device_id=args.device,
                provenance_lock=args.provenance_lock,
            )
            sys.stdout.write(pretty_json(report))
            return 0 if report["passed"] else 3
        if args.command == "benchmark-backends":
            report = benchmark_cpu_cuda(
                args.experiment,
                args.contract,
                output_path=args.output,
                device_id=args.device,
                provenance_lock=args.provenance_lock,
                warmup=args.warmup,
                repeats=args.repeats,
            )
            sys.stdout.write(pretty_json(report))
            return 0
    except (NSSimError, OSError, ValueError) as exc:
        print(f"ns-sim: error: {exc}", file=sys.stderr)
        return 2
    return 1
