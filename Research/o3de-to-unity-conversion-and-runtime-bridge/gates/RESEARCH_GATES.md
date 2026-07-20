# Research Gates

Baseline: `92aa29960bab92d646c464ae48b8cf09d881a436`, observed 20 July 2026.

These gates govern the quality and classification of research records only. Passing any research gate grants
no implementation, installation, execution, inspection, deployment, runtime, save, licensing, or publication
authority. The separately amended normative design—not this research archive—authorises the narrow Core-only
Gate 0 precursor before Phase 9.

## R0 — Intake integrity

Required:

- preserve the supplied input without alteration;
- record its relative path, byte fingerprint, intake date, and origin description;
- identify inaccessible, private, or conversation-local citations;
- separate the preserved input from later summaries and corrections.

Current result: the supplied report is preserved below `inputs/` with SHA-256
`b17850a12efe97dbd92a8bdf9cfcd155204105c49e230c51cf9b10aceba9c048`. Its `turn...` citations are explicitly
non-durable.

## R1 — Durable sourcing

Required for each claim intended to influence a decision:

- one stable claim ID;
- a direct official source where available;
- exact product version, package version, repository revision, or documentation version;
- retrieval or observation date;
- a scoped statement of what the source supports and what it does not support;
- a repository path plus full commit ID for local observations.

A search-result summary, opaque citation token, mutable display name, community statement without a direct
locator, or unattributed excerpt does not pass R1.

## R2 — Repository reconciliation

Required:

- compare the claim with `README.md`, `ROADMAP.md`, accepted architecture, the editor-toolchain design, current
  Core/Framework contracts, and `ExternalToolchain` behavior at the baseline commit;
- classify it as aligned, a bounded refinement, contradicted, stale, or outside the current boundary;
- retain contradictions in `../CLAIM_REGISTER.md`;
- avoid treating a proposed design document as implemented behavior.

R2 cannot change normative repository policy. A contradiction is resolved only by a separately reviewed
repository change.

## R3 — Authority-lane classification

Every claim or experiment must belong to exactly one primary lane:

1. pure research/source collection;
2. Core contract and deterministic validation;
3. Framework persistence, staging, and evidence orchestration;
4. thin O3DE Editor presentation;
5. generic external-tool discovery;
6. generic process supervision;
7. Blender authoring provider;
8. Unity Editor test-project interchange;
9. FoA runtime-profile diagnostics;
10. FoA runtime adapter/build/deployment/execution;
11. save or persistence mutation.

An outer envelope may bind artifacts from multiple lanes, but it cannot collapse their permissions. Unity
Editor interchange does not inherit FoA runtime authority. Generic host cleanup does not inherit game rollback
authority.

## R4 — Experiment readiness

Before an experiment can be proposed to its implementation gate, its research record must name:

- hypothesis and explicit non-goals;
- exact provider, tool, schema, configuration, fixture, platform, and version identities;
- synthetic or legally redistributable inputs;
- read and write roots;
- process, network, dependency, and import-code behavior;
- expected outputs and canonical comparison method;
- failure, cancellation, cleanup, and retry behavior;
- privacy, redaction, licence, attribution, and retention decisions;
- negative cases and evidence returned;
- the normative implementation gate that would authorize execution.

R4 means the experiment is reviewable. It does not mean it may run.

## R5 — Promotion candidate

A research conclusion may be proposed for normative design review only when:

- all material claims pass R1 and R2;
- unresolved unknowns and adverse evidence remain visible;
- exact ownership and gate placement are stated;
- no implementation or compatibility claim exceeds fixture evidence;
- the proposal includes schema/version, migration or rejection, security, legal, test, documentation, and
  rollback consequences;
- the proposal does not exceed the already authorised Gate 0 boundary or bypass the Phase 9 prerequisite for
  Gates 1 and later.

Promotion creates a review candidate, not an accepted decision. The preserved input and claim history remain
unchanged.
