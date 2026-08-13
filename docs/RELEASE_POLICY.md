# Release Policy

## Pre-alpha

Before the first stable release, interfaces and numerical contracts may change. Releases should still identify exact source revisions and known limitations so experimental results remain interpretable later.

## Release classes

- **Development snapshot:** convenient checkpoint; may not have complete archival validation.
- **Research release:** versioned scientific and reproducibility contracts with documented benchmark evidence.
- **Stable release:** backward-compatibility expectations are explicitly stated and archival materials are complete for supported reference workflows.

## Minimum research-release evidence

A research release should include:

- tagged source revision;
- changelog;
- scientific contract and solver/discretization documentation;
- experiment/schema versions;
- environment or container specification;
- automated test result;
- validation report for supported canonical cases;
- reproducibility instructions;
- known limitations;
- license;
- reference receipts/hashes where archival claims depend on them.

## Semantic versioning

Semantic versioning may be used for software interfaces, but scientific-contract changes must be called out explicitly even when ordinary API compatibility would permit a smaller version bump.

## Archival releases

When a release is deposited to an archive such as Zenodo, the archive should identify the exact Git tag and commit, include or reference the source artifact, and preserve sufficient validation/reproducibility material to understand the claimed result without relying on a moving branch.
