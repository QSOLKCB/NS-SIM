# Scientific Contract

## Scope

The first NS-SIM scientific target is a finite-dimensional numerical approximation of two-dimensional incompressible Navier–Stokes flow. The exact discrete scheme becomes part of the contract only when implemented and versioned.

## Governing continuum model

For velocity `u(x,t)`, pressure `p(x,t)`, density `rho`, kinematic viscosity `nu`, and specific body-force acceleration `f`:

```text
∂u/∂t + (u·∇)u = -(1/rho)∇p + nu∇²u + f
∇·u = 0
```

In dimensional form, `f` is force per unit mass and therefore has units of acceleration (`L/T²`). If a source supplies a force density `b` (force per unit volume), the corresponding term is `b/rho`. Experiment inputs must explicitly identify which forcing representation is supplied, together with units or a nondimensional convention. The canonical incompressible contract normalizes forcing to the specific-acceleration form used above.

A numerical run approximates this model under a declared domain, discretization, initial condition, boundary condition, timestep policy, pressure treatment, precision, and tolerance set.

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

## Incompressibility

The discrete divergence is generally not mathematically zero in floating-point arithmetic. NS-SIM must report the chosen divergence norm and tolerance rather than converting `small residual` into a claim of exact zero.

## Pressure

Pressure may have a gauge freedom depending on formulation and boundary conditions. Numerical verification or physical validation must compare pressure in a gauge-consistent way or compare gauge-invariant quantities.

## Numerical validity

A run is invalid if required solver convergence fails, canonical state becomes non-finite, hard timestep admissibility is violated, required constraints exceed configured failure tolerances, or the experiment contract is malformed.

## Verification and validation boundary

Numerical **verification** asks whether the implementation solves the declared mathematical/discrete problem consistently. Analytic solutions, manufactured solutions, refinement studies, numerical benchmark comparisons, residual checks, and backend-vs-reference comparisons are verification evidence.

Physical **validation** asks whether the modeled equations and parameterization represent a physical system adequately for a stated purpose and regime. A positive validation claim requires comparison to experimental or observational evidence with the physical mapping, measurement uncertainty, comparison metric, and acceptance criterion declared.

Verification evidence must not be relabeled as physical validation merely because a benchmark is well established.

## Extension rule

Compressible flow, free surfaces, multiphase flow, turbulence closures, passive scalars, thermal models, SPH, and other future models require their own versioned scientific contracts. They must not be silently folded into the incompressible reference contract.
