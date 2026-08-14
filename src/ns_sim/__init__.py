"""NS-SIM deterministic fluid-dynamics reference and candidate backends."""

from .cuda_backend import (
    benchmark_cpu_cuda,
    compare_cpu_cuda,
    execute_cuda_experiment,
    verify_cuda_repeat,
    write_cuda_provenance_lock,
)
from .runtime import execute_experiment, verify_repeat
from .schema import load_experiment, normalize_experiment

__all__ = [
    "benchmark_cpu_cuda",
    "compare_cpu_cuda",
    "execute_cuda_experiment",
    "execute_experiment",
    "load_experiment",
    "normalize_experiment",
    "verify_cuda_repeat",
    "verify_repeat",
    "write_cuda_provenance_lock",
]
__version__ = "0.1.0"
