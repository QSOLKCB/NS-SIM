# Contributing to NS-SIM

NS-SIM is currently a private pre-alpha research project. Contributions should preserve the separation between scientific definition, numerical implementation, acceleration, validation, and derived presentation.

## Change expectations

A contribution should be scoped to one coherent concern and should explain:

- what changes;
- why the change is necessary;
- which scientific or software contracts are affected;
- what validation or regression evidence supports it;
- whether reproducibility behavior changes;
- whether receipts, schemas, or archived outputs change.

## Scientific changes

Changes to governing equations, discretization, initial/boundary conditions, pressure formulation, timestep logic, numerical stabilization, filtering, precision, convergence criteria, or canonical serialization require corresponding documentation and validation changes.

Do not hide a scientific-contract change inside a performance optimization.

## Backend changes

Accelerated implementations must be compared with the canonical reference using declared metrics and tolerances. Architecture-specific behavior must be documented, particularly reductions, fused operations, precision modes, non-deterministic kernels, and library algorithms that can alter reproducibility.

## Tests

Prefer small deterministic cases that are practical in continuous integration. Large GPU experiments may supplement but must not replace reference tests.

When available, contributions should run:

1. unit and schema tests;
2. canonical CPU regression cases;
3. analytic/benchmark validation relevant to the change;
4. backend-vs-reference comparison for accelerated code;
5. documentation consistency checks.

## Pull requests

Pull requests should remain reviewable, avoid unrelated formatting churn, and state known limitations. Failed or unavailable checks must be reported rather than described as passing.

## AI-assisted contributions

AI agents must follow `AGENTS.md`. Agent-only documentation must remain machine-readable according to that contract. Human-facing scientific documentation may remain Markdown.
