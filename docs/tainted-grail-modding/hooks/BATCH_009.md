# Semantic Hook Batch 009 — Durable Proofs and Intent Recovery

Batch 009 hardens the project-owned offline repair package with journal compaction proofs, explicit lock-abandonment review records, recoverable multi-file publication intents, cancellation/recovery composition matrices, bounded API v2 generation gaps, and reproducible CI policy receipts.

It does not inspect or load game or mod assemblies, execute game code, discover installations, admit runtime evidence, or promote hooks.

## Base

- Batch 008 merge commit: `3ab2f43ace96b6fb1b34498ebf1ba37717d6e93a`.
- Package authority: engine-neutral synthetic validation only.
- Runtime authority: none.
- Promotion authority: none.

## Journal compaction and checkpoint proofs

`semantic_repair.compaction` adds lease-owned compaction for journals whose transactions are all terminal.

A journal may be compacted only when:

- the caller owns the exact active journal lease;
- the journal contains no torn final record;
- every transaction ends in `committed`, `rolled-back`, `cancelled`, `intent-committed`, `intent-rolled-back`, or an existing compacted checkpoint;
- each transaction has either no ownership metadata or one consistent owner/generation identity;
- the proof path is distinct from the journal path.

Compaction replaces the history with one canonical `compacted-checkpoint` record. The proof binds:

- original journal SHA-256;
- original record count;
- original final record hash;
- sorted terminal transaction summaries;
- checkpoint payload SHA-256;
- compacted journal SHA-256;
- compacted checkpoint record hash.

The journal and proof are restored to their previous bytes if publication or verification fails. Proof verification rejects altered compacted bytes, payloads, record hashes, source hashes, terminal summaries, or authority fields.

A compaction proof is not a game save, runtime log, diagnostic artifact, evidence receipt, or promotion decision.

## Lock-abandonment review records

`semantic_repair.abandonment` records an observed stranded lease without deleting, replacing, expiring, or stealing it.

The canonical review contains:

- resource ID;
- observed owner ID;
- observed generation;
- SHA-256 of the exact lock bytes;
- SHA-256 of the exact generation-state bytes;
- reviewer ID;
- review reason;
- recommendation `manual-review-no-lock-theft`;
- `runtime_authority: none`;
- `promotion: none`.

A review can be created only for an active lock whose lease generation agrees with the generation state. Recording the review leaves the lock active.

## Multi-file publication intent journals

`semantic_repair.publication_intent` adds a lease-owned intent protocol for normalized relative files below one project-owned root.

The journal phases are:

```text
intent-prepared
→ intent-file-published
→ intent-committed
```

Recovery may terminate with:

```text
intent-rolled-back
```

The prepared intent records, for every sorted target:

- normalized relative path;
- whether previous bytes existed;
- base64-encoded previous bytes when present;
- previous SHA-256;
- intended SHA-256;
- intended byte count.

Every file replacement is followed by a durable progress record. A synthetic crash may therefore leave a partially published set with enough information for deterministic rollback.

Recovery fails closed when:

- the intent or prepared record is absent;
- the recovering owner differs from the intent owner;
- the journal has a torn tail;
- a target contains bytes matching neither its previous nor intended hash;
- the latest phase is unknown.

No publication target may be absolute, contain dot segments, escape the configured root, or appear twice.

## Cancellation and recovery composition matrix

The committed golden matrix covers:

```text
cancel-requested | cancelling | cancelled
×
complete journal | torn final record
```

Expected plans are:

- `cancel-requested` or `cancelling` → `rollback`;
- `cancelled` → `none`;
- a torn tail always adds the first `truncate-torn-tail` action.

The six cases are serialized in deterministic order and declare no runtime or promotion authority.

## API v2 generation-gap limits

API v2 registry snapshot application now has a positive `max_generation_gap`, defaulting to 64.

Consumers continue to reject older and conflicting same-generation snapshots. They additionally reject a newer snapshot when:

```text
incoming generation - current generation > max_generation_gap
```

The committed fixtures prove:

- generation 2 → generation 4 succeeds with an explicit gap limit of 2;
- generation 2 → generation 67 fails with the default limit of 64;
- a non-positive configured limit fails closed.

All fixture owners, commands, versions and tokens are synthetic.

## Reproducible CI policy receipts

`semantic_repair.ci_policy` now evaluates the workflow into canonical receipt bytes containing:

- policy version;
- exact workflow SHA-256;
- valid or invalid status;
- ordered policy violations;
- `runtime_authority: none`;
- `promotion: none`.

The committed golden receipt is bound to the exact workflow bytes. A workflow edit must either preserve the identical receipt or intentionally update the golden after passing the negative policy.

Policy evaluation continues to reject:

- permissions other than exactly `contents: read`;
- persisted checkout credentials;
- secret references;
- upload, Pages, attestation, release or container-push actions;
- write permissions;
- network or package-publication commands;
- `continue-on-error: true`.

The workflow uploads no receipt or artifact. Verification occurs entirely inside the checked-out repository.

## Validation

Focused Batch 009 validation:

```text
13 tests passed
0 failed
0 external Python dependencies
```

Coverage includes:

- terminal compaction and checkpoint verification;
- non-terminal compaction refusal;
- tampered-proof rejection;
- canonical lock-abandonment review;
- absent-lock review refusal;
- successful multi-file intent commit;
- crash recovery to exact previous bytes;
- unknown third-state manual-review refusal;
- serialized API generation-gap acceptance and rejection;
- invalid gap-limit rejection;
- byte-identical CI policy receipts;
- six-case cancellation/recovery golden equivalence.

The hosted Python 3.11–3.13 workflow remains the authority for the complete repository offline suite.

## Governance result

- hook promotions: 0;
- evidence promotions: 0;
- runtime adapters: 0;
- game or loader assembly inspection: 0;
- Batch 004 prohibitions changed: 0;
- runtime diagnostic authority: 0;
- runtime mount-conversion authority: 0;
- Avalon Companions runtime authority: 0;
- automatic lock theft authority: 0;
- artifact publication authority: 0.

Passing Batch 009 proves only deterministic behavior of project-owned offline models.

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

Semantic Hook Batch 010 should add interrupted-compaction matrices, checkpoint-chain rotation, intent-journal checkpoint integration, reviewer-quorum records for abandonment decisions, bounded publication backup sizes, API snapshot replay-window receipts, and cross-version CI receipt fixtures. It must preserve the same no-runtime and no-promotion boundary.
