# NS-SIM Architecture

## Architectural objective

NS-SIM separates the **scientific contract** from the **execution backend**. The same versioned experiment definition must remain interpretable without allowing an optimization backend to silently redefine modeled physics or numerical semantics.

## Implemented Phase 1 path

```text
JSON experiment
      |
      v
strict schema/semantic normalization
      |
      +--> exact-float identity document --> SHA-256 experiment hash
      |
      v
canonical 2D model + finite-difference contract
      |
      v
cpu-reference-v1 / NumPy
      |
      +--> environment provenance
      |
      v
u,v,p canonical state
      |
      +--> .nss checkpoints + SHA-256
      +--> diagnostics
      |
      v
receipt.json
```

Phase 1 freezes a narrow canonical layer: uniform cell-centered periodic 2D grids, centered advection/diffusion, backward-divergence/forward-gradient projection, forward Euler, deterministic periodic Jacobi pressure solve, float64 state, and `ns-sim-state/1` serialization.

The runtime layer owns experiment parsing/normalization, identities, checkpoint scheduling, diagnostics, provenance, receipts, and repeat-execution comparison. Phase 1 implements only `cpu-reference-v1`; future accelerated backends depend on canonical semantics rather than redefining them.

Software regressions and invariant checks establish runtime behavior. Phase 2 numerical verification will compare against analytic/benchmark references and refinement expectations. Physical validation remains a separate evidence activity requiring experimental/observational references and uncertainty/acceptance criteria.

Derived visualization/sonification remains downstream and non-authoritative.

## Canonical state

Phase 1 canonical state is the float64 `u`, `v`, and gauge-fixed `p` fields plus step/time metadata bound to the experiment hash. `ns-sim-state/1` serializes these fields uncompressed in a declared order and byte order before hashing.

Derived caches, rendering buffers, audio buffers, UI state, wall-clock timing, and non-semantic logging are excluded from canonical state.

## Failure philosophy

NS-SIM fails closed on malformed or scientifically ambiguous experiments. Unknown fields, unsupported combinations, non-finite state, pressure non-convergence, or violated declared timestep limits produce explicit failure rather than a plausible-looking success artifact.
