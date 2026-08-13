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

## Separation of experiment and execution metadata

Requested backend may be part of the experiment/run request, but discovered hardware identity, wall-clock timing, cost, remote host ID, and scheduler metadata belong in execution provenance rather than the physical model definition.
