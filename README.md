# NS-SIM

**Deterministic, reproducible fluid-dynamics simulation runtime for Navier–Stokes research, numerical verification, physical validation, GPU acceleration, visualization, and sonification.**

> Status: private pre-alpha research project. Phase 1 implements the canonical 2D CPU reference runtime. Interfaces and numerical contracts may still change before the first stable release. The Phase 2 numerical-verification suite is not yet complete, and no physical-validation claim is made.

## Purpose

NS-SIM is intended to make numerical fluid-dynamics experiments reproducible as complete computational objects: equations, discretization, grid, boundary conditions, initial conditions, timestep policy, solver configuration, backend, precision, diagnostics, checkpoints, and provenance are all part of the run contract.

The first implementation target is now realized as a deterministic reference runtime for **two-dimensional incompressible Navier–Stokes flow**. CUDA acceleration and later three-dimensional work remain future phases.

NS-SIM is not a claim to solve the mathematical Navier–Stokes existence-and-smoothness problem, is not a safety-certified engineering CFD package, and must not present numerical output as exact continuum truth.

## Initial mathematical target

For velocity field `u`, pressure `p`, density `rho`, kinematic viscosity `nu`, and specific body-force acceleration `f`:

```text
∂u/∂t + (u·∇)u = -(1/rho)∇p + nu∇²u + f
∇·u = 0
```

In dimensional form, `f` has units of acceleration (`L/T²`) and is force per unit mass. If an input is instead supplied as force density `b` (force per unit volume), its momentum-equation contribution is `b/rho`; the representation and units must be explicit and normalization to the canonical acceleration form is part of the experiment contract.

## Implemented Phase 1 numerical contract

Phase 1 implements `cpu-reference-v1` on a rectangular uniform cell-centered periodic grid. The versioned discrete contract currently fixes:

- float64 canonical state and little-endian canonical serialization;
- periodic boundaries in both axes;
- centered second-order advection and diffusion differences;
- a backward-divergence / forward-gradient projection pair;
- explicit forward-Euler predictor/projection stepping;
- deterministic periodic Jacobi pressure iteration;
- a mean-zero pressure gauge;
- declared pressure tolerance and iteration cap;
- fixed timestep with declared advective-CFL and diffusion-number limits;
- fail-closed handling of malformed contracts, non-finite state, pressure non-convergence, and timestep-limit violations.

This is intentionally narrow. Non-periodic walls, obstacles, alternate solvers, alternate precision, CUDA, multi-GPU, and 3D require later versioned contracts rather than silent implementation substitutions.

## Install and run

```bash
python -m pip install -e '.[test]'
```

Validate, normalize, and hash an experiment:

```bash
ns-sim normalize examples/phase1-periodic-vortex.json
```

Execute one canonical CPU run:

```bash
ns-sim run examples/phase1-periodic-vortex.json --output runs/example
```

Execute the same experiment twice in one declared environment and test backend-local R2 byte identity:

```bash
ns-sim verify-repeat examples/phase1-periodic-vortex.json --output runs/repeat-check
```

## Design principles

1. **Reference before acceleration.** A canonical CPU implementation establishes the numerical contract before GPU optimization.
2. **Configuration is part of the result.** A result without its complete experiment configuration is incomplete.
3. **Receipts over screenshots.** Runs emit machine-verifiable provenance, hashes, diagnostics, and checkpoint metadata alongside any later visual output.
4. **Determinism is qualified.** Bitwise reproducibility, backend-local reproducibility, and tolerance-based cross-device reproducibility are different claims and must be reported separately.
5. **Verification before spectacle.** Analytic-reference, refinement, and benchmark cases precede large turbulence runs. Physical-validation claims require separate physical evidence.
6. **No hidden physics.** Numerical stabilizers, filtering, forcing, clipping, precision changes, and backend-specific behavior must be declared.
7. **Visualization and sonification are derived views.** They may represent the simulation but never redefine its canonical state.

## Phase 1 artifacts

A successful run emits:

```text
<output>/
├── experiment.normalized.json
├── experiment.identity.json
├── receipt.json
└── checkpoints/
    └── step-XXXXXXXX.nss
```

The normalized experiment remains human-readable. The identity document represents semantic binary64 values using exact IEEE-754 hexadecimal strings before deterministic JSON serialization and SHA-256 hashing.

