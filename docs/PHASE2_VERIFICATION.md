# Phase 2 Numerical Verification

Phase 2 expands NS-SIM's verification evidence without weakening the Phase 1 canonical runtime contract or turning numerical benchmarks into physical-validation claims.

## Implemented executable verification core

### Taylor–Green vortex

`ns_sim.verification` now provides reusable spatial and temporal refinement tooling around the canonical periodic CPU reference solver.

The spatial study compares the numerical velocity field with the analytic decaying Taylor–Green solution on a declared grid sequence. The temporal study keeps the spatial grid fixed and compares successively refined timesteps with a finer same-grid numerical reference at the same final time. This separation prevents the spatial truncation error from masking the Forward-Euler time-refinement signal.

The archived Taylor–Green gate records:

- maximum allowed finest-grid velocity L2 error;
- minimum observed spatial refinement order;
- minimum observed temporal self-convergence order.

### Poiseuille/channel flow

Phase 2 includes a deterministic one-dimensional steady plane-Poiseuille verification kernel with no-slip walls and constant specific body-force acceleration.

The tridiagonal finite-difference system is solved by an explicit Thomas algorithm rather than a dense BLAS solve. The quadratic analytic velocity profile is represented to roundoff by the centered second derivative. A trapezoidal volume-flow observable supplies a nontrivial second-order grid-refinement quantity.

The archived Poiseuille gate records:

- maximum profile L-infinity error;
- maximum wall-slip error;
- minimum observed flow-rate refinement order.

## Archived non-periodic numerical benchmark gates

The Phase 1 canonical backend supports periodic x/y boundaries only. Phase 2 therefore does not silently reinterpret that backend as a wall/obstacle solver.

Instead, Phase 2 archives independent benchmark contracts and comparison functions for candidate non-periodic solver outputs.

### Lid-driven cavity

The Re=100 reference archive stores centerline velocity data from Ghia, Ghia, and Shin (1982), DOI `10.1016/0021-9991(82)90058-4`, Tables I and II.

Candidate output must provide monotone coordinate/value arrays for:

- horizontal velocity `u` along the vertical centerline;
- vertical velocity `v` along the horizontal centerline.

NS-SIM interpolates the candidate onto the archived benchmark coordinates and evaluates L-infinity and RMSE differences under explicit repository tolerances.

### Cylinder wake / vortex shedding

The Re=100 archive follows the DFG/FeatFlow 2D-2 time-periodic flow-around-cylinder benchmark associated with Schaefer and Turek (1996). The archived fine-reference observables include:

- Strouhal number;
- mean drag coefficient;
- drag amplitude;
- lift amplitude.

The geometry, cylinder position/radius, viscosity, characteristic velocity, characteristic length, source attribution, reference values, and NS-SIM acceptance tolerances are stored together in the archive.

These are numerical benchmark comparisons. They are not experimental uncertainty statements and do not establish physical validation.

## Command line

Run the executable Phase 2 core:

```bash
ns-sim verify-phase2 examples/phase1-periodic-vortex.json \
  --references verification/references \
  --output runs/phase2-verification.json
```

Compare a future non-periodic solver candidate with an archived cavity or cylinder reference:

```bash
ns-sim verify-benchmark candidate.json verification/references/lid-driven-cavity-re100.json
ns-sim verify-benchmark candidate.json verification/references/cylinder-wake-re100.json
```

A benchmark command exits successfully only when the candidate satisfies every declared gate.

## Report semantics

`verify-phase2` reports `passed` only for the executable Taylor–Green and Poiseuille core. Lid-driven cavity and cylinder wake are reported as `reference_gate_ready` with `candidate_required: true` until an actual non-periodic solver produces candidate observables.

This distinction is intentional. An archived reference is evidence infrastructure; it is not evidence that an unsupported solver case has already passed.

`validation_status` remains `not_claimed` unless a separate physical-validation workflow supplies experimental or observational references, uncertainty information, a simulation-to-measurement mapping, comparison metrics, acceptance criteria, and a stated regime.
