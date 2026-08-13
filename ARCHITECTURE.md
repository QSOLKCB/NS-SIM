# NS-SIM Architecture

## Architectural objective

NS-SIM separates the **scientific contract** from the **execution backend**. The same experiment definition should be interpretable by a canonical reference implementation and by accelerated implementations without allowing backend optimizations to silently redefine the modeled problem.

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

Changes here are scientific-contract changes and require validation updates.

### 2. Runtime layer

Owns execution semantics that are independent of a particular accelerator:

- experiment parsing and normalization;
- run identity;
- checkpoint scheduling;
- diagnostic collection;
- provenance capture;
- receipt generation;
- replay and comparison.

### 3. Backend layer

Implements canonical operations on a declared execution target. Initial targets are:

- canonical CPU reference;
- CUDA single-GPU acceleration;
- later multi-GPU/domain-decomposed execution.

A backend may optimize implementation but may not silently change equations, boundary conditions, precision, filters, convergence thresholds, or timestep policy.

### 4. Validation layer

Compares outputs against analytic solutions, benchmark data, convergence expectations, conservation/divergence metrics, and canonical reference results.

Validation results must name the reference, metric, tolerance, grid, timestep, precision, and backend.

### 5. Derived-output layer

Visualization, sonification, spectra, videos, and other representations are downstream products. They may be deterministically generated from canonical states, but they are not authoritative simulation state.

## Planned data flow

```text
experiment source
      |
      v
normalize + validate configuration
      |
      +--> experiment hash
      |
      v
canonical model contract
      |
      v
selected backend ---------> hardware/software provenance
      |
      v
simulation states --------> checkpoints
      |
      +--------------------> diagnostics
      |
      +--------------------> visualization / sonification
      |
      v
final state + validation + receipt
```

## Dependency direction

The reference/canonical layer must not depend on visualization or sonification. Accelerated backends depend on canonical interfaces, not the reverse. Validation may consume canonical and backend results. Archival tooling may consume every stable artifact but must not alter simulation results.

## Canonical state

The exact serialized state format will be defined during implementation. At minimum, state identity must account for velocity fields and any other evolved canonical fields. Pressure treatment must be documented because pressure may be gauge-dependent depending on solver formulation.

Derived caches, rendering buffers, audio buffers, UI state, and non-semantic logging are excluded from canonical state unless a later contract explicitly promotes them.

## Failure philosophy

NS-SIM should fail closed on malformed or scientifically ambiguous experiment definitions. Unknown configuration fields, unsupported solver combinations, non-finite state, failed pressure convergence, invalid boundary specifications, or violated hard timestep constraints should produce explicit run failure rather than a plausible-looking result.
