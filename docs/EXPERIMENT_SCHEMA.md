# Experiment Schema Requirements

Phase 1 freezes the first executable experiment schema as JSON: `ns-sim-experiment/1`. Its machine-readable companion is [`schemas/experiment-v1.schema.json`](../schemas/experiment-v1.schema.json).

The runtime performs strict semantic validation itself; the JSON Schema is an interoperability artifact and must remain consistent with the executable validator.

## Required semantic groups

Every Phase 1 experiment contains exactly these top-level groups:

```text
schema_version
experiment_name
model
domain
grid
material
initial_condition
boundary_conditions
forcing
discretization
time_integration
timestep_policy
solver
precision
stopping_condition
diagnostics
checkpoint_policy
backend_request
reproducibility_policy
```

Unknown fields fail closed.

## Phase 1 fixed choices

```text
schema_version                          ns-sim-experiment/1
model                                   incompressible-navier-stokes-2d / 1
grid.layout                             cell-centered-uniform
boundary_conditions.x                   periodic
boundary_conditions.y                   periodic
discretization.name                     finite_difference_projection_v1
discretization.advection                centered_second_order
discretization.diffusion                centered_second_order
discretization.divergence_gradient_pair backward_forward_v1
time_integration.name                   forward_euler_projection_v1
solver.pressure.method                  jacobi_periodic_v1
precision.dtype                         float64
precision.byte_order                    little
backend_request.name                    cpu-reference-v1
```

Unsupported alternatives are rejected rather than silently mapped onto these values.

## Forcing semantics

Canonical momentum forcing is specific body-force acceleration. Input must declare representation, units/nondimensional convention, and a two-component value. Supported representations are `specific_body_force_acceleration` and `force_density`.

`force_density` is normalized via `f = b/rho`. The normalized experiment retains the input representation/value and canonical acceleration value, so the conversion remains explicit in the semantic identity.

Phase 1 accepts a nondimensional convention or the narrow SI labels needed by implemented fields; it is not a general unit-conversion engine.

## Canonical normalization and hashing

All result-affecting choices are explicit; Phase 1 does not hide semantic defaults. The canonical identity document is deterministic JSON with sorted keys and no insignificant whitespace. Binary64 semantic values are represented by exact hexadecimal strings inside `$float64` objects before SHA-256 hashing.

R0 applies to this normalized semantic contract and does not require execution provenance.

## Experiment versus execution metadata

Requested backend is part of the experiment/run request. Discovered CPU identity, Python/NumPy versions, OS information, source revision, and other execution provenance belong in the receipt rather than the R0 experiment identity.

See [`examples/phase1-periodic-vortex.json`](../examples/phase1-periodic-vortex.json). Its Taylor–Green initializer is a deterministic runtime exercise, not yet a Phase 2 verification claim.
