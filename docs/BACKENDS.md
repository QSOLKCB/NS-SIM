# Backend Contract

Backends execute a versioned canonical numerical contract. They are replaceable execution implementations, not alternate sources of physics.

## Canonical CPU backend

Phase 1 implements `cpu-reference-v1` in NumPy. The reference path prioritizes clarity, determinism, and auditability over peak performance and is the basis for regression and accelerated-backend comparison.

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

Phase 3 implements `cuda-single-gpu-v1` with CuPy as a correctness-first single-GPU candidate backend for the existing periodic float64 contract.

The canonical experiment still declares `backend_request.name = cpu-reference-v1`. CUDA execution is an explicitly named candidate implementation of that frozen contract; Phase 3 does not broaden or silently rewrite the Phase 1 experiment schema.

The backend currently mirrors:

- `finite_difference_projection_v1`;
- centered second-order advection and diffusion;
- backward-divergence / forward-gradient projection;
- `forward_euler_projection_v1`;
- `jacobi_periodic_v1`;
- periodic x/y boundaries;
- float64 state and host-side `ns-sim-state/1` serialization;
- experiment-declared checkpoint scheduling and hard numerical diagnostics.

`ns-sim run-cuda` emits a versioned CUDA run artifact. `ns-sim cuda-provenance` captures an exact GPU/software environment lock, and `--provenance-lock` fails closed when the current environment differs from the pinned one.

The recorded CUDA environment includes GPU model, device ordinal, compute capability, total global memory, CUDA driver version, the CUDA runtime linked to CuPy, the locally detected CUDA runtime when available, CuPy/NumPy/Python versions, platform identity, byte order, precision, and the single-GPU/no-mixed-precision declaration.

`ns-sim verify-cuda-repeat` is the backend-local evidence path. It reports R2 only when repeated executions match experiment/environment identities, canonical initial/final state identities, checkpoint hashes, and diagnostic history.

`ns-sim compare-backends` is the cross-backend evidence path. It compares the CUDA candidate against `cpu-reference-v1` under `verification/backends/cuda-single-gpu-v1.json`. A passing gate reports R3 only for the specific experiment hash, source revision, comparison-contract identity, and recorded environments.

A CUDA backend does not inherit R2 from the CPU path. R2 and R3 are separately demonstrated claims.

### Performance gate

`ns-sim benchmark-backends` first executes the R3 numerical comparison and refuses to publish timing results if that gate fails. Timing reports include both environments, experiment identity, comparison-contract identity, individual durations, medians, and the observed speed ratio.

The first CUDA implementation intentionally mirrors the reference Jacobi iteration and synchronizes scalar residual checks. This favors auditability over peak throughput; later optimization is permitted only while the declared comparison gates remain satisfied.

## Precision

Precision is semantic when it can materially change the trajectory or evidence result. Phase 1 and `cuda-single-gpu-v1` accept only float64 canonical computation/state.

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
