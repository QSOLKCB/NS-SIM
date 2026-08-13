# Backend Contract

Backends execute a versioned canonical numerical contract. They are replaceable execution implementations, not alternate sources of physics.

## Canonical CPU backend

The first CPU implementation should prioritize clarity, determinism, and auditability over peak performance. It acts as the reference for regression and accelerated-backend comparison.

## CUDA backend

A CUDA backend may change memory layout, kernel fusion, parallel decomposition, reduction implementation, and other execution details where those changes preserve the declared numerical contract or are explicitly versioned deviations.

The backend must report relevant provenance such as GPU model, compute capability where useful, driver/runtime/toolkit versions, numerical-library versions, precision modes, and determinism settings.

## Precision

Precision is semantic when it can materially change the trajectory or validation result. FP64, FP32, TF32, mixed precision, and reduced-precision solver paths must not be silently substituted for one another.

## Backend conformance

A backend comparison should evaluate more than final-frame appearance. Depending on the case, compare:

- canonical field norms;
- divergence residuals;
- energy/enstrophy histories;
- solver convergence behavior;
- integral observables;
- benchmark-specific quantities.

## Multi-GPU future

Domain decomposition introduces halo exchange, reduction ordering, partition identity, synchronization, and communication-library behavior. These must be included in the reproducibility analysis when multi-GPU execution is added.
