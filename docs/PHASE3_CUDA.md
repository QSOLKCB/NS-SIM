# Phase 3 CUDA Acceleration

Phase 3 adds a correctness-first single-GPU CUDA candidate backend without changing the Phase 1 canonical scientific contract.

The canonical reference remains `cpu-reference-v1`. `cuda-single-gpu-v1` executes the same supported periodic float64 finite-difference projection contract as an accelerated candidate implementation. Cross-backend agreement is assessed numerically under an explicit comparison contract; it is never assumed from shared equations or visually similar output.

## Supported scope

`cuda-single-gpu-v1` currently supports exactly the Phase 1 periodic contract:

- model `incompressible-navier-stokes-2d` version `1`;
- uniform cell-centered 2D grid;
- periodic x/y boundaries;
- `finite_difference_projection_v1`;
- centered second-order advection and diffusion;
- backward-divergence / forward-gradient projection pair;
- `forward_euler_projection_v1`;
- `jacobi_periodic_v1`;
- float64 computation and canonical host serialization;
- one CUDA device per process.

The experiment continues to declare `backend_request.name = cpu-reference-v1`. This is intentional: Phase 3 treats CUDA as a candidate execution implementation of the frozen canonical contract rather than silently changing the experiment schema. CUDA execution is explicitly declared in the Phase 3 run/comparison artifacts.

Non-periodic walls, immersed/embedded obstacles, FP32/TF32/mixed precision, multi-GPU execution, and alternative solver contracts remain outside this backend version.

## CuPy installation

NS-SIM keeps CUDA optional so CPU-only installations and CI do not acquire a GPU dependency.

For CUDA 12.x:

```bash
python -m pip install -e '.[test,cuda12]'
```

For CUDA 13.x:

```bash
python -m pip install -e '.[test,cuda13]'
```

Install only one CuPy distribution in an environment.

## Single-GPU run

```bash
ns-sim run-cuda examples/phase1-periodic-vortex.json \
  --device 0 \
  --output runs/cuda
```

The run records:

- source revision and whether it is usable as execution provenance;
- normalized experiment identity;
- canonical initial-state identity;
- the CPU initialization environment used to establish R1;
- CUDA final-state identity;
- the experiment-declared checkpoint schedule;
- numerical diagnostics and pressure convergence;
- GPU/software environment provenance;
- explicit R2/R3 status as not assessed by a single run;
- physical validation as `not_claimed`.

The CUDA backend initializes from the canonical CPU-defined float64 initial state, then transfers that state to the selected GPU. The CPU initialization environment identity is retained in the CUDA run artifact because R1 is scoped to canonical CPU initialization, not merely to the later GPU execution environment. Final/checkpoint states are copied back to host and serialized through the existing `ns-sim-state/1` contract.

## Pinned GPU/software provenance

Capture the exact environment before an archival or comparison run:

```bash
ns-sim cuda-provenance \
  --device 0 \
  --output provenance/cuda-device0.json
```

The lock binds the run to the recorded:

- backend identifier and logical device ordinal;
- stable physical GPU UUID;
- PCI bus identity;
- GPU model;
- compute capability;
- total global memory;
- CUDA driver version;
- CUDA runtime linked to CuPy;
- locally detected CUDA runtime when available;
- CuPy and NumPy versions;
- Python implementation/version;
- operating-system/kernel and machine identity;
- byte order;
- float64 precision contract;
- explicit single-GPU/no-mixed-precision declaration.

The stable UUID is required so logical ordinal remapping or multiple identical GPUs cannot satisfy an exact provenance lock merely because model-level properties match. Invalid CUDA ordinals are rejected before device selection so CLI failures remain controlled NS-SIM configuration errors rather than raw CUDA tracebacks.

Require an exact lock match with `--provenance-lock`. A mismatch fails closed instead of quietly producing evidence under a different environment.

## Backend-local reproducibility

```bash
ns-sim verify-cuda-repeat examples/phase1-periodic-vortex.json \
  --device 0 \
  --provenance-lock provenance/cuda-device0.json \
  --output runs/cuda-repeat
```

This executes the CUDA backend twice in the same recorded environment.

`R2` is demonstrated only when the source revision is usable and the experiment identity, CPU initialization environment identity, CUDA environment identity, initial state, final serialized state, checkpoint hashes, and diagnostic history are identical across the two executions. If byte identity holds but the implementation revision is unavailable, the report uses `R2_status: withheld_missing_source_revision` rather than upgrading the evidence classification.

Failure to demonstrate R2 does not automatically mean the numerical result is invalid; it means backend-local bitwise reproducibility has not been established with the required provenance.

