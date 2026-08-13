# Determinism and Reproducibility Classes

NS-SIM treats determinism as a qualified property.

## R0 — Contract reproducible

The full semantic experiment contract can be normalized and identified. Two parties can determine whether they intended to run the same modeled experiment.

## R1 — Initial-state reproducible

Canonical initialization under the declared contract produces the same serialized initial state and identity hash.

## R2 — Backend-local bitwise reproducible

Repeated execution in a declared backend/device/software environment produces byte-identical canonical outputs according to the relevant serialization contract.

R2 is empirical and environment-scoped. It must not be generalized to other devices or software stacks without testing.

## R3 — Cross-backend numerically reproducible

Two implementations agree under named comparison metrics and tolerances. Appropriate measures may include field norms, divergence residual, kinetic-energy history, enstrophy, integral quantities, frequency/Strouhal behavior, or case-specific observables.

R3 does not imply byte identity.

## R4 — Canonical reference reproducible

The project-supported CPU reference path reproduces an archived canonical reference result under its pinned environment and serialization contract.

## Comparison rule

A comparison must identify:

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

## Sources of legitimate variation

Potential sources include reduction order, floating-point contraction/FMA, compiler transformations, GPU architecture, library selection, pressure-solver ordering, atomic operations, mixed precision, and nondeterministic kernels.

Such variation must be measured and classified, not hidden by rounding outputs until hashes match.
