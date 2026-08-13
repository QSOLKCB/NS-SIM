# Scientific Contract

## Scope

NS-SIM targets finite-dimensional numerical approximations of two-dimensional incompressible Navier–Stokes flow. Phase 1 now implements and versions the first exact discrete scheme as `finite_difference_projection_v1` on `cpu-reference-v1`.

## Governing continuum model

For velocity `u(x,t)`, pressure `p(x,t)`, density `rho`, kinematic viscosity `nu`, and specific body-force acceleration `f`:

```text
∂u/∂t + (u·∇)u = -(1/rho)∇p + nu∇²u + f
∇·u = 0
```

In dimensional form, `f` is force per unit mass and therefore has units of acceleration (`L/T²`). If a source supplies a force density `b` (force per unit volume), the corresponding term is `b/rho`. Experiment inputs must explicitly identify which forcing representation is supplied, together with units or a nondimensional convention. The canonical incompressible contract normalizes forcing to the specific-acceleration form used above.

A numerical run approximates this model under a declared domain, discretization, initial condition, boundary condition, timestep policy, pressure treatment, precision, and tolerance set.

## Phase 1 discrete contract

Phase 1 supports rectangular, uniform, cell-centered grids with periodic boundaries in both axes. Canonical fields are float64 arrays shaped `(ny, nx)`.

The implemented scheme uses:

- centered second-order differences for advective derivatives;
- centered second-order periodic Laplacians for diffusion;
- backward discrete divergence;
- forward pressure gradient, paired so divergence-of-gradient matches the pressure Laplacian;
- explicit forward-Euler momentum prediction;
- periodic projection;
- deterministic Jacobi pressure iteration from a zero initial pressure guess each step;
- mean-zero pressure gauge fixing;
- declared pressure residual tolerance and maximum iteration count.

See `PHASE1_RUNTIME.md` for executable details.

## Contract boundaries

A scientifically complete experiment must declare or inherit from a versioned profile:

- dimensionality and domain;
- coordinate/grid convention;
- state variables;
- density and viscosity or nondimensional equivalents;
- initial condition;
- boundary conditions;
- forcing representation, units/nondimensional convention, and normalized forcing semantics;
- spatial discretization;
- pressure/projection method;
- time integrator;
- timestep or adaptive timestep rule;
- solver stopping conditions;
- precision;
- filters, clipping, stabilization, or dealiasing if any.

If one of these materially affects the computed trajectory, it cannot remain an undocumented implementation detail.

## Timestep contract

Phase 1 uses fixed `dt`. Each experiment declares a maximum accepted advective CFL and diffusion number. Exceeding either is a hard run failure. These are declared run-admissibility guards, not a universal proof of numerical stability or accuracy.

## Incompressibility

The discrete divergence is generally not mathematically zero in floating-point arithmetic. Phase 1 receipts report L∞ and L2 divergence norms rather than converting a small residual into a claim of exact zero.

## Pressure

Pressure has gauge freedom under the Phase 1 periodic formulation. The runtime fixes the gauge by subtracting the mean during Jacobi iteration. Numerical verification or physical validation must compare pressure in a gauge-consistent way or compare gauge-invariant quantities.

## Numerical validity

A run is invalid if required solver convergence fails, canonical state becomes non-finite, hard timestep admissibility is violated, required constraints exceed configured failure tolerances, or the experiment contract is malformed.

## Verification and validation boundary

Phase 1 regression tests establish software/runtime invariants and deterministic artifact behavior. They do **not** constitute the Phase 2 numerical-verification suite.

Numerical **verification** asks whether the implementation solves the declared mathematical/discrete problem consistently. Analytic solutions, manufactured solutions, refinement studies, numerical benchmark comparisons, residual checks, and backend-vs-reference comparisons are verification evidence.

Physical **validation** asks whether the modeled equations and parameterization represent a physical system adequately for a stated purpose and regime. A positive validation claim requires comparison to experimental or observational evidence with the physical mapping, measurement uncertainty, comparison metric, and acceptance criterion declared.

Verification evidence must not be relabeled as physical validation merely because a benchmark is well established.

## Extension rule

Non-periodic walls, immersed obstacles, compressible flow, free surfaces, multiphase flow, turbulence closures, passive scalars, thermal models, SPH, alternate precision, future GPU schemes, and other models require their own explicit versioned scientific contracts. They must not be silently folded into `finite_difference_projection_v1`.
