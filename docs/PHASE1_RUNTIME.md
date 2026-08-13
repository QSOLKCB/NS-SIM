# Phase 1 Canonical Runtime Contract

## Status

Phase 1 implements `cpu-reference-v1` for `ns-sim-experiment/1`. It is a pre-alpha reference runtime intended for auditability, deterministic regression, and minimum numerical verification before acceleration.

## Supported model

`incompressible-navier-stokes-2d` version `1` currently supports rectangular uniform cell-centered grids with periodic boundaries in both axes. State arrays have shape `(ny, nx)` and use float64.

Dimensional contracts are intentionally narrow. `domain.units = "m"` requires `material.units = "SI"`; `domain.units = "nondimensional"` requires `material.units = "nondimensional"`. Phase 1 has no implicit dimensional/nondimensional conversion scale.

## Discrete operators and step

Advection and viscous derivatives use centered second-order periodic differences. Projection uses backward discrete divergence and forward pressure gradient, whose composition matches the five-point pressure Laplacian.

The explicit predictor is

```text
u* = u + dt[-(u·∇)u + nu∇²u + fx]
v* = v + dt[-(u·∇)v + nu∇²v + fy]
```

Pressure solves `∇²p = (rho/dt) ∇·u*`. The right-hand-side mean is removed for periodic solvability. Deterministic Jacobi iteration starts from zero each step and each iterate is shifted to zero mean to fix the pressure gauge. Velocity is then corrected by the declared forward gradient.

The pressure solve fails if its L∞ residual does not reach the configured tolerance by `max_iterations`.

## Timestep admissibility

The runtime computes

```text
advective_cfl = dt * (max|u|/dx + max|v|/dy)
diffusion_number = nu * dt * (1/dx² + 1/dy²)
```

and fails when either exceeds the experiment's declared limit. These guards are not a universal proof of stability or accuracy.

## Initial conditions and forcing

Phase 1 implements `zero` and a deterministic square-periodic `taylor_green` initializer. Taylor–Green modes must be strictly below the Nyquist limit in both grid dimensions so the initializer cannot silently alias or collapse a requested nonzero mode.

Canonical forcing is specific body-force acceleration. `force_density` input is normalized using `f = b/rho`, while both input and normalized semantics remain visible in the normalized contract.

## Numerical verification included in Phase 1

The canonical solver is not declared implemented on smoke tests alone. CI includes two numerical-verification checks:

1. a discrete shear wave whose nonlinear term and projection vanish, allowing the centered diffusion eigenvalue plus the Forward-Euler update to be checked directly to floating-point tolerance;
2. a Taylor–Green analytic comparison using coupled grid/time refinement from 16² to 32², requiring the refined velocity-field error to be materially smaller than the coarse error.

These checks exercise the declared diffusion/time integration exactly and the coupled advection/projection/diffusion trajectory against a continuum analytic solution. They are minimum Phase 1 evidence, not the complete Phase 2 verification programme.

## Canonical identities and checkpoints

The normalized experiment identity JSON sorts object keys and encodes semantic float64 values using exact IEEE-754 hexadecimal representation inside `$float64` objects before SHA-256 hashing.

`ns-sim-state/1` is an uncompressed binary format with magic `NSSIMSTATE1\n`, a big-endian 64-bit JSON-header length, compact sorted UTF-8 metadata, then contiguous little-endian float64 `u || v || p` payloads in C order. SHA-256 of the complete byte stream is the canonical state/checkpoint hash.

## Receipts and reproducibility evidence

`ns-sim-receipt/1` records deterministic run identity, source revision when it can be derived from the actual NS-SIM source checkout, experiment identity, backend/environment identity, initial/final/checkpoint hashes, diagnostics, reproducibility status, numerical-verification status, and physical-validation status. Running an installed package from an unrelated Git checkout must not cause that unrelated commit to be recorded as NS-SIM provenance.

The R1 environment identity includes backend, precision, runtime identity, and the `ns-sim-state/1` serialization contract. A single run demonstrates only R0/R1 evidence. `ns-sim verify-repeat` executes twice and reports R2 only when experiment/environment identities, state/checkpoint hashes, and diagnostic histories match exactly.

## Explicit non-claims

Phase 1 does not claim the expanded Phase 2 numerical-verification suite is complete, any physical validation, R3 cross-backend agreement, R4 archival reproducibility, GPU support, or non-periodic wall/obstacle/free-surface physics.
