# Backend Contract

Backends execute a versioned canonical numerical contract. They are replaceable execution implementations, not alternate sources of physics.

## Canonical CPU backend

Phase 1 implements `cpu-reference-v1` in NumPy. The reference path prioritizes clarity, determinism, and auditability over peak performance and is the basis for regression and future accelerated-backend comparison.

The current CPU contract includes:

- the `finite_difference_projection_v1` periodic 2D numerical contract;
- float64 canonical arrays;
- little-endian `ns-sim-state/1` serialization;
- strict experiment normalization and identity;
- declared pressure-solver stopping conditions;
- finite-state/CFL/diffusion-number failure checks;
- checkpoint and receipt generation;
- CPU/software/environment provenance;
- environment-scoped R1 and R2 evidence paths.

`ns-sim verify-repeat` is the Phase 1 R2 evidence path. It runs the same experiment twice and requires exact experiment/environment identities, initial/final state hashes, checkpoint hashes, and diagnostic histories before reporting backend-local bitwise reproducibility.

The current CPU implementation is not yet an archival R4 reference. R4 requires a pinned environment and archived reference result in a later release process.

## CUDA backend

A CUDA backend is future Phase 3 work. It may change memory layout, kernel fusion, parallel decomposition, reduction implementation, and other execution details where those changes preserve the declared numerical contract or are explicitly versioned deviations.

The backend must report relevant provenance such as GPU model, compute capability where useful, driver/runtime/toolkit versions, numerical-library versions, precision modes, and determinism settings.

A CUDA backend must not inherit R2 from the CPU path. Cross-backend equivalence is an R3-style numerical comparison unless direct byte identity has separately been demonstrated under the applicable environments.

## Precision

Precision is semantic when it can materially change the trajectory or evidence result. Phase 1 accepts only float64 canonical computation/state.

FP32, TF32, mixed precision, and reduced-precision solver paths require explicit future contracts and must not be silently substituted for float64.

## Backend conformance

A backend comparison evaluates more than final-frame appearance. Depending on the supported case, comparison should include:

- canonical field norms;
- divergence residuals;
- energy/enstrophy histories;
- solver convergence behavior;
- integral observables;
- benchmark-specific quantities.

The reference, metric, tolerance, sampling alignment, precision, and both backend environments must be identified. Performance gains do not waive numerical-verification requirements, and backend agreement is not physical validation.

## Multi-GPU future

Domain decomposition introduces halo exchange, reduction ordering, partition identity, synchronization, and communication-library behavior. These must be included in reproducibility analysis when multi-GPU execution is added.
