# Remote Compute Policy

NS-SIM is intended to support remote GPU execution, including rented GPU infrastructure such as Vast.ai, after the local reference and validation paths are stable.

## Principle

Remote execution must be **reproducible packaging plus untrusted execution**, not `copy the working directory to a machine and hope`.

## Planned job bundle

A remote job should be derivable from a bounded bundle containing:

- exact source revision or immutable source artifact;
- normalized experiment definition;
- pinned container/runtime specification;
- required non-secret input data with hashes;
- backend request;
- resource limits where applicable.

Secrets must be injected separately.

## Returned artifacts

Expected returned artifacts include receipts, canonical checkpoints/results, diagnostics, logs stripped of secrets, validation summaries, and hashes. Local verification should check returned hashes before archival or comparison.

## Provenance

Remote provenance should identify relevant hardware/software details while keeping scheduler, provider billing, and host metadata separate from the physical experiment identity unless they change numerical semantics.

## Reproducibility caveat

A rented GPU with the same marketing model is not automatically an identical numerical environment. Driver, firmware, CUDA libraries, compiler/runtime, clocks, ECC behavior, and host configuration may differ. Claims must use the reproducibility classes defined in `docs/DETERMINISM.md`.

## Data minimization

Remote jobs should upload only declared experiment inputs. Repository secrets, unrelated home-directory files, SSH material, browser data, and unrelated datasets must never be included in job bundles.
