# Determinism and Reproducibility Classes

NS-SIM treats determinism as a qualified property. Reproducibility classes describe different evidence levels and must not be silently promoted from one class to another.

## R0 — Contract reproducible

The full normalized semantic experiment contract is complete, schema-valid, and stably identified. Two parties can determine whether they intended to run the same modeled experiment.

R0 does **not** require execution provenance because an experiment may qualify for R0 before any execution has occurred. Once a run is executed, its receipt must separately capture the execution provenance required to interpret or claim higher reproducibility classes.

Phase 1 `ns-sim normalize` emits the normalized contract and SHA-256 experiment identity.

## R1 — Initial-state reproducible

Canonical CPU initialization under a declared initialization environment produces the same serialized initial state and identity hash.

The R1 environment must identify the canonical CPU backend, precision mode, software/runtime or container identity, and serialization contract/version. Hardware identity must also be recorded when hardware-dependent initialization behavior is possible. R1 is therefore an environment-scoped byte-identity claim, not an implicit cross-device claim.

Phase 1 performs the canonical initialization twice before accepting a run and requires the two `ns-sim-state/1` hashes to match.

## R2 — Backend-local bitwise reproducible

Repeated execution in a declared backend/device/software environment produces byte-identical canonical outputs according to the relevant serialization contract.

R2 is empirical and environment-scoped. It must not be generalized to other devices or software stacks without testing.

A single Phase 1 run does not claim R2. `ns-sim verify-repeat` performs two executions and reports R2 only when experiment/environment identities, initial/final state hashes, checkpoint hashes, and diagnostic histories match exactly.

## R3 — Cross-backend numerically reproducible

Two implementations agree under named comparison metrics and tolerances. Appropriate measures may include field norms, divergence residual, kinetic-energy history, enstrophy, integral quantities, frequency/Strouhal behavior, or case-specific observables.

R3 does not imply byte identity. Phase 1 has no R3 claim because no accelerated backend exists yet.

## R4 — Canonical reference reproducible

The project-supported CPU reference path reproduces an archived canonical reference result under its pinned environment and serialization contract.

R4 requires the archival reference identity, source revision, pinned execution environment, canonical serialization version, and hashes used to establish byte identity. Phase 1 does not yet make R4 claims.

## Phase 1 identity encodings

The experiment hash is computed over deterministic JSON with sorted keys and no insignificant whitespace. Semantic binary64 values are encoded using exact IEEE-754 hexadecimal representation inside `$float64` objects, so decimal pretty-print formatting cannot alter identity.

Canonical state/checkpoint hashing uses `ns-sim-state/1`: a declared header plus little-endian float64 `u`, `v`, and `p` arrays in fixed C order.

Hashes establish byte identity, not physical validity.

## Classification requirements

| Class | Semantic contract | Execution environment | Hardware scope | Evidence |
| --- | --- | --- | --- | --- |
| R0 | required | not required | not required | normalized contract identity |
| R1 | required | canonical initialization environment required | recorded when material | repeated initial-state byte/hash identity |
| R2 | required | required | same declared device/environment | repeated-run byte identity |
| R3 | required | required for each run | may differ | metric/tolerance agreement |
| R4 | required | pinned canonical reference environment | pinned/declared as applicable | archival byte/hash identity |

A completed run may possess an R0-identifiable experiment while still being unusable for R2–R4 claims if its execution provenance is incomplete.

## Comparison rule

A numerical comparison must identify:

```text
reference_run
candidate_run
fields_or_observables
norm_or_metric
tolerance
sampling_alignment
precision
backend_identity
result
```

Bitwise classifications must additionally identify the serialization contract and all environment fields required by the relevant class.

## Sources of legitimate variation

Potential sources include reduction order, floating-point contraction/FMA, compiler transformations, CPU/GPU architecture, library selection, pressure-solver ordering, atomic operations, mixed precision, and nondeterministic kernels.

Such variation must be measured and classified, not hidden by rounding outputs until hashes match.
