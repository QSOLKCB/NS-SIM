# Backend Contract

Backends execute a versioned canonical numerical contract. They are replaceable execution implementations, not alternate sources of physics.

## Canonical CPU backend — implemented

Phase 1 implements `cpu-reference-v1` in NumPy and prioritizes clarity, determinism, and auditability over peak performance.

Its current contract includes CPU/NumPy execution, float64 canonical arrays, little-endian canonical state serialization, the periodic 2D discretization described in `PHASE1_RUNTIME.md`, environment-scoped R1/R2 evidence, and explicit source/software/hardware provenance in receipts.

`ns-sim verify-repeat` is the Phase 1 R2 evidence path. It compares two executions under one declared environment and requires exact experiment/environment identities, initial/final state hashes, checkpoint hashes, and diagnostics.

The CPU runtime is not yet an archival R4 reference; that requires a pinned release environment and archived reference result.

## CUDA backend — future Phase 3

A CUDA backend may change memory layout, kernel fusion, parallel decomposition, reduction implementation, and other execution details where those changes preserve the declared numerical contract or are explicitly versioned deviations.

Relevant GPU model/runtime/library/precision/determinism provenance must be reported.

## Precision

Phase 1 accepts only float64. FP32, TF32, mixed precision, and reduced-precision solver paths require future explicit contracts and must not be silently substituted.

## Backend conformance

Future accelerated-backend comparisons must evaluate canonical field norms, divergence residuals, energy/enstrophy histories, solver behavior, integral observables, and benchmark-specific quantities as appropriate. Such R3-style numerical agreement is distinct from physical validation.

## Multi-GPU future

Domain decomposition introduces halo exchange, reduction ordering, partition identity, synchronization, and communication-library behavior. These must be included in reproducibility analysis when multi-GPU execution is added.
