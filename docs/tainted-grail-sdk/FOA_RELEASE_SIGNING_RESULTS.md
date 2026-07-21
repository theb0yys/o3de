# FoA Release-Signing Result Evidence

Status: implemented and hardened; exact-head host build, compiled execution, and Windows UI evidence remain pending.

## Purpose

This contract preserves a release-signing result supplied by a separately reviewed external signer and binds it
to one exact accepted release-assembly/checksum result.

It exists so later review can distinguish:

- the exact release artifact and accepted assembly result presented for signing;
- the exact archive identity, path, format, size, and reported SHA-256 fingerprint;
- the approved external-signing intent and identity metadata;
- the separately reviewed signer tool and its declared capabilities;
- whether signing was not attempted, succeeded, failed, or was skipped;
- which signature artifacts, failures, and supplied diagnostic references were reported;
- structurally valid supplied evidence from signing, verification, trust, or release authority performed by the SDK.

The SDK does not perform signing. It validates bounded supplied metadata and returns candidate evidence by value.

## Exact inputs and reconstructed upstream evidence

`AdapterReleaseSigningEvidenceService::BuildEvidenceReturn` consumes:

1. one exact ready `AdapterReleaseArtifactEnvelope`;
2. one exact `AdapterReleaseAssemblyResultEnvelope`;
3. the supplied `AdapterReleaseAssemblyEvidenceReturn` for that assembly result;
4. one separately supplied `AdapterReleaseSigningResultEnvelope`.

The service does not trust the caller-supplied assembly-evidence return merely because its status says accepted.
It rebuilds the deterministic assembly evidence return from the exact artifact and assembly result, then compares:

- status, accepted state, and contract-valid state;
- all identities and fingerprints;
- observation, failure, diagnostic, source-document, and evidence-record counts;
- deterministic source and evidence documents;
- deterministic issues;
- every file-read, hashing, assembly, signing, upload, publication, launch, adapter, and deployment flag.

Any mutated count, issue, candidate document, or no-operation flag causes
`assembly_result_not_accepted`. The assembly result must also report one successful supplied archive before signing
evidence can be accepted.

## Exact binding

The signing result must reproduce the exact accepted upstream state:

- release-artifact identity and canonical SHA-256 fingerprint;
- assembly-result identity and fingerprint;
- archive identity;
- safe package-relative archive reference;
- archive format;
- archive byte size;
- archive lowercase SHA-256 fingerprint;
- reconciliation identity;
- package-preview identity;
- manifest identity and fingerprint;
- pack identity and semantic version;
- profile identity;
- game version;
- branch;
- runtime target;
- signing-intent identity;
- signing-intent decision;
- signing identity kind;
- signer identity;
- identity locator;
- identity fingerprint.

Any canonical-artifact drift, assembly-result drift, archive drift, release-context drift, or signing-intent drift
fails closed.

## Closed enum values

Every contract enum is closed at the validation boundary. Out-of-range numeric values fail closed for:

- signing-intent decision and identity kind;
- signer-review decision and capabilities;
- signing outcome;
- signature-artifact kind;
- failure kind;
- diagnostic kind.

`unknown` remains a valid, representable external failure kind. It means the external signer reported a failure
whose specific typed cause is not known. It is not used as a fallback for an out-of-range numeric enum value.

## Signing-intent boundary

Only a ready artifact whose reviewed signing-intent decision is `sign_externally` can produce accepted
release-signing evidence.

An artifact whose decision is `unsigned` returns `signing_not_requested`. The supplied result cannot add a
signer, identity kind, locator, or fingerprint to an unsigned artifact and cannot select identity metadata
different from the approved external-signing intent.

Identity locators and fingerprints remain reviewed metadata. The SDK does not resolve the locator, inspect a
key store, load a key or certificate, authenticate a signer, or contact an identity or transparency service.

## Reviewed external signer

The supplied signer review preserves:

- stable review identity;
- stable signer-tool identity;
- strict semantic signer-tool version;
- lowercase SHA-256 signer-tool fingerprint;
- `unknown`, `accepted`, or `rejected` decision;
- named reviewer;
- unique evidence identities;
- exact UTC review timestamp;
- bounded public notes;
- declared `archive_signing` capability;
- declared `signature_artifact_fingerprint` capability.

Acceptance requires an `accepted`, evidence-backed, capability-complete review containing only known capability
values. The SDK does not discover, install, invoke, authenticate, or trust the signer tool.

## Signing outcomes and chronology

The result preserves one typed outcome:

- `not_attempted`;
- `succeeded`;
- `failed`;
- `skipped`.

Outcome metadata also preserves attempted state, completion time, signature artifacts, top-level failure
identities, and diagnostic identities.

A `succeeded` result must report an attempt, a valid completion timestamp, at least one valid signature
artifact, and no failure reference.

A `failed` result must report an attempt, a valid completion timestamp, and at least one exact supplied
failure. A structurally valid failed result remains accepted as adverse evidence; contract acceptance does not
rewrite failure as success.

