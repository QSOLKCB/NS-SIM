# Release Policy

## Pre-alpha

Before the first stable release, interfaces and numerical contracts may change. Releases should still identify exact source revisions and known limitations so experimental results remain interpretable later.

## Release classes

- **Development snapshot:** convenient checkpoint; may not have complete archival numerical-verification evidence and makes no implicit physical-validation claim.
- **Research release:** versioned scientific and reproducibility contracts with documented numerical-verification evidence for supported workflows.
- **Stable release:** backward-compatibility expectations are explicitly stated and archival materials are complete for supported reference workflows. Physical validation is included only where a positive validation claim is explicitly made and supported.

## Minimum research-release evidence

A research release should include:

- tagged source revision;
- changelog;
- scientific contract and solver/discretization documentation;
- experiment/schema versions;
- environment or container specification;
- automated test result;
- numerical-verification report for supported canonical cases;
- explicit physical-validation status;
- physical-validation report when `validation_status` is positive rather than `not_claimed`;
- reproducibility instructions;
- known limitations;
- license;
- reference receipts/hashes where archival claims depend on them.

Analytic solutions, refinement studies, numerical benchmarks, residual checks, and backend-vs-reference comparisons belong in the numerical-verification report. They must not be presented as physical validation without qualifying experimental or observational evidence.

## Stable-release evidence

A stable release must retain the research-release evidence above and additionally state the supported compatibility surface and any frozen canonical reference profiles. A stable release is not required to claim physical validation; if it does not, `validation_status` must say so explicitly.

## Semantic versioning

Semantic versioning may be used for software interfaces, but scientific-contract changes must be called out explicitly even when ordinary API compatibility would permit a smaller version bump.

## Archival releases

When a release is deposited to an archive such as Zenodo, the archive should identify the exact Git tag and commit, include or reference the source artifact, and preserve sufficient verification/reproducibility material to understand the claimed numerical result without relying on a moving branch. If physical validation is claimed, the archive must additionally preserve or identify the validation reference, uncertainty information, comparison metric, acceptance criterion, and stated scope of the claim.
