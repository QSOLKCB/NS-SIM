# NS-SIM

**Deterministic, reproducible fluid-dynamics simulation runtime for Navier–Stokes research, numerical verification, physical validation, GPU acceleration, visualization, and sonification.**

> Status: private pre-alpha research project. Phase 1 implements the canonical periodic 2D CPU reference runtime. Phase 2 implements the analytic/refinement verification core and archived non-periodic benchmark gates, while cavity/cylinder candidate solvers remain future work. Phase 3 implements a correctness-first single-GPU CUDA candidate backend and CPU/CUDA comparison framework. No physical-validation claim is made.

## Purpose

NS-SIM treats a numerical fluid-dynamics experiment as a reproducible computational object: equations, discretization, grid, boundary conditions, initial conditions, timestep policy, solver configuration, precision, diagnostics, checkpoints, provenance, verification evidence, and backend identity are explicit.

The canonical reference is two-dimensional incompressible Navier–Stokes flow. Accelerated implementations may execute the same versioned numerical contract, but they may not silently redefine it.

NS-SIM is not a claim to solve the mathematical Navier–Stokes existence-and-smoothness problem, is not a safety-certified engineering CFD package, and must not present numerical output as exact continuum truth.

## Mathematical target

For velocity field `u`, pressure `p`, density `rho`, kinematic viscosity `nu`, and specific body-force acceleration `f`:

```text
∂u/∂t + (u·∇)u = -(1/rho)∇p + nu∇²u + f
∇·u = 0
```

In dimensional form, `f` has acceleration units (`L/T²`). Force-density input `b` contributes as `b/rho`; representation and units are part of the experiment contract.

## Phase 1 — canonical CPU reference

`cpu-reference-v1` currently fixes:

- float64 canonical state and little-endian `ns-sim-state/1` serialization;
- rectangular uniform cell-centered periodic 2D grids;
- centered second-order advection and diffusion;
- backward-divergence / forward-gradient projection pair;
- Forward-Euler predictor/projection stepping;
- deterministic periodic Jacobi pressure iteration;
- mean-zero pressure gauge;
- fixed timestep with declared CFL/diffusion limits;
- deterministic checkpoints, diagnostics, receipts, and provenance;
- R1 initialization checks and explicit R2 repeat-execution verification.

Install the CPU/test environment:

```bash
python -m pip install -e '.[test]'
```

Normalize an experiment:

```bash
ns-sim normalize examples/phase1-periodic-vortex.json
```

Run the canonical CPU backend:

```bash
ns-sim run examples/phase1-periodic-vortex.json --output runs/cpu
```

Test same-environment CPU R2:

```bash
ns-sim verify-repeat examples/phase1-periodic-vortex.json --output runs/cpu-repeat
```

## Phase 2 — numerical verification

The executable Phase 2 core includes:

- systematic Taylor–Green spatial refinement;
- Richardson temporal self-convergence;
- per-step admissibility diagnostics;
- deterministic plane-Poiseuille analytic/no-slip verification;
- reusable refinement/profile/metric tooling;
- archived Ghia–Ghia–Shin Re=100 cavity data;
- archived DFG/FeatFlow Re=100 cylinder-wake metrics;
- explicit versioned tolerances and reference identities.

Run the executable core:

```bash
ns-sim verify-phase2 examples/phase1-periodic-vortex.json \
  --references verification/references \
  --output runs/phase2-verification.json
```

The cavity and cylinder archives are independent reference gates. They remain `candidate_required` until an implemented non-periodic wall/obstacle solver produces matching candidate observables.

See [Phase 2 numerical verification](docs/PHASE2_VERIFICATION.md).

## Phase 3 — CUDA acceleration

`cuda-single-gpu-v1` is a correctness-first CuPy implementation of the existing Phase 1 periodic float64 numerical contract.

The canonical experiment intentionally continues to request `cpu-reference-v1`; CUDA is named in Phase 3 execution/comparison artifacts as a candidate implementation of that frozen scientific contract. This keeps CPU↔GPU comparisons bound to one experiment identity instead of creating backend-dependent physics hashes.

Install one CUDA extra that matches the environment:

```bash
# CUDA 12.x
python -m pip install -e '.[test,cuda12]'

# CUDA 13.x
python -m pip install -e '.[test,cuda13]'
```

Capture a pinned GPU/software environment:

```bash
ns-sim cuda-provenance \
  --device 0 \
  --output provenance/cuda-device0.json
```

Run CUDA:

```bash
ns-sim run-cuda examples/phase1-periodic-vortex.json \
  --device 0 \
  --provenance-lock provenance/cuda-device0.json \
  --output runs/cuda
```

Test CUDA backend-local R2:

