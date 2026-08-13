# Determinism and Reproducibility Classes

NS-SIM treats determinism as a qualified property. Reproducibility classes describe different evidence levels and must not be silently promoted.

## R0 — Contract reproducible

The normalized semantic experiment contract is complete, schema-valid, and stably identified. Phase 1 `ns-sim normalize` produces the normalized contract and SHA-256 experiment identity. R0 does not require execution provenance.

## R1 — Initial-state reproducible

Canonical CPU initialization under a declared initialization environment produces the same serialized initial state and identity hash.

Phase 1 performs two canonical initializations before a run is accepted and requires their `ns-sim-state/1` hashes to match. Receipts identify backend, precision, Python/NumPy environment, machine/CPU identity, byte order, and serialization context. R1 remains environment-scoped.

## R2 — Backend-local bitwise reproducible

A single Phase 1 run does not claim R2. `ns-sim verify-repeat` performs two executions and reports R2 only when experiment/environment identities, initial/final hashes, checkpoint hashes, and diagnostic histories match exactly.

R2 must not be generalized to other devices or software stacks without testing.

## R3 — Cross-backend numerically reproducible

Two implementations agree under named comparison metrics and tolerances. R3 does not imply byte identity. No R3 claim exists in Phase 1 because no accelerated backend exists yet.

## R4 — Canonical reference reproducible

A supported CPU reference path reproduces an archived canonical result under a pinned environment and serialization contract. Phase 1 does not yet make R4 claims.

## Phase 1 identity encodings

Experiment hashing uses deterministic identity JSON where semantic float64 values are encoded using exact IEEE-754 hexadecimal representation inside `$float64` objects. Canonical state hashing uses `ns-sim-state/1`, with little-endian float64 `u`, `v`, `p` payloads in fixed C order.

Hashes establish byte identity, not physical validity.

## Classification requirements

| Class | Semantic contract | Execution environment | Hardware scope | Evidence |
| --- | --- | --- | --- | --- |
| R0 | required | not required | not required | normalized contract identity |
| R1 | required | canonical initialization environment required | recorded when material | repeated initial-state byte/hash identity |
| R2 | required | required | same declared environment | repeat-execution byte identity |
| R3 | required | required for each run | may differ | metric/tolerance agreement |
| R4 | required | pinned canonical reference environment | pinned/declared | archival byte/hash identity |

Floating-point contraction, runtime/library changes, architecture, reduction order, and solver iteration behavior can change low-order bits. Such variation must be measured and classified, not hidden by rounding outputs until hashes match.