A `not_attempted` or `skipped` result cannot claim completed signature artifacts. The complete chronology must
also satisfy:

```text
archive completion <= signature-artifact creation <= signing completion <= capture
signer review       <= signature-artifact creation
signer review       <= signing completion
```

A signature cannot predate the archive it signs or the review that accepted the supplied signer metadata.

## Signature artifacts

Each supplied signature artifact preserves:

- stable signature-artifact identity;
- known typed artifact kind;
- safe package-relative reference;
- bounded public media type;
- positive reported byte size;
- lowercase SHA-256 fingerprint;
- UTC creation timestamp;
- exact archive identity and fingerprint;
- unique diagnostic-reference identities.

The contract supports detached signatures, signature bundles, certificate bundles, transparency receipts,
attestations, and reviewed `other` evidence without assuming one vendor or identity technology.

Signature-artifact identities and Windows case-folded path identities must be unique. The SDK does not open,
parse, hash, verify, copy, write, register, persist, or publish a signature artifact.

## Failures and supplied diagnostics

A supplied signing failure preserves:

- stable failure identity;
- known typed failure kind, including representable `unknown`;
- bounded public code and message;
- optional signature-artifact binding;
- unique diagnostic-reference identities;
- retryable state.

A supplied diagnostic reference preserves:

- stable diagnostic identity;
- known diagnostic kind;
- safe package-relative reference;
- lowercase SHA-256 fingerprint;
- unique optional signature-artifact bindings.

The service rejects absolute or drive-qualified paths, traversal, malformed fingerprints, malformed
timestamps, duplicate identities, Windows case-folded path collisions, orphan references, and
non-reciprocal artifact/diagnostic bindings. Referenced diagnostic content is never opened or inspected.
Because its media type is not supplied or inspected, diagnostic source documents use
`application/octet-stream`; the SDK does not invent `text/plain`.

## Privacy and public-evidence checks

Externally supplied public text is bounded and rejects control bytes, private absolute path shapes,
credential-bearing URLs, authorization values, bearer tokens, passwords, PIN markers, API-key markers,
client secrets, access keys, and private-key markers.

These checks apply to reviewer metadata, notes, identity locators, media types, failure codes, and failure
messages before candidate evidence is produced. The boundary is deliberately conservative; it is not a general
secret-scanning guarantee and must not be used to justify placing credentials in the contract.

## Fixed collection limits

Validation rejects oversized metadata before nested reference analysis or candidate-evidence construction.
Contract maxima are:

- 128 transient registry envelopes;
- 128 signature artifacts per envelope;
- 128 failures per envelope;
- 128 diagnostics per envelope;
- 64 nested references per artifact, failure, or diagnostic;
- 8 signer capabilities;
- 64 signer-review evidence IDs;
- 256 KiB aggregate text per envelope.

The fixed limits prevent unbounded registry growth, quadratic validation over attacker-controlled collections,
and disproportionate Editor allocation.

## Reported and authoritative fingerprints

`m_resultFingerprint` is preserved as the **reported result fingerprint**. The SDK cannot prove that declaration
because the external contract does not provide caller-independent canonical signing-result bytes.

For candidate source/evidence identity, Core builds deterministic canonical JSON from the complete bounded
signing-result metadata, excluding the reported fingerprint, and calculates an **SDK-derived authority
fingerprint**. Changing only the reported result fingerprint therefore cannot change the candidate source
identity. Both values remain visible so reviewers can distinguish the external claim from the SDK-derived
metadata identity.

## Deterministic status precedence

The fail-closed status order is:

1. `assembly_result_not_accepted`;
2. `signing_not_requested`;
3. `signer_unreviewed`;
4. `assembly_binding_mismatch`;
5. `signing_intent_binding_mismatch`;
6. `envelope_invalid`;
7. `signing_outcome_mismatch`;
8. `signature_artifact_binding_mismatch`;
9. `failure_diagnostic_binding_mismatch`;
10. `accepted`.

`accepted` means only that the separately supplied metadata is structurally valid, bounded, public-safe under
the contract checks, and exactly bound. It does not mean that the SDK signed the archive, verified a signature,
authenticated the signer, established cryptographic trust, approved the release, or authorised publication.

Issues are sorted deterministically by code, signature-artifact identity, failure identity, diagnostic identity,
and message.

## Candidate evidence

A contract-valid result may return candidate source/evidence documents by value for:

- release-artifact binding;
- accepted assembly-result and archive binding;
- signer review;
- signing-intent binding;
- signing attempt and outcome;
- every supplied signature artifact;
- every supplied failure;
- every supplied diagnostic reference.

Candidate evidence is not automatically registered, persisted, promoted, validated, permitted, trusted,
uploaded, or published.

Equivalent valid inputs produce deterministic authority fingerprints, source identities, evidence identities,
and evidence ordering. Validation does not mutate the artifact, assembly result, assembly evidence return,
signing result, or registries.

