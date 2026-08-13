# Experiment Schema Requirements

Phase 1 freezes the first executable experiment schema as JSON: `ns-sim-experiment/1`. Its machine-readable companion is [`schemas/experiment-v1.schema.json`](../schemas/experiment-v1.schema.json).

The Python runtime performs strict semantic validation itself. The JSON Schema is an interoperability artifact and must remain consistent with the executable validator; it is not a substitute for the canonical normalization code.

## Required semantic groups

A Phase 1 experiment represents exactly these top-level semantic groups:

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

## Phase 1 fixed contract choices

The first executable contract intentionally permits a narrow set of values:

```text
schema_version                          ns-sim-experiment/1
model                                   incompressible-navier-stokes-2d / "1"
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

`model.version` is the JSON string `"1"`; numeric `1` is rejected rather than silently coerced. Unsupported alternatives fail validation rather than being silently mapped onto these semantics.

## Dimensional contract

Phase 1 deliberately supports only internally consistent unit systems:

```text
domain.units = nondimensional  <=>  material.units = nondimensional
domain.units = m               <=>  material.units = SI
```

Mixed dimensional/nondimensional contracts are rejected because Phase 1 defines no reference scales capable of converting between them. This prevents a dimensional grid spacing from being combined with nondimensional viscosity or forcing while still producing an apparently valid receipt.

## Forcing semantics

For the canonical incompressible model, the momentum equation uses `f` as a **specific body-force acceleration** with dimensional units `L/T²`.

A forcing input declares:

```text
forcing.representation
forcing.units_or_nondimensional_convention
forcing.value
```

Phase 1 accepts these representations:

```text
specific_body_force_acceleration
force_density
```

If `force_density` is supplied, canonical normalization converts it to specific acceleration using `f = b/rho` after checking the declared density/unit convention. The normalized experiment preserves the input representation, input units, input value, canonical representation, canonical units, and canonical value. The conversion therefore remains visible and affects semantic identity when its inputs differ.

No implementation may interpret an unqualified forcing field sometimes as acceleration and sometimes as force density.

Phase 1 accepts a narrow nondimensional convention and the implemented SI labels; it is not a general unit-conversion engine.

## Initial-condition resolution

The Phase 1 Taylor–Green initializer is sampled on cell centres. Its integer mode must therefore be strictly below the Nyquist limit of **both** grid dimensions:

```text
2 * mode < nx
2 * mode < ny
```

Modes at or above that limit are rejected instead of being allowed to alias, or to collapse a requested nonzero mode into an effectively zero sampled field.

## Schema rules

- Units or nondimensional conventions must be explicit and internally paired as above.
- Defaults that affect results must be versioned and visible after normalization; Phase 1 avoids hidden semantic defaults.
- Unknown fields fail validation unless a future versioned extension mechanism explicitly allows them.
- Ordering differences in source JSON must not create different canonical identities when semantics are identical.
- Numeric values that cannot be represented as finite binary64 values fail as configuration errors rather than escaping as Python conversion exceptions.
- Numeric serialization used for hashing is specified and versioned.
- Paths included in the semantic contract must use portable, normalized rules when such fields are later introduced.
- Secrets are forbidden.
- Unsupported boundary, precision, backend, discretization, solver, model-version, or unit combinations fail closed.

## Canonical normalization

The normalized form used for hashing is machine-readable, deterministic, and schema-versioned. It excludes ephemeral execution values such as timestamps, temporary paths, discovered hostnames, and remote-job IDs.

For `ns-sim-experiment/1`, object keys are sorted and semantic binary64 values are represented by exact IEEE-754 hexadecimal strings wrapped as `$float64` objects before compact UTF-8 JSON serialization. SHA-256 of those bytes is `experiment_hash`.

Normalization is idempotent for a fully canonical normalized experiment. This allows the public result of `load_experiment()` to be passed directly to APIs such as `execute_experiment()`. A normalized-looking dictionary whose derived canonical forcing fields no longer agree with its preserved input semantics is rejected rather than silently accepted.

R0 classification applies to this normalized semantic contract and does not require execution provenance. Execution metadata is attached when a run occurs.

## Separation of experiment and execution metadata

Requested backend remains part of the experiment/run request, but discovered hardware identity, Python/NumPy versions, OS information, source revision, wall-clock timing, cost, remote host ID, and scheduler metadata belong in execution provenance rather than the physical model definition.

A completed run receipt must preserve enough execution provenance to support any claimed R1–R4 classification even though those fields are not part of the R0 semantic experiment identity. For R1, the hashed environment identity includes the canonical `ns-sim-state/1` serialization contract and the declared precision contract.

Source revision is derived only from an identified NS-SIM source checkout or an explicit trusted override; the current working directory is not treated as NS-SIM provenance merely because it happens to be another Git repository.

## Example and verification boundary

[`examples/phase1-periodic-vortex.json`](../examples/phase1-periodic-vortex.json) is an executable Phase 1 experiment contract. The example file by itself is a deterministic runtime exercise, not numerical-verification evidence.

Separate CI tests now compare the canonical solver against a discrete shear-wave diffusion identity and perform a Taylor–Green analytic refinement check. Those checks provide minimum Phase 1 numerical-verification evidence while the broader Phase 2 benchmark/refinement programme remains future work.
