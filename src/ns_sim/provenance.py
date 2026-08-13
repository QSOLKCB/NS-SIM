from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np

from .canonical import identity_hash

_STATE_SERIALIZATION_CONTRACT = "ns-sim-state/1"
_RUNTIME_CONTRACT = "ns-sim/0.1.0"


def _cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        try:
            for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.lower().startswith("model name") and ":" in line:
                    return line.split(":", 1)[1].strip()
        except OSError:
            pass
    return platform.processor() or platform.machine() or "unknown"


def _source_checkout_root() -> Path | None:
    source_file = Path(__file__).resolve()
    for parent in source_file.parents:
        candidate = parent / "src" / "ns_sim" / "provenance.py"
        if not (parent / "pyproject.toml").is_file() or not (parent / ".git").exists():
            continue
        try:
            if candidate.resolve() == source_file:
                return parent
        except OSError:
            continue
    return None


def source_revision() -> str:
    override = os.environ.get("NS_SIM_SOURCE_REVISION")
    if override:
        return override
    root = _source_checkout_root()
    if root is None:
        return "unknown"
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
        revision = proc.stdout.strip()
        return revision if revision else "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def environment_provenance() -> dict:
    env = {
        "backend": "cpu-reference-v1",
        "runtime_contract": _RUNTIME_CONTRACT,
        "state_serialization_contract": _STATE_SERIALIZATION_CONTRACT,
        "precision_contract": {"dtype": "float64", "byte_order": "little"},
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "machine": platform.machine(),
        "cpu_model": _cpu_model(),
        "byteorder": sys.byteorder,
        "float64_bits": 64,
    }
    env["environment_identity"] = identity_hash(env)
    return env