## Transient registry

`AdapterReleaseSigningResultRegistry` stores supplied result envelopes in memory only.

Before copying an envelope, the registry enforces collection limits, known enum values, public-text checks,
safe archive/signature/diagnostic references, stable unique identities, Windows case-folded path uniqueness,
fingerprint shape, timestamps, and semantic signer-tool versioning. It rejects duplicate result identities and
refuses a 129th envelope. It preserves insertion order and is cleared when the dedicated Editor pane lifecycle
component deactivates.

No durable schema, migration, or persisted signing-result file is introduced.

## Read-only Editor pane

**Tainted Grail Release Signing Results** displays:

- signing-result identity and reported fingerprint;
- `contract status=not evaluated` for registry-only rows;
- an explicit statement that the SDK-derived authority fingerprint is unavailable in the registry-only view;
- release-artifact and assembly-result bindings;
- archive identity, path, format, byte size, and fingerprint;
- supplied signer review, tool version/fingerprint, reviewer, timestamp, capabilities, and evidence IDs;
- supplied signing identity kind, signer, locator, and fingerprint;
- attempted state, outcome, completion, and capture time;
- signature artifacts and exact archive bindings;
- failures and retryable state;
- **Supplied diagnostics — not evaluated**;
- reconciliation, package, manifest, pack, profile, game, branch, and runtime context;
- explicit SDK no-operation safety state.

The pane never calls registry-only diagnostics safe. It caps display at 1,024 rows, caps each cell at 4,096
characters, and reports display truncation. These presentation caps are separate from the stricter contract
limits and protect against future registry implementation changes.

The pane is non-editable and provides no registration, review-authoring, file-open, key-load, credential,
identity-resolution, cryptographic, copy/write, sign, verify, upload, publish, launch, adapter, deployment, or
save action.

The pane deliberately does not evaluate contract acceptance because registry entries do not contain all exact
upstream inputs required by `AdapterReleaseSigningEvidenceService`.

## Security, privacy, and legal boundary

The result contract must not carry private-key bytes, passwords, tokens, credentials, PINs, unrestricted
environment dumps, secret-bearing command lines, raw key-store inventories, or unrestricted absolute paths.

The SDK:

- does not open or modify the archive;
- does not read or hash package or signature files;
- does not load keys, certificates, credentials, tokens, or PINs;
- does not resolve or authenticate signing identities;
- does not sign or verify;
- does not copy or write signature artifacts;
- does not contact a network service;
- does not upload or publish;
- does not launch FoA or call an adapter;
- does not mutate deployment state or saves.

No upload or publication occurs. Failure, skipped, partial, unknown-cause, and adverse evidence remains visible
rather than being erased or inferred away.

## Validation and tests

Repository validation enforces:

- required contracts, shared hardening boundary, service, registry, pane, lifecycle, and compiled-test files;
- Core and Editor build ownership;
- production-linked compiled-test manifest linkage;
- exact Editor module and pane registration;
- transient registry cleanup;
- non-editable and bounded UI presentation;
- reconstructed upstream assembly evidence;
- closed enum values and representable unknown external failures;
- chronology, privacy, fixed limits, reported/authority fingerprint separation, and unknown diagnostic media;
- explicit no-operation fields and absence of file, process, network, and cryptographic operation APIs;
- public documentation, roadmap, release-process, local-validation, and twenty-two-pane checklist integration.

Compiled coverage includes exact success, rejected and caller-mutated assembly evidence, unsigned intent,
signer-review capabilities, binding drift, malformed and unknown numeric enums, representable unknown failures,
outcome consistency, valid failed adverse evidence, unsafe and case-fold-colliding paths, archive/review/signature
chronology, secret-like metadata, oversized envelopes, orphan and reciprocal diagnostics, deterministic evidence
ordering, reported-fingerprint isolation, input non-mutation, and transient-registry behavior.

The authoritative repository gate is:

```text
python Gems/TaintedGrailModdingSDK/Tools/run_local_validation.py --keep-going
```

A configured host build and compiled CTest run remain separate exact-head requirements. Windows acceptance
requires the documented twenty-two-pane manual UI evidence pass.

## Compatibility, migration, and rollback

Contract version: `1`.

The slice is transient and introduces no durable schema or migration. Existing release-artifact and
release-assembly result contracts are unchanged. The candidate source importer version advances because source
identity now uses the SDK-derived authority fingerprint rather than the caller-reported result fingerprint.

Rollback is removal or reversion of the release-signing contracts, hardening boundary, evidence service,
registry, compiled tests, read-only pane, validator, and documentation. Existing persisted workspace, pack,
source/evidence, and catalog data requires no migration.

## Limitations

This slice validates supplied release-signing metadata only. Actual archive access, key custody, signing,
signature verification, trust establishment, upload, publication, FoA launch, adapter execution, deployment,
and save mutation require separate reviewed designs, implementations, tests, evidence, and operator controls.
