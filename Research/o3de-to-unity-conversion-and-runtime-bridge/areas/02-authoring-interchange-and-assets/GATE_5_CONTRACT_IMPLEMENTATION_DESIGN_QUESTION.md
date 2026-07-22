# Gate 5 Canonical Interchange Contract Implementation Design Question

Status: focused design question; no implementation authority

Repository baseline: `504e10b27e46fceae4d68af200118edca27b4d1b` (`main`), observed 22 July 2026

Parent research conclusion: `CANONICAL_INTERCHANGE_SCHEMA_AND_IDENTITY_RESEARCH.md`

## Design question

What exact Gate 5 Core contract API, source-file ownership, canonical serializer boundary, validator limits,
public schema package, migration interface, and synthetic fixture acceptance matrix should FOA-SDK authorize for
the first contract-only implementation slice while preserving zero filesystem, provider, process, native-host,
runtime, deployment, save, signing, publication, or evidence-promotion authority?

## Entry prerequisite

This question may be reviewed now. Implementation may begin only after:

1. the canonical interchange research conclusion is accepted and merged;
2. repository drift is reconciled to the proposed implementation base;
3. the Phase 9 entry prerequisite is explicitly accepted under the controlling roadmap and gate map;
4. this focused design receives explicit maintainer acceptance.

Research acceptance alone does not satisfy those prerequisites.

## Required design decisions

### Core model surface

- exact C++ type names and namespaces;
- source/header ownership and build-target placement;
- `PackageId`, `AssetId`, `RevisionFingerprint`, `BindingId`, and `MappingId` value types;
- document, asset, mapping, binding, payload, transformation, loss, provenance, licensing, lock, extension, and
  evidence-reference records;
- enum and ID grammar ownership;
- bounded maximum counts and sizes;
- reflection and public API exposure;
- caller-input non-mutation guarantees.

### Canonical serializer

- dedicated `foa-interchange-canonical-json-v1` implementation boundary;
- relationship to the existing `DeterministicContractJson` helper;
- exact object property order and stable array ordering;
- ASCII semantic-token validation;
- UTF-8 presentation-string behavior;
- finite number and negative-zero handling;
- semantic, package, payload, and qualification fingerprint interfaces;
- byte-level golden fixtures.

### Pure validation

- canonical validation result shape;
- stable error and blocker code representation;
- deterministic issue precedence and ordering;
- cross-reference and cycle validation;
- spatial/matrix validation;
- provenance, legal, extension, and migration validation;
- no filesystem, environment, clock, network, process, or host queries.

### Migration interface

- exact pure adjacent migration API;
- source and target schema dispatch;
- preservation of source documents;
- semantic-drift detection;
- identity and mapping consequences;
- migration evidence returned by value;
- unsupported-future-version and missing-migrator behavior.

### Public schema package

- repository path and owner for JSON Schema or equivalent public schema artifacts;
- generated versus hand-authored source of truth;
- schema/profile version publication rules;
- canonical examples and negative examples;
- third-party consumption boundary;
- compatibility and migration documentation.

### Fixture programme

- minimal documents-only and asset packages;
- canonical byte identity;
- rename, revision, duplicate, fork, merge, split, replacement, and tombstone cases;
- binding unresolved, stale, conflict, supersession, and host-ID changes;
- exact spatial identity and conversion matrices;
- unusual UTF-8 presentation text and invalid semantic tokens;
- future schema, unknown field, extension, path, payload, digest, dependency, loss, provenance, legal, and
  migration negatives;
- deterministic issue ordering;
- caller-input non-mutation;
- no filesystem or process authority.

## Required deliverables

1. implementation design document with exact ownership and dependency graph;
2. complete C++ contract inventory;
3. canonical serialization decision record and golden-byte examples;
4. validator and blocker precedence table;
5. migration API and state-transition design;
6. public schema package layout;
7. focused compiled-test and validator plan;
8. exact proposed changed-file list;
9. explicit authority matrix with every operational capability false;
10. rollback and compatibility consequences;
11. acceptance checklist for the first implementation PR;
12. following focused unit after Gate 5 contracts.

## Acceptance criteria

The design is ready for implementation review only when:

- every type and source file has one owner;
- Core remains independent from Framework, Editor, Qt, filesystem, providers, Blender, Unity, runtime adapters,
  and the target game;
- no second identity, evidence, permission, or catalog system is introduced;
- canonical bytes and fingerprints are specified exactly;
- every invalid class maps to a stable deterministic code;
- migration fails closed and never mutates source input;
- fixtures cover every accepted research invariant and negative path;
- the changed-file scope is narrow and contract-only;
- no service consumes the contracts;
- every operational or performed flag is absent or permanently false;
- Phase 9/Gate 5 authority is recorded separately rather than inferred from this design.

## Out of scope

- filesystem package loading or publication;
- Asset Processor integration;
- provider discovery or execution;
- Blender add-on or command work;
- Unity package, project, importer, or command work;
- native host compatibility claims;
- runtime payload mapping;
- deployment, game launch, mutation, save access, signing, or publication.

## Permanent non-authority statement

This design question does not authorize implementation. It creates no schema, service, serializer, validator,
migration, filesystem, process, provider, native-host, runtime, deployment, save, signing, publication, or
evidence-promotion authority.
