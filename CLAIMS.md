# Claims Policy

NS-SIM uses conservative scientific language. Repository documentation, release notes, demos, plots, audio, and benchmark summaries must distinguish implemented behavior from planned behavior and numerical evidence from mathematical proof.

## Allowed claim classes

Claims may describe:

- the equations and numerical scheme actually implemented;
- deterministic configuration or serialization when tested;
- bitwise reproducibility within a precisely declared environment when demonstrated;
- cross-backend numerical agreement under a named metric and tolerance;
- comparison against a named analytic or benchmark reference;
- measured convergence behavior for documented grids/timesteps;
- provenance and hash verification of archived artifacts.

## Claims requiring qualification

Terms such as `deterministic`, `reproducible`, `validated`, `canonical`, `converged`, `stable`, `accurate`, and `GPU-equivalent` must identify the applicable contract, environment, metric, or evidence when ambiguity could materially change meaning.

## Prohibited overclaims

Do not claim or imply that:

- a finite numerical simulation is an exact continuum solution;
- NS-SIM resolves the Navier–Stokes existence-and-smoothness Millennium Prize problem;
- matching visualizations establish matching states;
- cross-GPU results are bitwise identical without direct verification;
- one benchmark validates all Reynolds numbers, geometries, discretizations, or flow regimes;
- formal verification of software properties automatically proves physical fidelity;
- a run is reproducible when required inputs, environment, or provenance are missing.

## Planned versus implemented

Future architecture must be labeled `planned`, `target`, or equivalent until code and tests exist. README examples may illustrate a planned interface but must not be presented as commands that currently work unless they do.
