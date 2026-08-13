# NS-SIM

**Deterministic, reproducible fluid-dynamics simulation runtime for Navier–Stokes research, numerical verification, physical validation, GPU acceleration, visualization, and sonification.**

> Status: private pre-alpha research project. Phase 1 implements the canonical 2D CPU reference runtime. The Phase 2 numerical-verification suite is not yet complete, and no physical-validation claim is made.

## Purpose

NS-SIM treats a numerical fluid-dynamics run as a reproducible computational object: equations, discretization, grid, boundary conditions, initial conditions, timestep policy, solver configuration, backend, precision, diagnostics, checkpoints, hashes, and execution provenance are explicit parts of the contract.

NS-SIM is not a claim to solve the mathematical Navier–Stokes existence-and-smoothness problem, is not a safety-certified engineering CFD package, and must not present numerical output as exact continuum truth.

## Phase 1 runtime

Phase 1 provides a working reference implementation for **two-dimensional incompressible Navier–Stokes flow** on a uniform cell-centered periodic grid.

The implemented continuum target is

```text
∂u/∂t + (u·∇)u = -(1/rho)∇p + nu∇²u + f
∇·u = 0
```

where `f` is specific body-force acceleration. Force-density input is accepted only when explicitly identified and is normalized through `f = b/rho`.

The `cpu-reference-v1` numerical contract currently fixes float64 canonical state, little-endian serialization, uniform cell-centered rectangular grids, periodic x/y boundaries, centered second-order advection/diffusion, a backward-divergence/forward-gradient projection pair, forward-Euler stepping, a mean-zero pressure gauge, deterministic Jacobi pressure iteration, and fail-closed timestep/convergence checks.

This is deliberately narrow. No-slip walls, obstacles, alternate pressure solvers, CUDA, 3D, and benchmark tolerances belong to later versioned contracts.

## Install

```bash
python -m pip install -e '.[test]'
```

Python 3.11+ and NumPy are required.

## Run

```bash
ns-sim normalize examples/phase1-periodic-vortex.json
ns-sim run examples/phase1-periodic-vortex.json --output runs/example
ns-sim verify-repeat examples/phase1-periodic-vortex.json --output runs/repeat-check
```

A single execution may demonstrate R0/R1. `verify-repeat` reports R2 only after two executions match in the same declared environment. R3 requires a future cross-backend comparison; R4 requires an archived pinned reference result.

## Phase 1 artifacts

A successful run emits normalized and identity experiment JSON, a provenance-bearing `receipt.json`, and versioned `.nss` checkpoints. Semantic binary64 values are represented exactly for experiment hashing, and canonical state/checkpoint hashes use SHA-256 over the declared `ns-sim-state/1` byte format.

Diagnostics include finite-state status, discrete divergence L∞/L2, pressure residual/iterations, advective CFL, diffusion number, kinetic energy, enstrophy, and maximum velocity components.

Malformed contracts, unknown fields, unsupported combinations, non-finite state, declared timestep-limit violations, and pressure non-convergence terminate the run instead of producing a plausible-looking success receipt.

## Verification and validation boundary

Phase 1 includes regression and invariant tests for runtime behavior. Those tests are **not** the Phase 2 numerical-verification suite and are not physical validation.

The planned Phase 2 evidence suite includes Taylor–Green vortex, plane Poiseuille/channel flow, lid-driven cavity, cylinder wake/vortex shedding, and refinement tooling. Physical-validation claims additionally require experimental/observational evidence, uncertainty, metrics, acceptance criteria, and declared scope.

## Repository layout

```text
NS-SIM/
├── src/ns_sim/         # canonical Phase 1 runtime
├── schemas/            # versioned experiment and receipt schemas
├── examples/           # executable experiment contracts
├── tests/              # software/runtime invariant regressions
├── docs/               # scientific and engineering contracts
└── .github/workflows/  # CI checks
```

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
