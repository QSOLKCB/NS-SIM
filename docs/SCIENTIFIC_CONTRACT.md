# Scientific Contract

## Scope

The first NS-SIM scientific target is a finite-dimensional numerical approximation of two-dimensional incompressible Navier–Stokes flow. The exact discrete scheme becomes part of the contract only when implemented and versioned.

## Governing continuum model

For velocity `u(x,t)`, pressure `p(x,t)`, density `rho`, kinematic viscosity `nu`, and body force `f`:

```text
∂u/∂t + (u·∇)u = -(1/rho)∇p + nu∇²u + f
∇·u = 0
```

A numerical run approximates this model under a declared domain, discretization, initial condition, boundary condition, timestep policy, pressure treatment, precision, and tolerance set.

## Contract boundaries

A scientifically complete experiment must declare or inherit from a versioned profile:

- dimensionality and domain;
- coordinate/grid convention;
- state variables;
- density and viscosity or nondimensional equivalents;
- initial condition;
- boundary conditions;
- forcing;
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

Pressure may have a gauge freedom depending on formulation and boundary conditions. Validation must compare pressure in a gauge-consistent way or compare gauge-invariant quantities.

## Numerical validity

A run is invalid if required solver convergence fails, canonical state becomes non-finite, hard timestep admissibility is violated, required constraints exceed configured failure tolerances, or the experiment contract is malformed.

## Extension rule

Compressible flow, free surfaces, multiphase flow, turbulence closures, passive scalars, thermal models, SPH, and other future models require their own versioned scientific contracts. They must not be silently folded into the incompressible reference contract.
