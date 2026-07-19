# FoA Adapter Runtime Result Evidence Contract

## Status

Implemented as Correction Slice 10. This contract accepts typed metadata describing an externally attempted plan and returns candidate source/evidence documents. It adds no adapter implementation or execution path.

## Purpose

Slice 9 produces canonical work-order plans with execution prohibited. Slice 10 defines how a later, separately reviewed adapter can report what it attempted without silently changing editor-owned validation or permission state.

The contract records:

- the exact attempted plan;
- every attempted step identity and sequence;
- typed step outcomes;
- typed failures;
- cleanup and rollback results;
- safe log references;
- plan, result, step-output, and log SHA-256 fingerprints;
- exact pack, adapter, profile, game-version, branch, and runtime-target bindings.

Accepted contracts return **new evidence candidates** only. They do not prove success merely because an adapter reported success.

## Typed outcomes

Every canonical plan step receives exactly one result with one of these outcomes:

- `not_attempted` — the step was not attempted;
- `succeeded` — the adapter reports an attempted successful result and supplies an output fingerprint;
- `failed` — the adapter reports an attempted failure and supplies one or more typed failure references;
- `skipped` — the step was deliberately not attempted because one or more typed failures or prerequisites blocked it.

`Attempted` is true only for `succeeded` or `failed`. Failed and skipped outcomes require failures. Succeeded and not-attempted outcomes cannot carry failure references.

## Attempted plan binding

An envelope must bind exactly to one canonical `AdapterWorkOrderPlan`:

- exact `PlanId`;
- exact canonical plan JSON;
- declared `PlanFingerprint`;
- exact pack ID and version;
- exact adapter ID and version;
- exact profile ID, game version, branch, and runtime target.

The envelope must contain exactly one step result for every plan step. Unknown, duplicate, missing, reordered-by-identity, or changed step bindings fail closed. Sequence, capability, subject kind, subject ID, and subject reference must match the canonical step.

## Typed failures

Failures have:

- a lowercase namespaced stable failure ID;
- a typed kind: `contract`, `capability`, `runtime`, `persistence`, `cleanup`, `rollback`, or `unknown`;
- a lowercase code;
- a non-empty message;
- an optional exact attempted step ID;
- optional safe log-reference IDs;
- an explicit retryable flag.

Failures do not grant permission, invalidate prior evidence automatically, or rewrite catalog state. They return as new evidence for later review.

## Cleanup and rollback

The canonical plan already contains exactly one `cleanup` step and one `rollback` step. The envelope carries explicit `CleanupResult` and `RollbackResult` summaries.

Each summary must exactly match its corresponding step result:

- step ID;
- outcome;
- failure references;
- log references;
- output fingerprint.

A mismatched or missing recovery summary rejects the complete evidence return.

## Log references and fingerprints

A log reference contains:

- a stable log ID;
- a typed kind: `adapter`, `game`, `diagnostic`, `cleanup`, or `rollback`;
- a safe workspace-relative locator;
- a lowercase `sha256:<64 hex>` fingerprint;
- zero or more exact attempted step IDs.

Absolute paths, traversal, control characters, unknown steps, duplicate IDs, or malformed fingerprints fail closed. Slice 10 does not open, copy, inspect, persist, upload, or execute referenced logs.

## Evidence return

An accepted envelope produces candidate documents by value:

- one primary `adapter_runtime_result` source;
- one step-result evidence record per attempted plan step;
- failure evidence records;
- cleanup and rollback evidence records;
- one exact plan-binding evidence record;
- one separate source per referenced log fingerprint;
- log-reference evidence bound to the relevant attempted steps.

Candidate records retain the exact profile, game version, branch, source fingerprint, subject reference, capture time, adapter identity, and adapter version. Confidence begins as `unrated`.

Nothing is automatically registered with `SourceEvidenceRegistry`, written to disk, promoted into the catalog, validated, permitted, or published into `FoundationService` state.

## Transient registry and Editor view

`AdapterRuntimeResultRegistry` is transient Core state and is cleared when the Editor shuts down. Slice 10 adds no runtime-result document loader, file picker, import command, network transport, or registration control.

**Tainted Grail Adapter Runtime Result Evidence** is read-only. It shows:

- exact result and plan identities;
- contract acceptance or rejection;
- attempted step identities and outcomes;
- failures;
- cleanup and rollback results;
- log references and fingerprints;
- candidate source/evidence counts;
- actionable contract issues.

The normal Developer Preview state contains zero registered runtime-result envelopes.

## Governance boundary

Runtime-result evidence is an observation, not a governance decision.

The contract:

- does not promote validation or permission;
- does not remove blockers;
- does not mark records current;
- does not prove persistence, cleanup, or rollback safety by declaration alone;
- does not authorize another execution;
- does not mutate workspaces, packs, sources, evidence, catalogs, governance, plans, or saves.

A reviewer may later import and assess returned evidence through the ordinary source/evidence, validation, and permission workflow.

## No adapter implementation or execution path

Slice 10 contains no FoA process access, BepInEx/Harmony loading, adapter dispatch, game API call, deployment, launch, telemetry, save mutation, generated runtime code, or automatic result capture. It defines the return contract only.

## Rollback

Revert the implementing pull request. The registry and derived evidence candidates are transient, and no durable schema migration is required.
