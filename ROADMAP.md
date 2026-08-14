# NS-SIM Roadmap

The roadmap is directional, not a release promise. Numerical verification and scientific claim discipline take precedence over feature count.

## Phase 0 — Documentation and contracts — complete

- repository purpose and claims policy;
- architecture boundaries;
- machine-readable AI-agent contract;
- determinism/reproducibility classes;
- verification/validation and experiment-schema requirements;
- CPU/GPU backend contract;
- remote-compute security expectations.

## Phase 1 — Canonical 2D reference runtime — implemented in pre-alpha

- 2D incompressible Navier–Stokes model;
- canonical uniform cell-centered periodic grid/state representation;
- documented finite-difference projection method;
- deterministic `cpu-reference-v1` backend;
- strict JSON experiment schema, normalization, and SHA-256 identity;
- deterministic state serialization, run receipts, and checkpoints;
- finite-state, divergence, pressure-convergence, CFL, diffusion-number, energy, and enstrophy diagnostics;
- R1 initialization check and explicit R2 repeat-execution verifier;
- exact discrete shear-wave check for the diffusion operator plus Forward-Euler update;
- Taylor–Green analytic comparison with coupled spatial/time refinement from 16² to 32² requiring reduced velocity-field error;
- CI regression and canonical smoke run.

Phase 1 therefore includes minimum numerical-verification evidence for the canonical operator/time-step implementation. It does **not** claim the broader Phase 2 verification programme is complete.

## Phase 2 — Expanded numerical verification suite — implementation in progress

Implemented:

- systematic Taylor–Green spatial refinement and same-grid temporal self-convergence tooling with archived tolerances;
- deterministic plane-Poiseuille analytic/no-slip verification with second-order flow-rate refinement;
- reusable refinement-order, profile-comparison, metric-comparison, and reference-archive tooling;
- archived Ghia–Ghia–Shin Re=100 lid-driven-cavity centerline reference data and explicit tolerances;
- archived DFG/FeatFlow Re=100 cylinder-wake force/Strouhal metrics and explicit tolerances;
- CLI and CI entry points for the executable Phase 2 core and non-periodic candidate benchmark comparison.

Still required before Phase 2 can be called complete:

- an implemented non-periodic wall/obstacle candidate solver contract capable of producing lid-driven-cavity observables;
- an implemented non-periodic wall/obstacle candidate solver contract capable of producing cylinder-wake force and shedding observables;
- successful candidate comparisons against the archived cavity and cylinder gates.

The Phase 1 periodic canonical backend is not silently broadened to satisfy these cases. Archived reference gates remain `candidate_required` until a solver with declared boundary/geometry semantics produces the candidate data.

## Phase 3 — CUDA acceleration — implementation available in pre-alpha

Implemented:

- `cuda-single-gpu-v1` correctness-first CuPy backend for the Phase 1 periodic float64 numerical contract;
- canonical CPU-defined initialization followed by explicit single-device CUDA execution;
- experiment-declared checkpoint scheduling and host serialization through `ns-sim-state/1`;
- exact CUDA GPU/software provenance capture and optional fail-closed provenance locks;
- backend-local CUDA repeat verifier with explicit R2 classification;
- CPU-reference/CUDA comparison harness with versioned metric/tolerance contract and explicit R3 classification;
- performance benchmark harness that refuses timing publication unless the R3 numerical-comparison gate passes;
- CPU-only CI coverage of the CUDA numerical path through NumPy emulation and comparison/provenance contract tests.

Hardware evidence still required before release-level CUDA claims:

- execute `verify-cuda-repeat` on a declared NVIDIA GPU and archive the R2 result;
- execute `compare-backends` on that environment and archive a passing R3 report;
- execute `benchmark-backends` only after the R3 gate passes and archive the scoped performance report;
- retain the exact CUDA provenance lock with the evidence.

Phase 3 code availability is not itself a claim that any particular GPU, driver, or CuPy environment has demonstrated R2/R3 or a speedup. Those claims require recorded hardware execution.

## Phase 4 — Derived analysis

- deterministic visualization;
- spectral diagnostics;
- deterministic sonification mappings;
- exportable analysis artifacts linked to run receipts.

## Phase 5 — Remote GPU execution

- reproducible container/runtime image;
- remote-job packaging;
- Vast.ai-compatible workflow;
- verified artifact return;
- cost/resource metadata kept separate from physical results.

## Phase 6 — 3D and advanced models

Only after the reference and verification architecture is stable:

- 3D incompressible flow;
- domain decomposition and multi-GPU execution;
- DNS/LES research paths;
- passive scalars, thermal/buoyancy models, and other extensions where their contracts can be independently verified and, where claimed, physically validated.
