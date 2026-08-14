# Changelog

All notable project changes should be documented here. The project is pre-alpha and has not yet issued a stable release.

## Unreleased

### Phase 3 CUDA acceleration

- Add `cuda-single-gpu-v1`, a correctness-first CuPy implementation of the existing periodic float64 projection contract.
- Keep `cpu-reference-v1` canonical and treat CUDA as an explicitly declared candidate execution backend rather than changing the Phase 1 experiment schema.
- Add exact GPU/software provenance capture and optional fail-closed provenance locks.
- Add CUDA backend-local repeat verification with explicit R2 classification.
- Add versioned CPU/CUDA field-and-diagnostic comparison gates with explicit R3 classification.
- Add fail-closed CPU/CUDA performance benchmarking that runs only after the numerical comparison passes.
- Preserve experiment checkpoint scheduling and canonical `ns-sim-state/1` serialization for CUDA candidate states.
- Add CUDA 12.x and CUDA 13.x optional CuPy dependency groups while keeping CPU installations GPU-free.
- Add CPU-only CI regressions for the CUDA numerical kernels, comparison tolerances, and provenance-lock behavior.
- Keep physical validation explicitly `not_claimed` and require real-GPU archived evidence before release-level CUDA reproducibility or performance claims.

### Phase 2 numerical verification

- Add reusable Taylor–Green spatial and temporal refinement studies with explicit archived acceptance gates.
- Add deterministic plane-Poiseuille analytic/no-slip verification and second-order flow-rate refinement.
- Add versioned verification-reference archives and candidate comparison utilities.
- Archive Re=100 Ghia–Ghia–Shin lid-driven-cavity centerline data with explicit NS-SIM tolerances.
- Archive Re=100 DFG/FeatFlow cylinder-wake Strouhal and force metrics with explicit NS-SIM tolerances.
- Add `verify-phase2` and `verify-benchmark` CLI commands plus CI coverage.
- Keep cavity/cylinder status fail-honest as `candidate_required` until a declared non-periodic wall/obstacle solver produces candidate observables.
- Keep physical validation explicitly `not_claimed`.

### Phase 1 canonical runtime

- Implement the `cpu-reference-v1` 2D incompressible periodic finite-difference projection runtime.
- Freeze `ns-sim-experiment/1`, `ns-sim-state/1`, and `ns-sim-receipt/1` Phase 1 artifact contracts.
- Add strict configuration normalization and SHA-256 experiment identities using exact float64 hexadecimal identity encoding.
- Add deterministic initialization, canonical checkpoints, diagnostics, fail-closed timestep/pressure checks, and provenance-bearing receipts.
- Add explicit repeated execution for backend-local R2 byte-identity evidence.
- Add executable example, test suite, JSON Schema artifacts, and GitHub Actions CI.
- Keep Phase 2 numerical-verification benchmarks and all physical-validation claims explicitly out of Phase 1 scope.

### Documentation foundation

- Define NS-SIM purpose and initial 2D incompressible Navier–Stokes scope.
- Establish architecture, scientific-contract, claims, determinism, verification/validation, backend, experiment-schema, remote-compute, security, contribution, and release documentation.
- Establish a machine-readable-only contract for AI-agent documentation.
- Define reproducibility classes that distinguish canonical CPU reference behavior from GPU numerical agreement.
