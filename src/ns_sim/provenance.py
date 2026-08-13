from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np

from .canonical import identity_hash


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


def source_revision() -> str:
    override = os.environ.get("NS_SIM_SOURCE_REVISION")
    if override:
        return override
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
        )
        return proc.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def environment_provenance() -> dict:
    env = {
        "backend": "cpu-reference-v1",
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