## CPU-reference comparison and R3

The versioned comparison contract lives at:

```text
verification/backends/cuda-single-gpu-v1.json
```

Run the comparison:

```bash
ns-sim compare-backends examples/phase1-periodic-vortex.json \
  --device 0 \
  --contract verification/backends/cuda-single-gpu-v1.json \
  --provenance-lock provenance/cuda-device0.json \
  --output runs/cpu-vs-cuda.json
```

The comparison contract is fail-closed. It must declare the complete versioned metric set and its scope must exactly match the normalized experiment's model/version, periodic boundary conditions, discretization, time integration, and pressure solver. A subset of convenient metrics cannot qualify as the Phase 3 R3 gate.

The harness executes both implementations from the same normalized experiment and canonical initialization, then evaluates declared `atol + rtol * reference_scale` tolerances for:

- final `u` L-infinity error;
- final `v` L-infinity error;
- final pressure L-infinity error;
- combined velocity L2 error;
- final divergence difference;
- kinetic-energy difference;
- enstrophy difference;
- pressure-residual difference.

The absolute floor prevents near-zero reference quantities from making the gate ill-conditioned, while the relative term keeps the same contract meaningful across different valid field magnitudes.

The numerical gate and the reproducibility classification are reported separately. `R3_status: demonstrated` requires both a passing complete metric gate and a usable source revision. If the numerical comparison passes but the source revision is unknown, the report retains `numerical_gate_passed: true` but sets `passed: false` and `R3_status: withheld_missing_source_revision`.

A demonstrated R3 result applies only to that experiment hash, comparison-contract identity, source revision, and recorded environments. It does not imply bitwise CPU/GPU identity, cross-GPU bitwise identity, or physical validation.

## Performance benchmark gate

```bash
ns-sim benchmark-backends examples/phase1-periodic-vortex.json \
  --device 0 \
  --contract verification/backends/cuda-single-gpu-v1.json \
  --provenance-lock provenance/cuda-device0.json \
  --warmup 1 \
  --repeats 5 \
  --output runs/cpu-vs-cuda-performance.json
```

Performance measurement is fail-closed behind demonstrated R3 evidence. The benchmark refuses timing publication when the numerical gate fails or when required provenance is incomplete.

Immediately before timing, NS-SIM re-captures the CPU and CUDA environments and requires them to equal the environments that passed the R3 gate. This prevents verification on one device/environment followed by performance measurement on another.

The report records individual timings, medians, the observed CPU/CUDA speed ratio, experiment identity, comparison-contract identity, source revision, and both backend environments. The speed ratio is scoped to those exact conditions and is not a general hardware-performance claim.

## Versioned evidence schemas

Phase 3 emitted artifacts are mechanically schema-validatable:

```text
schemas/cuda-run-v1.schema.json
schemas/cuda-repeat-verification-v1.schema.json
schemas/backend-comparison-report-v1.schema.json
schemas/backend-performance-v1.schema.json
```

The provenance-lock and comparison-contract input schemas remain:

```text
schemas/cuda-provenance-lock-v1.schema.json
schemas/backend-comparison-contract-v1.schema.json
```

CI validates the schemas themselves and validates emulated emitted Phase 3 reports against their matching schema versions. This is artifact-contract evidence only; it does not substitute for execution on real NVIDIA hardware.

## Correctness-first implementation note

The initial CUDA backend mirrors the reference algorithm closely and checks Jacobi pressure residuals during iteration. Those scalar convergence checks synchronize host/device execution and can materially reduce measured GPU speedup, especially on small grids.

That tradeoff is intentional for the first accelerated backend: Phase 3 establishes a transparent, auditable CUDA reference candidate before later kernel fusion or solver optimization. Future performance work may reduce synchronization or fuse operations only when the versioned numerical comparison gates remain satisfied.

## CI and hardware evidence

CPU CI exercises the CUDA numerical kernels through NumPy emulation, complete comparison-contract validation, exact provenance-lock semantics, evidence-schema validation, missing-source-revision classification, invalid-device handling, and lazy CUDA dependency behavior. Ordinary GitHub-hosted CPU CI does not constitute CUDA hardware evidence.

Actual R2, R3, and performance claims for `cuda-single-gpu-v1` require running the corresponding commands on a real NVIDIA GPU with recorded provenance. Such evidence can then be archived alongside a release or research record.

## Validation status

CUDA agreement with the CPU reference is numerical-verification evidence only. It does not establish that the governing equations represent a physical experiment adequately.

`physical_validation_status` remains `not_claimed`.
