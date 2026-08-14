# Phase 2 Numerical Verification

Phase 2 expands NS-SIM's verification evidence without weakening the Phase 1 canonical runtime contract or turning numerical benchmarks into physical-validation claims.

## Implemented executable verification core

### Taylor–Green vortex

`ns_sim.verification` provides reusable spatial and temporal refinement tooling around the canonical periodic CPU reference solver.

The archived Taylor–Green gate is bound to a declared unforced benchmark regime: domain, material parameters, Taylor–Green amplitude/mode, periodic boundaries, canonical zero body-force acceleration, discretization, time integration, precision, and backend identity. The archived study also fixes the refinement schedules to which its absolute tolerances apply.

The spatial study compares the numerical velocity field with the analytic decaying Taylor–Green solution on a declared grid sequence. All spatial levels must end at a common physical time.

The temporal study keeps the spatial grid fixed and uses Richardson self-convergence differences between successive timestep levels. A still-finer same-grid run is retained as a residual-reference diagnostic, but the observed temporal order is not computed against that finite reference. All temporal candidates and the residual reference must end at the same physical time.

Every Taylor–Green step computes the normal canonical runtime diagnostics and enforces the declared CFL, diffusion-number, and finite-state hard conditions. The per-step diagnostics are retained in the verification report; an inadmissible run cannot count as passing evidence.

The archived Taylor–Green gate records:

- maximum allowed finest-grid velocity L2 error;
- minimum observed spatial refinement order;
- minimum observed Richardson temporal order.

### Poiseuille/channel flow

Phase 2 includes a deterministic one-dimensional steady plane-Poiseuille verification kernel with no-slip walls and constant specific body-force acceleration.

The tridiagonal finite-difference system is solved by an explicit Thomas algorithm rather than a dense BLAS solve. The quadratic analytic velocity profile is represented to roundoff by the centered second derivative. A trapezoidal volume-flow observable supplies a nontrivial second-order grid-refinement quantity.

The Poiseuille reference and report explicitly declare the forcing representation (`specific_body_force_acceleration`) and its units or nondimensional convention; a bare acceleration scalar is not treated as a complete scientific contract.

The archived Poiseuille gate records:

- maximum profile L-infinity error;
- maximum wall-slip error;
- minimum observed flow-rate refinement order.

## Archived non-periodic numerical benchmark gates

The Phase 1 canonical backend supports periodic x/y boundaries only. Phase 2 therefore does not silently reinterpret that backend as a wall/obstacle solver.

Instead, Phase 2 archives independent benchmark contracts and comparison functions for candidate non-periodic solver outputs.

### Lid-driven cavity

The Re=100 reference archive stores centerline velocity data from Ghia, Ghia, and Shin (1982), DOI `10.1016/0021-9991(82)90058-4`, Tables I and II.

Candidate output must declare the archived cavity regime exactly and provide monotone finite coordinate/value arrays for:

- horizontal velocity `u` along the vertical centerline;
- vertical velocity `v` along the horizontal centerline.

The Reynolds number is compared numerically without integer truncation. Malformed candidates fail as controlled verification errors rather than uncaught mapping exceptions.

NS-SIM interpolates the candidate onto the archived benchmark coordinates and evaluates L-infinity and RMSE differences under explicit repository tolerances.

### Cylinder wake / vortex shedding

The Re=100 archive follows the DFG/FeatFlow 2D-2 time-periodic flow-around-cylinder benchmark associated with Schaefer and Turek (1996). The archived fine-reference observables include:

- Strouhal number;
- mean drag coefficient;
- drag amplitude;
- lift amplitude.

A cylinder candidate must declare the same Reynolds number, geometry, viscosity, characteristic quantities, reference timestep regime, and observable definitions. Drag/lift coefficient normalization and the Strouhal definition are part of the benchmark contract rather than implicit assumptions.

These are numerical benchmark comparisons. They are not experimental uncertainty statements and do not establish physical validation.

## Command line

Run the executable Phase 2 core:

```bash
ns-sim verify-phase2 examples/phase1-periodic-vortex.json \
  --references verification/references \
  --output runs/phase2-verification.json
```

`--references` is required. There is deliberately no working-directory-dependent default reference path.

Compare a future non-periodic solver candidate with an archived cavity or cylinder reference:

```bash
ns-sim verify-benchmark candidate.json verification/references/lid-driven-cavity-re100.json
ns-sim verify-benchmark candidate.json verification/references/cylinder-wake-re100.json
```

Benchmark candidates are JSON objects containing `case`, `regime`, the required observable contract, and the measured profiles or metrics. A benchmark command exits successfully only when the candidate contract matches the archived regime and every numerical gate passes.

## Report semantics and provenance

`verify-phase2` reports `passed` only for the executable Taylor–Green and Poiseuille core. Lid-driven cavity and cylinder wake are reported as `reference_gate_ready` with `candidate_required: true` until an actual non-periodic solver produces candidate observables.

The report binds archived evidence to:

- the normalized base-experiment identity;
- source revision when available;
- backend and precision identity;
- runtime/software/hardware environment identity;
- the identities of every reference archive used to determine the result.

Benchmark comparison reports likewise include candidate and reference identities.

This distinction is intentional. An archived reference is evidence infrastructure; it is not evidence that an unsupported solver case has already passed.

`validation_status` remains `not_claimed` unless a separate physical-validation workflow supplies experimental or observational references, uncertainty information, a simulation-to-measurement mapping, comparison metrics, acceptance criteria, and a stated regime.
