# Reproducibility

Reproducibility is a first-class output of NS-SIM rather than an after-the-fact description.

## Reproducible experiment identity

A run should be identifiable from a normalized experiment definition plus all semantically relevant execution contracts. Exact fields will be versioned, but the identity model should include:

- model and equation version;
- discretization and solver version;
- domain/grid;
- initial and boundary conditions;
- forcing representation and normalized forcing semantics;
- timestep policy and stopping condition;
- precision;
- convergence tolerances;
- random seed where randomness exists;
- backend and backend-contract version.

The normalized semantic contract is sufficient for R0 identification. Execution provenance is a separate property of an executed run and is required for any claim whose class depends on a particular execution environment.

## Environment provenance

Receipts should capture enough information to classify reproducibility without embedding secrets. Relevant fields include source commit, OS/container identity, compiler/runtime versions, numerical libraries, CPU/GPU model, driver, CUDA/toolkit versions, and precision modes.

R1 byte identity is scoped to the declared canonical CPU initialization environment. R2–R4 claims require the execution provenance stated by their class definitions in [docs/DETERMINISM.md](docs/DETERMINISM.md).

## Hashes

Hashes establish byte identity, not physical validity. NS-SIM should use cryptographic hashes for normalized experiment definitions, canonical serialized states, checkpoints, and archival bundles. The chosen algorithm and serialization version must be explicit.

## Floating-point reality

Parallel floating-point computation is order-sensitive. GPU reductions, fused operations, library algorithms, compiler choices, and hardware generations can change low-order bits while remaining numerically consistent.

Therefore cross-backend comparison must use explicit norms and tolerances unless bitwise identity has been demonstrated under the exact declared environment.

## Verification versus validation

Reproducibility does not establish either numerical correctness or physical fidelity by itself. Numerical verification uses analytic/manufactured solutions, refinement, numerical benchmarks, residual checks, and backend-reference comparisons to test whether the declared equations are solved consistently. Physical validation requires qualifying experimental or observational evidence, uncertainty information, a mapping between simulation and measurement, and declared acceptance criteria.

A reproducible but unverified run must not be described as numerically verified. A verified numerical model must not be described as physically validated unless the separate validation requirements are met.

## Archival minimum

A release-quality reproducibility bundle should eventually contain:

- source revision or source archive;
- experiment definitions;
- schema versions;
- environment manifest;
- receipt(s);
- numerical-verification report;
- explicit physical-validation status;
- physical-validation report when a positive validation claim is made;
- reference hashes;
- known limitations;
- instructions to rerun the supported reference cases.
