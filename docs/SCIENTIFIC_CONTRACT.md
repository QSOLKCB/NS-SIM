# Scientific Contract

## Scope

NS-SIM Phase 1 implements a finite-dimensional numerical approximation of two-dimensional incompressible Navier–Stokes flow. The executable discrete contract is versioned as `finite_difference_projection_v1` and `cpu-reference-v1`.

## Governing continuum model

For velocity `u(x,t)`, pressure `p(x,t)`, density `rho`, kinematic viscosity `nu`, and specific body-force acceleration `f`:

```text
∂u/∂t + (u·∇)u = -(1/rho)∇p + nu∇²u + f
∇·u = 0
```

Force-density input `b` is normalized through `f = b/rho`; representation and units remain explicit in the normalized contract.

## Phase 1 discrete contract

Phase 1 supports a rectangular uniform cell-centered grid with periodic boundaries in both axes and float64 canonical fields shaped `(ny, nx)`.

The implemented scheme uses centered second-order advective derivatives and diffusion Laplacians, backward discrete divergence, forward pressure gradient, explicit forward-Euler momentum prediction, a periodic projection step, deterministic Jacobi pressure iteration from zero each step, mean-zero pressure gauge fixing, and declared pressure residual tolerance/iteration cap.

See `PHASE1_RUNTIME.md` for executable details.

## Timestep and numerical validity

Phase 1 uses fixed `dt`. Each run declares maximum accepted advective CFL and diffusion number. Exceeding either is a hard failure. These are admissibility guards, not a proof of stability or accuracy.

A run is invalid if the contract is malformed, state becomes non-finite, pressure fails to converge, or a declared hard timestep condition is violated.

## Incompressibility and pressure

Receipts report discrete divergence L∞/L2 norms rather than claiming exact zero in floating-point arithmetic. Periodic pressure gauge freedom is fixed by zero-mean Jacobi iterates; pressure comparisons must retain this gauge contract or use gauge-invariant quantities.

## Verification and validation boundary

Phase 1 regression tests establish software/runtime invariants and deterministic artifact behavior. They do not constitute the Phase 2 numerical-verification suite.

Numerical verification requires analytic/manufactured solutions, refinement studies, numerical benchmark comparisons, residual checks, or other declared evidence. Physical validation separately requires experimental/observational evidence, mapping, uncertainty, metrics, acceptance criteria, and scope.

## Extension rule

Non-periodic walls, immersed obstacles, compressible flow, free surfaces, multiphase flow, turbulence closures, passive scalars, thermal models, SPH, alternate precision, and future GPU schemes require explicit versioned contract extensions. They must not be silently folded into `finite_difference_projection_v1`.