Canonical checkpoints use the versioned `ns-sim-state/1` binary format. The state payload contains `u`, `v`, and gauge-fixed `p` arrays plus step/time metadata bound to the experiment hash. SHA-256 of the complete declared byte stream is the state/checkpoint identity.

The `ns-sim-receipt/1` receipt records source revision when available, backend/software/hardware provenance, experiment identity, initial/final state hashes, checkpoint hashes, diagnostics, and explicit reproducibility, numerical-verification, and physical-validation status.

## Diagnostics and failure behavior

Phase 1 records, where applicable:

- finite-state status;
- discrete divergence L∞ and L2 norms;
- pressure-solver residual and iteration count;
- advective CFL;
- diffusion number;
- kinetic energy;
- enstrophy;
- maximum absolute velocity components.

Unknown fields, unsupported solver/boundary/precision combinations, non-finite state, pressure non-convergence, declared timestep-limit violations, and nonempty output-directory reuse fail closed instead of producing a plausible-looking success receipt.

## Phase 2 evidence suite

The planned Phase 2 suite is primarily a **numerical verification** suite:

- Taylor–Green vortex;
- plane Poiseuille/channel flow;
- lid-driven cavity;
- cylinder wake / vortex shedding;
- spatial and temporal refinement tooling;
- archived reference outputs and declared tolerances.

The Phase 1 example contains a Taylor–Green initializer only as a deterministic runtime exercise. Its presence does not constitute Taylor–Green numerical verification.

Each Phase 2 case must define its evidence type, reference source, expected diagnostics, acceptable error metrics, grid/time refinement expectations, and reproducibility requirements. A comparison against experimental or observational data counts as physical validation only when the physical mapping, measurement uncertainty, comparison metric, acceptance criteria, regime, and scope are documented.

## Reproducibility model

NS-SIM distinguishes several classes of reproducibility:

- **R0 — Contract reproducible:** the normalized semantic experiment contract is fully specified, schema-valid, and stably identified. Execution provenance is not required at R0 because no execution need have occurred.
- **R1 — Initial-state reproducible:** canonical CPU initialization under a declared initialization environment reproduces the same serialized initial state and identity hash. The environment includes backend, precision, software/runtime or container identity, serialization version, and hardware identity where material.
- **R2 — Backend-local bitwise reproducible:** repeated runs match canonical identities under a declared backend/device/software environment.
- **R3 — Cross-backend numerically reproducible:** results agree within declared norms and tolerances.
- **R4 — Canonical reference reproducible:** the supported CPU reference path reproduces an archival reference result under its pinned environment.

A single Phase 1 execution demonstrates R0/R1 evidence only. `ns-sim verify-repeat` reports R2 only after two same-environment executions match experiment/environment identities, initial/final state hashes, checkpoint hashes, and diagnostic histories. R3 is unavailable until another backend exists. R4 requires a later pinned archival reference.

A GPU result must never be promoted from numerical agreement to bitwise equivalence without evidence.

## Repository layout

```text
NS-SIM/
├── src/ns_sim/         # implemented canonical Phase 1 runtime
├── schemas/            # versioned experiment/receipt schema artifacts
├── examples/           # executable experiment contracts
├── tests/              # software/runtime invariant regressions
├── docs/               # scientific and engineering contracts
├── .github/workflows/  # CI
├── backends/           # future accelerated backends
├── validation/         # future Phase 2 verification / physical-validation tooling
├── viz/                # future derived visualization tooling
├── sonification/       # future derived deterministic audio mappings
├── formal/             # later formal specifications / assurance where useful
└── containers/         # future reproducible runtime environments
```

Future directories are architectural targets, not claims that those implementations already exist.

## Verification and validation boundary

Phase 1 regression tests establish software behavior, schema consistency, state serialization, projection invariants, receipt/checkpoint production, and same-environment repeat identity. They do **not** constitute the Phase 2 numerical-verification suite and are not physical validation.

`validation_status` may remain `not_claimed` where no physical-validation evidence applies. A positive physical-validation claim requires a separately identified physical reference and uncertainty/acceptance contract.

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Scientific contract](docs/SCIENTIFIC_CONTRACT.md)
- [Phase 1 runtime contract](docs/PHASE1_RUNTIME.md)
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
