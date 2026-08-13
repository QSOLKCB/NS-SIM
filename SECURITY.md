# Security Policy

## Current status

NS-SIM is private pre-alpha software and has no supported production release yet. Security reports should be handled privately with the repository owner rather than disclosed in a public issue before a coordinated fix is available.

## Security boundaries

The project is expected to process experiment configurations, checkpoints, simulation outputs, GPU kernels/libraries, container images, and later remote-compute jobs. These inputs and environments must not be assumed trustworthy merely because they are part of a scientific workflow.

## Secrets

Credentials, API keys, cloud tokens, Vast.ai credentials, SSH private keys, registry tokens, and other secrets must never be:

- committed to the repository;
- embedded in experiment definitions;
- written into canonical receipts;
- included in diagnostic bundles or archived datasets.

Use environment-level or platform-native secret injection when remote execution is introduced.

## Remote compute

Remote GPU hosts should be treated as potentially untrusted execution environments. Remote workflows should eventually provide:

- pinned source revision and container/runtime identity;
- explicit upload/download boundaries;
- artifact hash verification;
- least-privilege credentials;
- no implicit upload of unrelated local files;
- sanitised logs and receipts;
- documented teardown/retention behavior.

## Input handling

Experiment and receipt schemas should reject unknown or malformed security-sensitive fields. Paths must not allow unintended traversal outside the run workspace. Archive extraction and artifact import must defend against path traversal, symlink surprises, oversized inputs, and untrusted executable content.

## Numerical failures are not security successes

A failed solver, NaN/Inf state, divergence failure, or corrupted checkpoint must produce an explicit simulation failure. Never treat an invalid numerical result as acceptable because the process exited successfully.
