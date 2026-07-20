# FoA Release-Signing Result Evidence

Status: implemented, continuing hardening and exact-head host/UI validation.

## Purpose

This contract preserves a release-signing result supplied by a separately reviewed external signer and binds it
to one exact accepted release-assembly/checksum result.

It exists so later review can distinguish:

- the exact release artifact and accepted assembly result presented for signing;
- the exact archive identity, path, format, size, and reported SHA-256 fingerprint;
- the approved external-signing intent and identity metadata;
- the separately reviewed signer tool and its declared capabilities;
- whether signing was not attempted, succeeded, failed, or was skipped;
- which signature artifacts, failures, and safe diagnostics were reported;
- contract-valid supplied evidence from signing, verification, trust, or release authority performed by the SDK.

The SDK does not perform signing. It validates supplied metadata and returns candidate evidence by value.

## Exact inputs

`AdapterReleaseSigningEvidenceService::BuildEvidenceReturn` consumes:

1. one exact ready `AdapterReleaseArtifactEnvelope`;
2. one exact `AdapterReleaseAssemblyResultEnvelope`;
3. the exact accepted `AdapterReleaseAssemblyEvidenceReturn` for that assembly result;
4. one separately supplied `AdapterReleaseSigningResultEnvelope`.

The assembly evidence must be contract-valid, accepted, exact-bound to the assembly result, and free of
SDK-performed operations. The assembly result must report one successful supplied archive before signing
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

Any canonical-artifact drift, assembly-result drift, archive drift, release-context drift, or signing-intent
drift fails closed.

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

Acceptance requires an `accepted`, evidence-backed, capability-complete review. The SDK does not discover,
install, invoke, authenticate, or trust the signer tool.

## Signing outcomes

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

A `not_attempted` or `skipped` result cannot claim completed signature artifacts. Completion and artifact
timestamps cannot occur after the capture timestamp, and signature artifacts cannot be created after the
reported completion time.

## Signature artifacts

Each supplied signature artifact preserves:

- stable signature-artifact identity;
- typed artifact kind;
- safe package-relative reference;
- bounded media type;
- positive reported byte size;
- lowercase SHA-256 fingerprint;
- UTC creation timestamp;
- exact archive identity and fingerprint;
- unique diagnostic-reference identities.

The contract supports detached signatures, signature bundles, certificate bundles, transparency receipts,
attestations, and reviewed `other` evidence without assuming one vendor or identity technology.

Signature-artifact identities and Windows case-folded path identities must be unique. The SDK does not open,
parse, hash, verify, copy, write, register, persist, or publish a signature artifact.

## Failures and diagnostics

A supplied signing failure preserves:

- stable failure identity;
- typed non-`unknown` failure kind;
- bounded public code and message;
- optional signature-artifact binding;
- unique diagnostic-reference identities;
- retryable state.

A supplied diagnostic reference preserves:

- stable diagnostic identity;
- typed diagnostic kind;
- safe package-relative reference;
- lowercase SHA-256 fingerprint;
- unique optional signature-artifact bindings.

The service rejects absolute or drive-qualified paths, traversal, malformed fingerprints, malformed
timestamps, duplicate identities, Windows case-folded path collisions, orphan references, and
non-reciprocal artifact/diagnostic bindings. Referenced diagnostic content is never opened or inspected.

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

`accepted` means only that the separately supplied metadata is structurally valid and exactly bound. It does
not mean that the SDK signed the archive, verified a signature, authenticated the signer, established
cryptographic trust, approved the release, or authorised publication.

Issues are sorted deterministically by code, signature-artifact identity, failure identity, diagnostic
identity, and message.

## Candidate evidence

A contract-valid result may return candidate source/evidence documents by value for:

- release-artifact binding;
- accepted assembly-result and archive binding;
- signer review;
- signing-intent binding;
- signing attempt and outcome;
- every supplied signature artifact;
- every supplied failure;
- every safe diagnostic reference.

Candidate evidence is not automatically registered, persisted, promoted, validated, permitted, trusted,
uploaded, or published.

Equivalent valid inputs produce deterministic source identities, evidence identities, and evidence ordering.
Validation does not mutate the artifact, assembly result, assembly evidence return, signing result, or
registries.

## Transient registry

`AdapterReleaseSigningResultRegistry` stores supplied result envelopes in memory only.

The registry rejects malformed contract/binding identities, malformed fingerprints, invalid signer-tool
versions, and duplicate result identities. It preserves insertion order and is cleared when the dedicated
Editor pane lifecycle component deactivates.

No durable schema, migration, or persisted signing-result file is introduced.

## Read-only Editor pane

**Tainted Grail Release Signing Results** displays:

- signing-result identity and fingerprint;
- `contract status=not evaluated` for registry-only rows;
- release-artifact and assembly-result bindings;
- archive identity, path, format, byte size, and fingerprint;
- supplied signer review, tool version/fingerprint, reviewer, timestamp, capabilities, and evidence IDs;
- supplied signing identity kind, signer, locator, and fingerprint;
- attempted state, outcome, completion, and capture time;
- signature artifacts and exact archive bindings;
- failures, retryable state, and safe diagnostics;
- reconciliation, package, manifest, pack, profile, game, branch, and runtime context;
- explicit SDK no-operation safety state.

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

No upload or publication occurs. Failure, skipped, partial, and adverse evidence remains visible rather than
being erased or inferred away.

## Validation and tests

Repository validation enforces:

- required contracts, service, registry, pane, lifecycle, and compiled-test files;
- Core and Editor build ownership;
- compiled-test manifest linkage;
- exact Editor module and pane registration;
- transient registry cleanup;
- non-editable UI controls;
- explicit no-operation fields and boundary text;
- absence of file, process, network, and cryptographic operation APIs;
- public documentation, roadmap, release-process, local-validation, and twenty-two-pane checklist integration.

Compiled coverage includes exact success, rejected assembly evidence, unsigned intent, signer-review
capabilities, binding drift, malformed fingerprints, outcome consistency, valid failed adverse evidence,
unsafe and case-fold-colliding paths, chronology, orphan and reciprocal diagnostics, deterministic evidence
ordering, input non-mutation, and transient-registry behavior.

The authoritative repository gate is:

```text
python Gems/TaintedGrailModdingSDK/Tools/run_local_validation.py --keep-going
```

A configured host build and compiled CTest run remain separate exact-head requirements. Windows acceptance
requires the documented twenty-two-pane manual UI evidence pass.

## Compatibility, migration, and rollback

Contract version: `1`.

The slice is transient and introduces no durable schema or migration. Existing release-artifact and
release-assembly result contracts are unchanged.

Rollback is removal or reversion of the release-signing contracts, evidence service, registry, compiled tests,
read-only pane, validator, and documentation. Existing persisted workspace, pack, source/evidence, and catalog
data requires no migration.

## Limitations

This slice validates supplied release-signing metadata only. Actual archive access, key custody, signing,
signature verification, trust establishment, upload, publication, FoA launch, adapter execution, deployment,
and save mutation require separate reviewed designs, implementations, tests, evidence, and operator controls.
