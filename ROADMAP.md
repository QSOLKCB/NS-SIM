# NS-SIM Roadmap

The roadmap is directional, not a release promise. Scientific validation takes precedence over feature count.

## Phase 0 — Documentation and contracts

- repository purpose and claims policy;
- architecture boundaries;
- machine-readable AI-agent contract;
- determinism/reproducibility classes;
- validation and experiment-schema requirements;
- CPU/GPU backend contract;
- remote-compute security expectations.

## Phase 1 — Canonical 2D reference runtime

- 2D incompressible Navier–Stokes model;
- canonical grid/state representation;
- documented projection method;
- deterministic CPU reference backend;
- configuration normalization and hashing;
- run receipts and checkpoints;
- finite-state, divergence, convergence, and timestep diagnostics.

## Phase 2 — Validation suite

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
- performance benchmarks that do not weaken validation.

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

Only after the reference and validation architecture is stable:

- 3D incompressible flow;
- domain decomposition and multi-GPU execution;
- DNS/LES research paths;
- passive scalars, thermal/buoyancy models, and other extensions where their contracts can be independently validated.
