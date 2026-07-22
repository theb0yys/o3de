# Semantic Hook Batch 006

## Identity

- base: merged Semantic Hook Batch 005
- authority: engine-neutral synthetic repair implementation and offline validation only
- game-runtime authority: none
- hook promotion authority: none

Batch 006 implements the inert project-owned repair primitives designed in Batch 005. It does not modify the upstream mods, load game or loader assemblies, use reflection, discover an installation, execute Harmony, mutate a game, or produce promotion evidence.

## Implemented primitives

### Exact typed transactions

`scripts/tainted_grail/repair_primitives.py` adds profile/type-bound field adapters and mapping transactions. An adapter accepts one exact profile ID, type ID, field name and Python value type. Transactions preflight the original and proposed values, reject identity or numeric-domain mismatches, commit only after preparation, roll back when a dependent write fails, and support repeated rollback.

The model deliberately provides no caller-name fallback, non-public lookup, assembly loading or native-object access.

### Hardened diagnostic model

The diagnostic primitive:

- resolves a canonical root and requires a strict descendant session path;
- rejects empty, rooted, multi-component, dot, dot-dot, reserved, control-character and overlong session segments;
- classifies caller-declared sensitive fields for redaction;
- neutralizes spreadsheet formula prefixes;
- enforces field, row and session byte limits;
- writes through same-directory temporary files and replacement;
- restores both prior row and summary bytes if either publication step fails;
- increments session accounting only after both outputs are durable.

This is a synthetic filesystem model. It does not capture game diagnostics or claim support-safe production output.

### Synthetic mount conversion transaction

The mount model captures explicit previous ownership including `null`, native actions, fields, movement states and created-object identities. It supports injected failures after object creation, field mutation, movement suspension and ownership change. Every failure uses the same idempotent rollback path and restores the complete synthetic snapshot.

It contains no Unity, TG.Main, model-element, hero, wolf or mount implementation.

### Avalon Companions API v2 model

The in-memory registry provides:

- `api_version = 2`;
- immutable owner/command registration identities;
- deterministic duplicate rejection;
- owner-scoped query;
- registration tokens;
- stale and cross-owner token rejection;
- retryable cleanup that retains its token after a failed unregister and clears it only after confirmed removal.

This is a contract model, not a compiled or runtime Avalon Companions API.

## Synthetic tests

`test_repair_primitives.py` covers:

- exact typed identity, numeric-domain rejection and successful commit;
- dependent-write failure rollback and idempotence;
- diagnostic segment rejection, redaction, formula neutralization and byte limits;
- row/summary restoration after injected summary replacement failure;
- exact mount snapshot restoration at four injected failure points;
- explicit restoration of previous `null` mount ownership and native actions;
- duplicate registration, owner isolation, stale-token refusal and retryable cleanup.

## Runner golden receipts

Batch 006 adds synthetic valid and invalid manifests plus their exact deterministic receipts under `scripts/tainted_grail/goldens/`.

`test_semantic_fixture_goldens.py` rebuilds both receipts through the Batch 005 runner and compares the complete object, including manifest SHA-256, sorted error ordering, counts, status, `runtime_authority: none` and `promotion: none`.

The invalid golden intentionally contains a duplicate case, empty expectations, a presented runtime fingerprint and an attempted behavior promotion. Its receipt must remain invalid.

## Validation result

Local standard-library validation:

```text
python -m unittest -v
```

- primitive tests: 9 passed;
- golden receipt tests: 2 passed;
- total: 11 passed;
- external dependencies: 0.

## Governance result

- hook promotions: 0;
- evidence promotions: 0;
- runtime adapters added: 0;
- game or loader assemblies referenced: 0;
- Batch 004 prohibitions changed: 0.

Passing these tests proves only the behavior of project-owned synthetic models and the deterministic offline receipt format.

## Next documented unit

Semantic Hook Batch 007 should harden these primitives as reusable project-owned packages: explicit transaction state machines, crash-recovery journals for synthetic diagnostic publication, property-based failure matrices, API v2 serialization/version negotiation fixtures, and CI wiring for the offline suite. It must preserve the same no-runtime and no-promotion boundary.
