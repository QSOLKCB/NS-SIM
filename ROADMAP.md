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
- CI regression and canonical smoke run.

Phase 1 does **not** complete the Phase 2 numerical-verification evidence suite.

## Phase 2 — Numerical verification suite

- Taylor–Green vortex;
- Poiseuille/channel flow;
- lid-driven cavity;
- cylinder wake / vortex shedding;
- grid/time refinement tooling;
- archived reference outputs and tolerances.

## Phase 3 — CUDA acceleration

- single-GPU backend;
- CPU-reference comparison harness;
- declared reproducibility classification;
- pinned GPU/software provenance;
- performance benchmarks that do not weaken verification requirements.

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
