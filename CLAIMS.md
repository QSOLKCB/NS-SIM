# Claims Policy

NS-SIM uses conservative scientific language. Repository documentation, release notes, demos, plots, audio, and benchmark summaries must distinguish implemented behavior from planned behavior, numerical verification from physical validation, and numerical evidence from mathematical proof.

## Allowed claim classes

Claims may describe:

- the equations and numerical scheme actually implemented;
- deterministic configuration or serialization when tested;
- bitwise reproducibility within a precisely declared environment when demonstrated;
- cross-backend numerical agreement under a named metric and tolerance;
- numerical verification against a named analytic, manufactured, or numerical benchmark reference;
- measured convergence behavior for documented grids/timesteps;
- physical validation against identified experimental or observational evidence when uncertainty, mapping, metric, acceptance criteria, regime, and scope are stated;
- provenance and hash verification of archived artifacts.

## Claims requiring qualification

Terms such as `deterministic`, `reproducible`, `verified`, `validated`, `canonical`, `converged`, `stable`, `accurate`, and `GPU-equivalent` must identify the applicable contract, environment, metric, or evidence when ambiguity could materially change meaning.

`Verified` refers to numerical verification unless another kind of verification is named. `Validated` or `physically validated` must not be inferred from analytic solutions, refinement studies, numerical benchmark agreement, solver residuals, or backend-reference agreement alone.

## Prohibited overclaims

Do not claim or imply that:

- a finite numerical simulation is an exact continuum solution;
- NS-SIM resolves the Navier–Stokes existence-and-smoothness Millennium Prize problem;
- matching visualizations establish matching states;
- cross-GPU results are bitwise identical without direct verification;
- one benchmark verifies or validates all Reynolds numbers, geometries, discretizations, or flow regimes;
- analytic or numerical benchmark agreement alone constitutes physical validation;
- formal verification of software properties automatically proves physical fidelity;
- a run is reproducible when the provenance required for its claimed reproducibility class is missing.

R0 is an exception to the last point only in the precise sense that R0 classifies a normalized semantic experiment contract before execution and therefore does not require execution provenance.

## Planned versus implemented

Future architecture must be labeled `planned`, `target`, or equivalent until code and tests exist. README examples may illustrate a planned interface but must not be presented as commands that currently work unless they do.
