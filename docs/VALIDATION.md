# Verification and Validation Policy

NS-SIM separates **numerical verification** from **physical validation**. They answer different questions and must be reported separately.

## Numerical verification

Verification asks whether the implementation solves the declared mathematical and discrete problem consistently.

Verification evidence includes, where applicable:

- analytic-solution comparison;
- manufactured-solution comparison;
- spatial and temporal refinement studies;
- conservation and constraint checks;
- solver residual and convergence checks;
- comparison with documented numerical benchmark data;
- regression against canonical reference outputs;
- accelerated-backend comparison with the canonical reference under explicit metrics and tolerances.

Passing verification supports claims about numerical implementation behavior. It does not, by itself, establish that the modeled equations faithfully represent a physical experiment.

## Physical validation

Validation asks whether the model represents a physical system adequately for a stated purpose, parameter range, geometry, and regime.

A positive physical-validation claim requires:

- an identified experimental or observational reference;
- a documented mapping between simulation quantities and measured physical quantities;
- relevant measurement and input uncertainties;
- declared comparison metrics;
- declared acceptance criteria or tolerances;
- the physical regime and scope to which the claim applies.

If those elements are absent, the project must report physical validation as `not_claimed` or equivalent rather than inferring validation from numerical verification.

## Baseline numerical-verification suite

### Taylor–Green vortex

Use an analytic or well-defined decaying-vortex setup to test spatial/time error, viscous decay, symmetry where applicable, and reproducibility.

### Poiseuille/channel flow

Use the analytic laminar profile to test forcing or pressure-gradient treatment, no-slip boundaries, steady-state error, and convergence.

### Lid-driven cavity

Use a documented numerical benchmark reference at selected Reynolds numbers to test walls, recirculation structure, and velocity profiles. This is numerical-verification evidence unless the comparison explicitly uses physical measurements with uncertainty information.

### Cylinder wake

Use a documented geometry and Reynolds-number regime to test obstacle boundaries, wake behavior, force coefficients where implemented, and vortex-shedding frequency or Strouhal behavior. Numerical benchmark comparisons are verification; comparison to physical measurements may additionally support validation when the validation requirements above are satisfied.

## Always-on numerical diagnostics

Where applicable, every canonical run should collect:

- finite-state check;
- discrete divergence norm;
- pressure/linear solver residual and iteration count;
- timestep/CFL diagnostic;
- kinetic energy;
- case-specific conservation or budget quantities.

These diagnostics are verification evidence and run-validity evidence, not standalone physical validation.

## Convergence evidence

A single visually plausible grid is not convergence evidence. Numerical-convergence claims should compare a declared sequence of spatial and/or temporal resolutions and report the measured error or observable trend.

## Backend verification

GPU and other accelerated implementations are verified against the canonical reference under explicit metrics and tolerances. Performance gains do not waive scientific comparison. Cross-backend agreement is not physical validation unless the candidate is also compared to qualifying physical evidence.

## Regression artifacts

Small canonical benchmark cases should be stable enough for automated regression. Large research runs may be archived separately but should not be the sole gate for correctness.

## Release evidence terminology

Release artifacts must distinguish the following fields or equivalent concepts:

```text
verification_status
verification_report
validation_status
validation_report
```

A `verification_report` is required for research releases that claim supported numerical workflows. `validation_status` may be `not_claimed`. A `validation_report` is required only when the release makes a positive physical-validation claim.
