# Semantic Hook Batch 011 — Archive, Dependency and Migration Proofs

Batch 011 extends the project-owned offline repair package with deterministic archive provenance, cumulative resource bounds, dependency proofs, immutable decision lifecycle records, replay sequences and workflow-receipt migration fixtures. It does not inspect or load game or mod assemblies, execute game code, admit runtime evidence, or promote hooks.

## Base

- Batch 010 merge commit: `1e5034212694031e7f4bb3f38a2ffb09eb6cd030`.
- Package authority: engine-neutral synthetic validation only.
- Runtime authority: none.
- Promotion authority: none.

## Checkpoint-chain archive manifests

`semantic_repair.checkpoint_archive` adds canonical manifests for chains replaced by a Batch 010 rotation anchor.

Each manifest binds:

- archive ID and contiguous archive index;
- one safe archive file name;
- complete archived-chain SHA-256;
- archived entry count;
- first and final archived entry SHA-256;
- active rotation-anchor entry SHA-256;
- previous archive-manifest SHA-256.

Manifest construction validates the complete archived JSONL chain and requires the active chain to contain exactly one `rotation-anchor`. The anchor must bind the archived bytes, entry count and final entry hash exactly.

A manifest does not delete an archive, rotate a chain or grant runtime continuity. It is a synthetic provenance document only.

## Repeated-compaction backup quotas

`semantic_repair.compaction_quota` adds a durable cumulative quota ledger for repeated compaction preparation.

The ledger records:

- immutable configured limits;
- unique operation IDs;
- contiguous operation indices;
- backup bytes reserved per operation;
- cumulative reserved backup bytes;
- a length-delimited SHA-256 over every backup part.

Default limits are:

```text
operations:       16
total bytes:      4,194,304
single operation: 1,048,576
```

An operation fails before reservation when it would exceed the single-operation, total-byte or operation-count limit. Duplicate operation IDs and changed limits fail closed.

The quota ledger does not capture runtime files or authorize compaction. It accounts only for caller-supplied synthetic backup bytes.

## Publication-intent dependency graphs

`semantic_repair.intent_dependencies` adds deterministic directed acyclic graph proofs for synthetic publication intents.

Nodes contain:

- intent ID;
- current synthetic intent status;
- sorted unique dependency IDs.

Graph construction rejects:

- duplicate intent IDs;
- missing dependency nodes;
- self-dependencies;
- duplicate or unsorted dependencies;
- unsupported statuses;
- dependency cycles.

The graph publishes a deterministic topological order. An `intent-prepared` node is runnable only when every dependency is `intent-committed`. A rolled-back or still-prepared dependency blocks the dependent node.

The graph does not execute an intent or publish any file.

## Quorum revocation and supersession

`semantic_repair.abandonment_lifecycle` adds immutable lifecycle records above Batch 010 abandonment decisions.

A revocation binds:

- the revoked decision SHA-256;
- exact resource, owner and generation observation;
- distinct sorted reviewers meeting the original quorum;
- a non-empty reason;
- effect `decision-revoked-lock-retained`.

A supersession binds:

- previous decision SHA-256;
- revocation SHA-256;
- distinct replacement decision SHA-256;
- resource ID;
- previous and replacement generations;
- distinct sorted reviewers meeting both quorum requirements;
- effect `decision-superseded-lock-retained`.

A supersession cannot reference another decision's revocation, cross resources, reuse the same decision or move to an older generation.

Neither record removes, expires, replaces or steals a lock.

## Replay-window sequence proofs

`semantic_repair.replay_sequence` hash-chains a sequence of Batch 010 replay-window receipts.

Every entry binds:

- monotonic sequence index;
- previous entry SHA-256;
- source receipt SHA-256;
- current and incoming generations;
- replay disposition;
- resulting generation;
- current entry SHA-256.

Generation continuity is explicit:

- `accepted` advances to the incoming generation;
- `already-current`, `same-generation-conflict`, `replayed-stale` and `replay-window-exceeded` retain the current generation;
- the next receipt must begin at the prior resulting generation.

The proof is non-mutating and creates no runtime replay authority.

## Workflow-receipt migration fixtures

`semantic_repair.ci_migration` defines a deterministic migration from policy receipt version 1 to version 2.

The migrated receipt preserves:

- exact workflow SHA-256;
- valid or invalid status;
- ordered policy violations;
- source v1 receipt SHA-256;
- authority, runtime-authority and promotion boundaries.

The migration fixture binds source policy version 1, target policy version 2, source receipt SHA-256, target receipt SHA-256, workflow SHA-256 and status.

Committed fixtures cover:

- the exact valid Batch 011 workflow;
- a synthetic invalid workflow containing both the permission-set violation and the forbidden `contents: write` token violation.

The workflow retains:

```text
permissions:
  contents: read
```

It references no secrets, installs no package, performs no network command and uploads no artifact.

## Validation

The focused Batch 011 suite passed:

```text
16 tests passed
0 failed
0 external Python dependencies
```

Coverage includes:

- archive-manifest golden and archive tamper rejection;
- cumulative quota golden, duplicate operation rejection and byte/count ceilings;
- dependency topological order, runnable/blocked classification, cycle rejection and missing-node rejection;
- abandonment revocation and supersession goldens, duplicate-reviewer rejection and cross-resource rejection;
- replay-sequence golden and generation-discontinuity rejection;
- valid and invalid workflow-receipt migrations plus tamper rejection.

Hosted workflow results are recorded separately from local synthetic validation.

## Governance result

- hook promotions: 0;
- evidence promotions: 0;
- runtime adapters: 0;
- game or loader assembly inspection: 0;
- Batch 004 prohibitions changed: 0;
- runtime diagnostic authority: 0;
- runtime mount-conversion authority: 0;
- Avalon Companions runtime authority: 0;
- automatic lock-theft authority: 0;
- artifact-publication authority: 0;
- runtime replay authority: 0;
- runtime dependency-execution authority: 0.

Passing Batch 011 proves only deterministic behavior of project-owned offline models.

## Scope

Allowed changes:

- offline Python package code;
- synthetic fixtures, goldens and tests;
- the read-only offline workflow;
- catalogue documentation.

Not changed:

- Batch 004 fixture manifests or decision register;
- hook records or verified runtime profiles;
- upstream mod source;
- game, loader or framework binaries;
- build graphs, installers, deployment, signing or publication;
- evidence status or promotion decisions.

## Next unit

Semantic Hook Batch 012 should add archive retention and tombstone manifests, quota release and compaction records, dependency-graph partial-rollback plans, quorum appeal records, replay-sequence compaction proofs, and chained workflow-receipt migration histories. It must retain the same no-runtime and no-promotion boundary.
