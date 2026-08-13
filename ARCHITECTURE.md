# NS-SIM Architecture

## Architectural objective

NS-SIM separates the **scientific contract** from the **execution backend**. The same experiment definition should be interpretable by a canonical reference implementation and by accelerated implementations without allowing backend optimizations to silently redefine the modeled problem.

Phase 1 now implements the first canonical execution path rather than leaving the architecture purely planned.

## Implemented Phase 1 data flow

```text
JSON experiment
      |
      v
strict schema + semantic normalization
      |
      +--> exact-float identity document --> SHA-256 experiment hash
      |
      v
canonical 2D model contract
      |
      v
cpu-reference-v1 / NumPy -----> hardware/software provenance
      |
      v
simulation states ------------> .nss checkpoints + hashes
      |
      +------------------------> diagnostics
      |
      v
final state + receipt
```

The package implementation lives under `src/ns_sim/`; schema artifacts are under `schemas/`; executable experiment examples are under `examples/`; regressions are under `tests/`.

## Layer model

### 1. Canonical layer

Owns the mathematical and numerical definition of a supported model:

- governing equations;
- nondimensionalization or units policy;
- grid and coordinate conventions;
- discrete operators;
- initial and boundary conditions;
- timestep admissibility;
- pressure/projection formulation;
- serialization rules for canonical state.

Phase 1 freezes one narrow canonical contract: uniform cell-centered periodic 2D grids, centered second-order advection and diffusion, a backward-divergence/forward-gradient projection pair, forward-Euler predictor/projection stepping, deterministic periodic Jacobi pressure solve, float64 state, and `ns-sim-state/1` serialization.

Changes here are scientific-contract changes and require documentation, regression, receipt/schema impact review, and appropriate numerical-verification updates.

### 2. Runtime layer

Owns execution semantics that are independent of a particular accelerator:

- experiment parsing and normalization;
- experiment and run identity;
- checkpoint scheduling;
- diagnostic collection;
- provenance capture;
- receipt generation;
- repeat-execution comparison.

Phase 1 implements these responsibilities in `src/ns_sim/` and fails closed rather than silently coercing unsupported contracts.

### 3. Backend layer

Implements canonical operations on a declared execution target. Current and planned targets are:

- **implemented:** `cpu-reference-v1`;
- **future:** CUDA single-GPU acceleration;
- **future:** multi-GPU/domain-decomposed execution.

A backend may optimize implementation but may not silently change equations, boundary conditions, precision, filters, convergence thresholds, or timestep policy.

### 4. Evidence layer

Software regressions and invariant checks establish runtime behavior. Numerical verification compares outputs against analytic/manufactured solutions, numerical benchmark data, convergence expectations, conservation/divergence metrics, and canonical reference results.

Physical validation is distinct: it requires comparison to experimental or observational evidence with uncertainty, mapping, metric, acceptance criteria, and scope. Neither regression success nor backend agreement alone is physical validation.

Phase 1 contains runtime regressions only. The Phase 2 verification suite remains future work.

### 5. Derived-output layer

Visualization, sonification, spectra, videos, and other representations are downstream products. They may be deterministically generated from canonical states, but they are not authoritative simulation state.

## Dependency direction

The reference/canonical layer must not depend on visualization or sonification. Accelerated backends depend on canonical interfaces, not the reverse. Verification tooling may consume canonical and backend results. Archival tooling may consume every stable artifact but must not alter simulation results.

## Canonical state

Phase 1 canonical state consists of float64 velocity fields `u`, `v`, gauge-fixed pressure `p`, step/time metadata, and the binding experiment hash.

`ns-sim-state/1` serializes a compact sorted JSON header followed by contiguous little-endian float64 `u`, `v`, and `p` arrays in C order. SHA-256 of the complete byte stream is the canonical state/checkpoint hash.

Derived caches, rendering buffers, audio buffers, UI state, wall-clock timing, and non-semantic logging are excluded from canonical state unless a later contract explicitly promotes them.

## Failure philosophy

NS-SIM fails closed on malformed or scientifically ambiguous experiment definitions. Unknown configuration fields, unsupported solver combinations, non-finite state, failed pressure convergence, invalid boundary specifications, or violated hard timestep constraints produce explicit run failure rather than a plausible-looking result.
