# NS-SIM

**Deterministic, reproducible fluid-dynamics simulation runtime for Navier–Stokes research, numerical verification, physical validation, GPU acceleration, visualization, and sonification.**

> Status: private pre-alpha research project. Interfaces, numerical methods, and reproducibility contracts may change before the first stable release.

## Purpose

NS-SIM is intended to make numerical fluid-dynamics experiments reproducible as complete computational objects: equations, discretization, grid, boundary conditions, initial conditions, timestep policy, solver configuration, backend, precision, diagnostics, checkpoints, and provenance are all part of the run contract.

The first implementation target is a deterministic reference runtime for **two-dimensional incompressible Navier–Stokes flow**, followed by accelerated CUDA backends and later three-dimensional work.

NS-SIM is not a claim to solve the mathematical Navier–Stokes existence-and-smoothness problem, is not a safety-certified engineering CFD package, and must not present numerical output as exact continuum truth.

## Initial mathematical target

For velocity field `u`, pressure `p`, density `rho`, kinematic viscosity `nu`, and specific body-force acceleration `f`:

```text
∂u/∂t + (u·∇)u = -(1/rho)∇p + nu∇²u + f
∇·u = 0
```

In dimensional form, `f` has units of acceleration (`L/T²`) and is force per unit mass. If an input is instead supplied as force density `b` (force per unit volume), its momentum-equation contribution is `b/rho`; the representation and units must be explicit and normalization to the canonical acceleration form is part of the experiment contract.

The initial reference solver is planned around a documented projection method with explicit discretization, pressure solve, boundary treatment, timestep policy, and convergence criteria.

## Design principles

1. **Reference before acceleration.** A canonical CPU implementation establishes the numerical contract before GPU optimization.
2. **Configuration is part of the result.** A result without its complete experiment configuration is incomplete.
3. **Receipts over screenshots.** Runs should emit machine-verifiable provenance, hashes, diagnostics, and checkpoint metadata alongside visual output.
4. **Determinism is qualified.** Bitwise reproducibility, backend-local reproducibility, and tolerance-based cross-device reproducibility are different claims and must be reported separately.
5. **Verification before spectacle.** Analytic-reference, refinement, and benchmark cases precede large turbulence runs. Physical-validation claims require separate physical evidence.
6. **No hidden physics.** Numerical stabilizers, filtering, forcing, clipping, precision changes, and backend-specific behavior must be declared.
7. **Visualization and sonification are derived views.** They may represent the simulation but never redefine its canonical state.

## Planned evidence suite

The initial suite is primarily a **numerical verification** suite:

- Taylor–Green vortex
- Plane Poiseuille/channel flow
- Lid-driven cavity
- Cylinder wake / vortex shedding

Each case should define its evidence type, reference source, expected diagnostics, acceptable error metrics, grid/time refinement expectations, and reproducibility requirements. A comparison against experimental or observational data counts as physical validation only when the physical mapping, measurement uncertainty, and acceptance criteria are documented.

## Reproducibility model

NS-SIM distinguishes several classes of reproducibility:

- **R0 — Contract reproducible:** the normalized semantic experiment contract is fully specified and stably identified. Execution provenance is not required at R0 because no execution need have occurred.
- **R1 — Initial-state reproducible:** canonical CPU initialization under a declared initialization environment reproduces the same serialized initial state and identity hash. The environment includes backend, precision, software/runtime or container identity, and serialization version, plus hardware identity when it can affect initialization.
- **R2 — Backend-local bitwise reproducible:** repeated runs match bit-for-bit under a declared backend/device/software environment.
- **R3 — Cross-backend numerically reproducible:** results agree within declared norms and tolerances.
- **R4 — Canonical reference reproducible:** the supported CPU reference path reproduces the archival reference result under its pinned environment.

R0 identifies an experiment contract, not an executed run. Completed-run receipts require execution provenance independently of whether the experiment qualifies for R0.

A GPU result must never be promoted from numerical agreement to bitwise equivalence without evidence.

## Planned run receipt

A canonical run receipt should identify at least:

```text
schema_version
run_id
experiment_hash
solver_contract
source_revision
backend
hardware
precision
software_environment
initial_state_hash
checkpoint_hashes
final_state_hash
diagnostics
verification_result
validation_status
```

`validation_status` may be `not_claimed` when no physical-validation evidence applies. A positive physical-validation claim requires a separately identified validation reference and uncertainty/tolerance contract.

## Planned repository layout

```text
NS-SIM/
├── canonical/          # reference equations, discretizations, contracts
├── runtime/            # execution, receipts, checkpoints, replay
├── backends/           # CPU, CUDA, later multi-GPU implementations
├── experiments/        # canonical benchmark and research configurations
├── validation/         # verification and physical-validation evidence tooling
├── viz/                # derived visualization tooling
├── sonification/       # derived deterministic audio mappings
├── formal/             # later formal specifications / assurance where useful
├── containers/         # reproducible runtime environments
└── docs/               # scientific and engineering documentation
```

The layout is a target architecture, not a claim that these modules already exist.

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Scientific contract](docs/SCIENTIFIC_CONTRACT.md)
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