```bash
ns-sim verify-cuda-repeat examples/phase1-periodic-vortex.json \
  --device 0 \
  --provenance-lock provenance/cuda-device0.json \
  --output runs/cuda-repeat
```

Test CPU↔CUDA R3 under the versioned comparison contract:

```bash
ns-sim compare-backends examples/phase1-periodic-vortex.json \
  --device 0 \
  --contract verification/backends/cuda-single-gpu-v1.json \
  --provenance-lock provenance/cuda-device0.json \
  --output runs/cpu-vs-cuda.json
```

Benchmark only after the R3 gate passes:

```bash
ns-sim benchmark-backends examples/phase1-periodic-vortex.json \
  --device 0 \
  --contract verification/backends/cuda-single-gpu-v1.json \
  --provenance-lock provenance/cuda-device0.json \
  --warmup 1 \
  --repeats 5 \
  --output runs/cpu-vs-cuda-performance.json
```

The performance harness fails closed if numerical comparison fails. A recorded speed ratio is scoped to that experiment hash, source revision, comparison contract, and CPU/GPU environments.

See [Phase 3 CUDA acceleration](docs/PHASE3_CUDA.md).

## Reproducibility classes

NS-SIM distinguishes:

- **R0 — Contract reproducible:** normalized semantic experiment contract is fully specified and stably identified.
- **R1 — Initial-state reproducible:** canonical initialization reproduces the same serialized initial state under a declared environment.
- **R2 — Backend-local bitwise reproducible:** repeated executions match canonical identities in the same backend/device/software environment.
- **R3 — Cross-backend numerically reproducible:** implementations agree under declared metrics and tolerances.
- **R4 — Canonical reference reproducible:** the supported CPU reference reproduces an archived reference result under a pinned reference environment.

CPU R2 does not imply CUDA R2. CUDA R2 does not imply CPU↔CUDA R3. R3 does not imply bitwise CPU/GPU identity or cross-GPU bitwise identity.

## Verification versus physical validation

Numerical verification asks whether the implementation behaves consistently with its declared mathematical/discrete problem.

Physical validation asks whether the model adequately represents a physical system for a stated purpose and regime. A positive validation claim requires physical observations/measurements, mapping, uncertainty, metric, acceptance criteria, and scope.

Backend agreement, analytic convergence, regression tests, and performance results are not physical validation by themselves.

Current physical-validation status is `not_claimed`.

## Design principles

1. **Reference before acceleration.** The CPU reference defines the audit boundary before optimization.
2. **Configuration is part of the result.** Scientific semantics are never hidden in launch scripts.
3. **Receipts over screenshots.** Evidence includes identities, diagnostics, tolerances, checkpoints, and provenance.
4. **Determinism is qualified.** R1/R2/R3/R4 are different claims.
5. **Verification before spectacle.** Analytic/refinement and benchmark evidence precede large research runs.
6. **No hidden physics.** Filters, forcing, precision changes, solver changes, and backend deviations must be declared.
7. **Performance cannot waive correctness.** CUDA timing is gated by CPU-reference numerical agreement.
8. **Visualization and sonification are derived views.** They never redefine canonical state.

## Repository layout

```text
NS-SIM/
├── src/ns_sim/          # canonical CPU runtime + candidate CUDA backend
├── schemas/             # versioned experiment/receipt/evidence schemas
├── examples/            # executable experiment contracts
├── verification/        # numerical reference and backend-comparison contracts
├── tests/               # runtime, verification, and backend regressions
├── docs/                # scientific and engineering contracts
├── .github/workflows/   # CPU CI / contract verification
├── viz/                 # future derived visualization tooling
├── sonification/        # future derived deterministic audio mappings
├── formal/              # later formal specifications / assurance where useful
└── containers/          # future reproducible remote/GPU environments
```

Future directories are architectural targets, not claims that those implementations already exist.

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Scientific contract](docs/SCIENTIFIC_CONTRACT.md)
- [Phase 1 runtime contract](docs/PHASE1_RUNTIME.md)
- [Phase 2 numerical verification](docs/PHASE2_VERIFICATION.md)
- [Phase 3 CUDA acceleration](docs/PHASE3_CUDA.md)
- [Determinism and reproducibility](docs/DETERMINISM.md)
- [Verification and validation policy](docs/VALIDATION.md)
- [Experiment schema](docs/EXPERIMENT_SCHEMA.md)
- [Backend contract](docs/BACKENDS.md)
- [Remote compute policy](docs/REMOTE_COMPUTE.md)
- [Claims policy](CLAIMS.md)
- [Reproducibility](REPRODUCIBILITY.md)
- [Roadmap](ROADMAP.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Release policy](docs/RELEASE_POLICY.md)

AI-agent instructions are intentionally machine-readable. See `AGENTS.md`.

## License

Apache License 2.0. See [LICENSE](LICENSE).
