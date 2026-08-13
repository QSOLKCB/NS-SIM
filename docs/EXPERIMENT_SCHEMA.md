# Experiment Schema Requirements

The concrete file format is not yet frozen. YAML, TOML, or JSON may be used during implementation, but a versioned canonical normalization must exist before experiment hashes are treated as stable identities.

## Required semantic groups

A future experiment schema should represent at least:

```text
schema_version
experiment_name
model
model_version
domain
grid
material_or_nondimensional_parameters
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

## Forcing semantics

For the canonical incompressible model, the momentum equation uses `f` as a **specific body-force acceleration** with dimensional units `L/T²`.

A forcing input must therefore declare at least:

```text
forcing.representation
forcing.units_or_nondimensional_convention
forcing.value_or_generator
```

Supported representations may include:

```text
specific_body_force_acceleration
force_density
```

If `force_density` is supplied, the canonical normalization must convert it to specific acceleration using `f = b/rho`, after checking units and density semantics. That conversion is part of the semantic experiment contract and must affect the normalized experiment identity when its inputs differ.

No implementation may interpret an unqualified forcing field sometimes as acceleration and sometimes as force density.

## Schema rules

- Units or nondimensional conventions must be explicit.
- Defaults that affect results must be versioned and visible after normalization.
- Unknown fields should fail validation unless a versioned extension mechanism explicitly allows them.
- Ordering differences in source files must not create different canonical identities when semantics are identical.
- Numeric serialization used for hashing must be specified.
- Paths included in the semantic contract must use portable, normalized rules.
- Secrets are forbidden.

## Canonical normalization

The normalized form used for hashing should be machine-readable, deterministic, and schema-versioned. It should not include ephemeral values such as timestamps, temporary paths, hostnames, or remote-job IDs unless those values actually alter simulation semantics.

R0 classification applies to this normalized semantic contract and does not require execution provenance. Execution metadata is attached when a run occurs.

## Separation of experiment and execution metadata

Requested backend may be part of the experiment/run request, but discovered hardware identity, wall-clock timing, cost, remote host ID, and scheduler metadata belong in execution provenance rather than the physical model definition.

A completed run receipt must preserve enough execution provenance to support any claimed R1–R4 classification even though those fields are not part of the R0 semantic experiment identity.
