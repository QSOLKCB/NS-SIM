# Validation Policy

Validation answers a narrower question than verification: whether a numerical implementation behaves consistently with specified reference solutions, benchmark results, conservation/constraint expectations, and convergence behavior within declared conditions.

## Baseline suite

### Taylor–Green vortex

Use an analytic or well-defined decaying-vortex setup to test spatial/time error, viscous decay, symmetry where applicable, and reproducibility.

### Poiseuille/channel flow

Use the analytic laminar profile to test forcing/pressure-gradient treatment, no-slip boundaries, steady-state error, and convergence.

### Lid-driven cavity

Use a documented benchmark reference at selected Reynolds numbers to test walls, recirculation structure, and velocity profiles.

### Cylinder wake

Use a documented geometry and Reynolds-number regime to test obstacle boundaries, wake behavior, force coefficients where implemented, and vortex-shedding frequency/Strouhal behavior.

## Always-on numerical diagnostics

Where applicable, every canonical run should collect:

- finite-state check;
- discrete divergence norm;
- pressure/linear solver residual and iteration count;
- timestep/CFL diagnostic;
- kinetic energy;
- case-specific conservation or budget quantities.

## Convergence evidence

A single visually plausible grid is not convergence evidence. Numerical-convergence claims should compare a declared sequence of spatial and/or temporal resolutions and report the measured error or observable trend.

## Backend validation

GPU and other accelerated implementations are validated against the canonical reference under explicit metrics and tolerances. Performance gains do not waive scientific comparison.

## Regression artifacts

Small canonical benchmark cases should be stable enough for automated regression. Large research runs may be archived separately but should not be the sole gate for correctness.
