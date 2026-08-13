# Reproducibility

Reproducibility is a first-class output of NS-SIM rather than an after-the-fact description.

## Reproducible experiment identity

A run should be identifiable from a normalized experiment definition plus all semantically relevant execution contracts. Exact fields will be versioned, but the identity model should include:

- model and equation version;
- discretization and solver version;
- domain/grid;
- initial and boundary conditions;
- forcing;
- timestep policy and stopping condition;
- precision;
- convergence tolerances;
- random seed where randomness exists;
- backend and backend-contract version.

## Environment provenance

Receipts should capture enough information to classify reproducibility without embedding secrets. Relevant fields include source commit, OS/container identity, compiler/runtime versions, numerical libraries, CPU/GPU model, driver, CUDA/toolkit versions, and precision modes.

## Hashes

Hashes establish byte identity, not physical validity. NS-SIM should use cryptographic hashes for normalized experiment definitions, canonical serialized states, checkpoints, and archival bundles. The chosen algorithm and serialization version must be explicit.

## Floating-point reality

Parallel floating-point computation is order-sensitive. GPU reductions, fused operations, library algorithms, compiler choices, and hardware generations can change low-order bits while remaining numerically consistent.

Therefore cross-backend comparison must use explicit norms and tolerances unless bitwise identity has been demonstrated under the exact declared environment.

## Archival minimum

A release-quality reproducibility bundle should eventually contain:

- source revision or source archive;
- experiment definitions;
- schema versions;
- environment manifest;
- receipt(s);
- validation report;
- reference hashes;
- known limitations;
- instructions to rerun the supported reference cases.
