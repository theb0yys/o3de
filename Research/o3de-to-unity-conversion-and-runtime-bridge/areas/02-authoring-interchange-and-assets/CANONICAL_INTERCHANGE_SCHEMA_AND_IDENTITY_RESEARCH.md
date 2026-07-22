# Canonical Interchange Schema and Identity Research Conclusion

Status: accepted research conclusion; no implementation authority

Current repository baseline: `504e10b27e46fceae4d68af200118edca27b4d1b` (`main`), observed 22 July 2026

Deep Research intake baseline: `195f5c15f0c59d47bd54e661b37d7457af9d1d95`

Parent synthesis: `../../FOA_SDK_PORTING_METHODS_RESEARCH.md`

Preserved intake: `../../inputs/CANONICAL_INTERCHANGE_SCHEMA_AND_IDENTITY_DEEP_RESEARCH.md`

## Authority boundary

This document accepts a research direction and resolves the minimum Schema-1 contract decisions needed for a
later Gate 5 design review. It does not authorize implementation, persistence, filesystem access, package
publication, process launch, Blender or Unity execution, O3DE source-root mutation, game inspection, runtime
adapter work, deployment, save access, evidence promotion, signing, or publication.

Gate 5 implementation remains blocked until the Phase 9 entry prerequisite and a focused Gate 5 implementation
design are explicitly accepted under the controlling gate map.

## Repository reconciliation

The Deep Research report was written against `195f5c15f0c59d47bd54e661b37d7457af9d1d95`. Current `main` is
`504e10b27e46fceae4d68af200118edca27b4d1b`, 179 commits later:

https://github.com/theb0yys/FOA-SDK/compare/195f5c15f0c59d47bd54e661b37d7457af9d1d95...504e10b27e46fceae4d68af200118edca27b4d1b

The intervening work materially changes the research context by adding or hardening deterministic JSON helpers,
exact evidence boundaries, ExtensionAPI ownership, route records, catalog schema migration, population
identities, package/deployment/release preview contracts, repository validation, and public modding knowledge.
It does not change the controlling porting order or grant provider execution.

The accepted conclusion therefore preserves the report's architecture while correcting:

- stale repository observations;
- source-register ID collisions;
- incomplete canonicalization rules;
- deferred spatial and matrix conventions;
- incomplete identity mapping for merge and split operations;
- missing package-level migration policy;
- missing canonical error and blocker inventory;
- archive ambiguity;
- evidence placement and fingerprint scope.

## Accepted architecture option

Schema 1 uses:

```text
one authoritative manifest
+ typed engine-neutral domain documents
+ contained format-specific payloads
+ exact canonical-to-native bindings
+ explicit identity mapping events
+ bounded reviewed extension namespaces
+ external Framework-owned qualification evidence
```

Option disposition:

| Option | Disposition | Reason |
| --- | --- | --- |
| Monolithic manifest | rejected | embeds too much domain data and pressures native detail into Core |
| Core manifest plus typed domain documents | accepted | preserves Road Atlas, Avalon AI, actors, troops, relationships, and governance as engine-neutral owners |
| Core manifest plus namespaced extensions | accepted with strict admission | supports bounded host detail without hidden authority |
| Host-native manifests plus minimal index | rejected | makes native IDs and serializer behavior de facto authority |
| Content-addressed payload graph | deferred | unnecessary complexity for the minimum Gate 5 contract |
| Ordered payload inventory | accepted | deterministic, reviewable, and sufficient for Schema 1 |

## Package boundary decision

Schema 1 is a **contained directory**, not an archive.

The package root contains exactly one authoritative file:

```text
manifest.tginterchange.json
```

Every material document and payload is contained under the package root and listed in the manifest. Deterministic
archive assembly is a later packaging concern and must not be coupled to the first canonical schema.

Schema 1 forbids:

- package self-fingerprint fields;
- absolute paths;
- path traversal, dot segments, symbolic-link escapes, case collisions, and Windows path aliases;
- unlisted material files;
- executable payloads, DLLs, native packages, add-ons, scripts intended for execution, or runtime bundles;
- game-install, proprietary Unity-project, deployment, launch, runtime, or save paths;
- process commands, environment variables, credentials, or executable entry points;
- mutable permission or authority flags.

## Minimum Schema-1 top-level field inventory

| Field | Type | Cardinality | State | Owner | Fingerprint scope |
| --- | --- | --- | --- | --- | --- |
| `schema_version` | integer | exactly 1 | required; value `1` | Core | package and semantic projection |
| `schema_profile` | ASCII token | exactly 1 | required | Core | package and semantic projection |
| `canonical_profile` | ASCII token | exactly 1 | required | Core | package and semantic projection |
| `package_kind` | enum | exactly 1 | required; `authoring-interchange` | Core | package and semantic projection |
| `package_id` | `PackageId` | exactly 1 | required | Core | package and semantic projection |
| `pack_id` | canonical pack ID | exactly 1 | required | Core | package and semantic projection |
| `display_name` | UTF-8 string | zero or one | optional, presentation only | Core | package only; excluded from semantic revisions |
| `producer` | object | exactly 1 | required | Core | package projection |
| `intended_consumers` | array | zero or more | optional | Core | package projection |
| `toolchain_lock` | object | exactly 1 | required | Core | package projection |
| `documents` | array | zero or more | required array, may be empty | Core | package and subject projections |
| `assets` | array | zero or more | required array, may be empty | Core | package and subject projections |
| `identity_mappings` | array | zero or more | required array, may be empty | Core | package and subject projections |
| `bindings` | array | zero or more | required array, may be empty | Core | package projection; excluded from semantic asset revisions unless profile says native binding is semantic |
| `payloads` | array | one or more | required | Core | package and subject projections |
| `transformations` | array | zero or more | required array, ordered | Core | package and affected subject projections |
| `losses` | array | zero or more | required array, ordered | Core | package and affected subject projections |
| `provenance` | array | one or more | required | Core | package and affected subject projections |
| `licensing` | array | one or more | required | Core | package projection |
| `evidence_refs` | array | zero or more | optional external Framework evidence bindings | Framework reference shape defined in Core | package qualification projection only |
| `extensions` | object | zero or one | optional, namespace-admitted | Core admission; namespace owner validates content | profile-defined; never silently excluded |

At least one `documents` or `assets` entry is required. A documents-only package is valid. An asset-only package is
valid only when its engine-neutral semantics and provenance are complete.

## Producer, consumer, and toolchain lock

`producer` records:

- `host_kind`: `o3de`, `blender`, or `unity-editor`;
- exact application version token;
- exact provider ID when a provider exists;
- exact native extension ID, version, source revision, and digest when applicable;
- exact configuration fingerprint;
- optional workspace and profile context as observations, never as portable identity.

`intended_consumers` records zero or more exact host/profile constraints. A missing consumer means the package is
host-neutral, not universally compatible.

`toolchain_lock` records:

- FOA-SDK commit and schema profile;
- O3DE repository, exact commit, and engine version;
- exact Blender or Unity version when that host participates;
- exact provider and extension versions and digests;
- exact payload-format and converter versions;
- exact configuration fingerprint;
- exact synthetic fixture revision when qualification evidence is attached.

Changing any lock component creates a new package fingerprint and new qualification result. It does not silently
rewrite earlier evidence.

## Canonical identity model

### ID syntax

All fingerprint-participating IDs use lowercase ASCII namespaced tokens. They must not depend on display names,
paths, Unity GUIDs, Blender names, O3DE labels, timestamps, or host-generated order.

### Primary identities

- `PackageId` identifies one package lineage.
- `AssetId` identifies one project-owned logical asset.
- `RevisionFingerprint` identifies one normalized semantic revision of one asset or domain document.
- `BindingId` identifies one canonical-to-native mapping.
- `MappingId` identifies one explicit rename, fork, merge, split, replacement, or aggregation event.

### Asset lifecycle

| Operation | Asset identity consequence | Revision consequence | Binding consequence |
| --- | --- | --- | --- |
| rename or move | preserve `AssetId` | unchanged unless semantic content changes | update or supersede affected native binding |
| semantic edit | preserve `AssetId` | new `RevisionFingerprint` | preserve or update bindings explicitly |
| duplicate | new `AssetId` by default | new revision | new bindings |
| fork | new `AssetId` with typed lineage | new revision | new bindings |
| replace | new or existing `AssetId` only through explicit policy | new revision | superseding binding or mapping event |
| merge | new target `AssetId` | new revision | typed many-to-one mapping and complete loss ledger |
| split | new child `AssetId` values | new revisions | typed one-to-many mapping and complete loss ledger |
| delete | tombstone; never reuse ID | final revision remains auditable | bindings retire |
| native GUID/path change | preserve `AssetId` | unchanged unless semantics changed | new or superseded `BindingId` |

### Identity mapping record

Every non-trivial lineage event uses `identity_mappings[]` with:

- `mapping_id`;
- `operation`: `rename`, `move`, `duplicate`, `fork`, `replace`, `merge`, `split`, `aggregate`, or `tombstone`;
- ordered `source_asset_ids`;
- ordered `target_asset_ids`;
- optional source and target revision fingerprints;
- transformation references;
- loss references;
- provenance and evidence references;
- explicit completeness state.

A merge or split cannot be represented only through `parent_asset_ids`. It requires a first-class mapping event.

### Binding states

Bindings use:

```text
unresolved
active
stale
conflicted
superseded
retired
```

A required consumer binding in `unresolved`, `stale`, or `conflicted` state blocks that consumer operation. A
binding value never becomes canonical identity.

## Domain-document binding

Road Atlas, Avalon AI, actor, troop, relationship, governance, and future domain records remain separately
versioned engine-neutral documents.

Each document record contains:

- stable document ID;
- document kind;
- exact document schema ID and version;
- contained payload ID;
- semantic revision fingerprint;
- canonical subject references;
- provenance and licensing references.

Each asset may reference zero or more domain documents. Each document may reference zero or more assets or other
canonical subjects. The manifest is the authoritative inventory; domain documents remain authoritative for their
own fields.

Native-only data must be classified as:

- an exact binding;
- a reviewed extension namespace;
- a contained opaque payload;
- a transformation;
- a loss;
- a blocker.

It must never be silently embedded as an unowned Core field.

## Canonical serialization decision

Schema 1 uses the dedicated profile:

```text
foa-interchange-canonical-json-v1
```

This profile is **not RFC 8785 JCS**. RFC 8785 is retained as comparative primary research, but the accepted
profile deliberately matches existing FOA-SDK deterministic-contract practice and avoids introducing implicit
Unicode normalization into the first slice.

Rules:

1. UTF-8 input, no BOM.
2. Duplicate property names are rejected during parsing.
3. No insignificant whitespace is emitted.
4. Every object type has one schema-defined property order.
5. Arrays are sorted by their canonical stable key except ordered transformations, losses, mappings, and steps.
6. Fingerprint-participating IDs, enums, paths, versions, media types, hashes, error codes, and reason codes are
   restricted to declared ASCII grammars.
7. Human display strings may contain valid UTF-8. They are preserved byte-for-byte and escaped deterministically;
   they are excluded from semantic revision fingerprints.
8. Unicode NFC is not performed by Schema 1. Canonically equivalent Unicode strings can therefore remain
   byte-distinct at the package level. This is intentional and must be documented.
9. Integers use minimal base-10 form.
10. Finite floating-point values use the shortest round-trip decimal form that preserves the binary value.
11. Non-finite values are rejected before serialization.
12. Negative zero is normalized to positive zero.
13. Boolean and null literals are lowercase JSON literals.
14. SHA-256 values use exactly 64 lowercase hexadecimal characters, with the algorithm named separately.
15. Paths use `/`, contain no empty, `.` or `..` segment, and are compared using both exact bytes and the declared
    Windows path-equivalence key.
16. A canonical serializer must not consult locale, filesystem ordering, environment, or host clock.

The current generic `DeterministicContractJson` helper is useful precedent but is not automatically the accepted
Schema-1 serializer. Gate 5 implementation must add a dedicated serializer or prove that an extended shared
helper exactly satisfies this profile.

Primary comparative references:

- https://www.rfc-editor.org/rfc/rfc8785.html
- https://www.unicode.org/reports/tr15/tr15-57.html

## Fingerprint model

Schema 1 distinguishes:

### Payload fingerprint

SHA-256 over exact contained payload bytes.

### Package fingerprint

SHA-256 over:

1. canonical manifest bytes with no self-fingerprint field; and
2. ordered tuples of canonical payload path, byte size, media type, and payload SHA-256.

### Semantic revision fingerprint

SHA-256 over a schema-defined semantic projection for one asset or document. It excludes:

- display names;
- timestamps;
- evidence references;
- native paths and host-generated IDs unless the selected profile declares them semantic;
- qualification outcomes;
- unordered presentation metadata.

It includes:

- canonical identity and kind;
- referenced semantic document revisions;
- semantic payload digests;
- canonical transforms;
- declared semantic extension fields;
- transformations and losses that affect the subject.

### Qualification fingerprint

Framework-owned SHA-256 over the package fingerprint, exact toolchain lock, fixture revision, comparison policy,
and evidence result set.

No fingerprint proves authenticity, licensing, permission, compatibility, or runtime authority by itself.

## Spatial and temporal basis decision

Schema 1 fixes the canonical basis as:

```text
handedness: right-handed
right axis: +X
forward axis: +Y
up axis: +Z
linear unit: metre
angular unit: radian
time unit: second
```

O3DE documents a right-handed Z-up coordinate system with positive X to the right and forward away from the
viewer. Blender documentation describes Y forward and Z up. Unity is left-handed, Y-up, positive Z-forward and
therefore always requires an explicit conversion to and from the canonical basis.

Primary host references:

- https://www.docs.o3de.org/docs/user-guide/assets/scene-settings/scene-format-support/
- https://docs.blender.org/manual/en/4.2/files/import_export/stl.html
- https://docs.unity3d.com/current/Manual/QuaternionAndEulerRotationsInUnity.html

### Vector and matrix convention

Schema 1 fixes:

- column vectors;
- matrix-on-left multiplication: `p_canonical = M_source_to_canonical * p_source`;
- homogeneous 4x4 affine matrices;
- column-major flattened storage;
- translation in the fourth column;
- composition `M_world = M_parent_world * M_local`;
- right-hand-rule positive rotation in canonical space;
- explicit mapping direction for every matrix;
- no implicit transpose or handedness conversion.

The O3DE math API documents matrix multiplied by column vector as its standard transform form. The canonical
storage and composition rules are selected for Schema 1 so host adapters cannot infer convention from engine
names.

Reference:

- https://docs.o3de.org/docs/api/frameworks/azcore/_a_z_base_math.html

### Temporal representation

- all canonical times are seconds;
- frame and sample rates are rational `{numerator, denominator}` values;
- clip start/end and event times are explicit seconds;
- interpolation and resampling operations are explicit transformations;
- root-motion basis is explicit;
- tolerance is never inferred from frame rate.

### Tolerance record

A numeric tolerance record names:

- subject/property path;
- absolute tolerance;
- relative tolerance;
- angular tolerance in radians when applicable;
- comparison norm;
- unit;
- fixture/profile scope.

Missing tolerance means exact comparison.

## Payload and dependency model

Schema 1 permits these material payload roles:

- `canonical-document`;
- `scene-source`;
- `mesh-source`;
- `texture-source`;
- `material-map`;
- `skeleton-source`;
- `animation-source`;
- `collider-source`;
- `metadata`;
- `preview`;
- `licence-notice`.

Evidence content remains in Framework-owned evidence documents; the package carries exact evidence references,
not mutable evidence bodies.

Each payload records:

- stable payload ID;
- canonical relative path;
- role;
- media type;
- byte size;
- SHA-256;
- ordered or sorted dependencies as declared by role;
- associated asset/document IDs;
- provenance/licensing references.

Dependency cycles are forbidden in Schema 1. External references are provenance-only and cannot satisfy a
material dependency.

## Transformation record

Every transformation contains:

- stable transformation ID;
- sequence number unique within the package revision;
- phase;
- stable operation code;
- subject IDs and property paths;
- source and destination basis/profile;
- canonical parameter object;
- reversibility state;
- tolerance reference when applicable;
- evidence references.

Transformations are declared changes, not failures.

## Loss taxonomy

Each loss entry contains:

- stable loss ID;
- sequence number;
- subject and property path;
- source and destination host/profile;
- phase;
- reason code;
- severity: `information`, `warning`, `error`, or `blocker`;
- source feature;
- result representation;
- reversibility;
- tolerance reference when applicable;
- evidence references.

Minimum loss classes:

```text
unsupported-feature
approximation
resampled
rebaked
renamed-native
merged
split
dropped
opaque-native-reference
non-reproducible
```

A host operation can succeed while the package remains blocked because of incomplete or blocker-level losses.
A preserved source-native file does not make a conversion lossless.

## Determinism and equivalence classes

Schema 1 uses:

```text
byte_identical
canonical_document_identical
payload_set_identical
semantic_equivalent_within_tolerance
reviewed_visual_or_behavioural_match
non_reproducible_but_loss_accounted
```

Only the first four can be derived mechanically. Visual or behavioral review is explicit human evidence. A
non-reproducible result remains representable only when all differences are accounted for and no blocker is
hidden.

## Provenance and legal state model

Source kind:

```text
project-owned
synthetic
user-supplied-reviewed
user-supplied-unreviewed
local-reference-only
upstream-reference
prohibited
```

Each provenance record binds source kind, source identity, exact revision or fingerprint when known, authorship,
modification state, attribution, evidence, and permitted use.

Each licensing record binds:

- subject ID;
- SPDX expression, reviewed `LicenseRef`, or `NOASSERTION`;
- redistribution state: `allowed`, `local-only`, `review-required`, or `blocked`;
- required notices;
- reviewer and evidence references;
- decision time supplied by the caller, never read from the host clock by Core.

Rules:

- `NOASSERTION` never implies redistribution permission;
- `prohibited` blocks containment, import, export, publication, and redistribution;
- `user-supplied-unreviewed` blocks publication and cross-user redistribution;
- `local-reference-only` cannot satisfy a material package dependency;
- legal review cannot be inferred from a successful parse, import, hash, or fixture.

## Validation ownership

### Core

Core owns pure validation of schema, canonical form, identity, references, mappings, bindings, paths, payloads,
fingerprints, transforms, losses, provenance, licensing, extension admission, migration shape, and deterministic
error ordering.

### Framework

Framework owns workspace/profile context, active pack and producer context, evidence retrieval and binding,
staging containment, candidate-before-publish orchestration, qualification fingerprints, migration publication,
and failure preservation.

### Host-specific provider or native extension

Host layers own syntax and observation checks for Unity GUIDs, O3DE native asset IDs, Blender object identifiers,
native project locks, importer/exporter behavior, and host-specific feature support. Host validation cannot weaken a
Core blocker.

## Canonical error and blocker inventory

Error codes are lowercase ASCII namespaced tokens. Equivalent invalid inputs produce identical ordered codes.

| Code | Owner | Meaning |
| --- | --- | --- |
| `interchange.schema.unsupported-version` | Core | schema version is not exactly supported |
| `interchange.schema.unsupported-profile` | Core | schema or canonical profile is unknown |
| `interchange.schema.unknown-field` | Core | closed object contains an unknown field |
| `interchange.schema.forbidden-field` | Core | prohibited field or authority surface appears |
| `interchange.canonical.duplicate-key` | Core | JSON object has duplicate property names |
| `interchange.canonical.invalid-string` | Core | string violates UTF-8 or field grammar |
| `interchange.canonical.non-finite-number` | Core | NaN or infinity supplied |
| `interchange.canonical.negative-zero` | Core | noncanonical negative zero supplied for verification |
| `interchange.canonical.order-invalid` | Core | canonical field or collection order is wrong |
| `interchange.identity.invalid` | Core | canonical ID syntax or scope is invalid |
| `interchange.identity.duplicate` | Core | canonical identity occurs more than once |
| `interchange.identity.mapping-invalid` | Core | lineage mapping is incomplete or inconsistent |
| `interchange.binding.invalid` | Core/host | binding shape or native value is invalid |
| `interchange.binding.unresolved-required` | Core | required consumer binding is unresolved |
| `interchange.binding.conflict` | Core | competing active bindings exist |
| `interchange.binding.supersession-invalid` | Core | supersession chain is missing or cyclic |
| `interchange.path.absolute` | Core | path is absolute |
| `interchange.path.traversal` | Core | path escapes or contains dot segments |
| `interchange.path.symlink` | Framework | resolved package member crosses a symlink |
| `interchange.path.case-collision` | Core/Framework | paths collide under declared platform equivalence |
| `interchange.path.windows-alias` | Core | reserved name, trailing dot/space, or alias collision |
| `interchange.payload.unlisted` | Framework | material file is not declared |
| `interchange.payload.missing` | Framework | declared payload is absent |
| `interchange.payload.digest-mismatch` | Framework | observed payload bytes do not match declaration |
| `interchange.payload.size-mismatch` | Framework | observed size does not match declaration |
| `interchange.dependency.missing` | Core | dependency ID does not resolve |
| `interchange.dependency.cycle` | Core | payload dependency graph contains a cycle |
| `interchange.transform.sequence-invalid` | Core | sequence is duplicate, missing, or unordered |
| `interchange.transform.matrix-invalid` | Core | matrix shape, finiteness, basis, or direction is invalid |
| `interchange.loss.incomplete` | Core | affected conversion lacks required loss detail |
| `interchange.loss.blocker` | Core | blocker-level loss prevents requested progression |
| `interchange.provenance.incomplete` | Core | material subject lacks complete provenance |
| `interchange.licensing.noassertion-blocked` | Core/Framework | requested use exceeds `NOASSERTION` state |
| `interchange.content.prohibited` | Core/Framework | prohibited content is referenced or contained |
| `interchange.lock.incomplete` | Core | required exact lock component is missing |
| `interchange.lock.mismatch` | Framework/host | observed host/tool lock differs |
| `interchange.evidence.binding-mismatch` | Framework | evidence does not bind exact package, lock, fixture, or subject |
| `interchange.migration.unavailable` | Core | no accepted adjacent migration exists |
| `interchange.migration.source-invalid` | Core | source package is invalid before migration |
| `interchange.migration.semantic-drift` | Core | migration changed semantics without declared mapping/loss |
| `interchange.package.partial` | Framework | package is incomplete or publication was interrupted |
| `interchange.extension.unapproved` | Core | namespace is not admitted by the selected profile |

## Schema evolution and migration policy

1. Schema 1 top-level and typed objects are closed.
2. Unknown fields fail closed unless they occur inside an explicitly admitted extension namespace.
3. Unknown namespaces fail closed; they are never ignored.
4. Unsupported future schema versions fail closed.
5. Downgrade is forbidden.
6. Migration is explicit and adjacent: `N -> N+1` only.
7. Multiple-version migration chains run as ordered pure steps and record every intermediate version.
8. Migration never mutates or overwrites the source package.
9. A migrated package preserves `PackageId` and stable `AssetId` values unless the migration includes an explicit
   identity mapping accepted by the target schema.
10. Package fingerprint always changes after migration.
11. Semantic revision fingerprints remain unchanged only when the target semantic projection is proven equal.
12. Any semantic change requires new revision fingerprints, transformations, mappings, and losses.
13. Migration is Core-pure and deterministic; it launches no host and reads no filesystem beyond supplied bytes.
14. Framework publishes migrated candidates only after full target-schema validation and exact source/candidate
    evidence binding.
15. Failed migration leaves source, current workspace, catalog, published package, and evidence unchanged.
16. Removed fields are retained in typed migration evidence or declared losses; they are never silently dropped.
17. Extension migration requires the exact namespace migrator and accepted namespace version.

## Positive fixture matrix

| Fixture | Expected result |
| --- | --- |
| minimal documents-only package | valid |
| minimal asset package with contained payload | valid |
| rename preserving `AssetId` | same asset identity, binding or label update only |
| semantic asset edit | new semantic revision fingerprint |
| Unity GUID replacement | same `AssetId`, new superseding binding |
| split mapping | new child IDs, complete mapping, transformations, and loss records |
| merge mapping | new target ID, complete many-to-one mapping and loss records |
| exact canonical reserialization | byte-identical canonical manifest |
| O3DE-basis identity matrix | exact spatial equivalence |
| explicit Unity-to-canonical conversion matrix | structurally valid; compatibility remains unqualified |
| `NOASSERTION` local-only subject | valid local review, publication blocked |
| explicit Schema 1 to later-schema migration fixture | source preserved and candidate deterministic |

## Negative fixture matrix

| Fixture | Required failure |
| --- | --- |
| unknown future schema version | `interchange.schema.unsupported-version` |
| unknown top-level field | `interchange.schema.unknown-field` |
| duplicate JSON property | `interchange.canonical.duplicate-key` |
| path traversal or absolute path | path blocker |
| case-colliding payloads | `interchange.path.case-collision` |
| symlink escape | `interchange.path.symlink` |
| unlisted or missing payload | payload blocker |
| payload digest mismatch | `interchange.payload.digest-mismatch` |
| duplicate `AssetId` or `BindingId` | `interchange.identity.duplicate` |
| merge without complete sources/targets | `interchange.identity.mapping-invalid` |
| required unresolved binding | `interchange.binding.unresolved-required` |
| non-finite matrix value | `interchange.canonical.non-finite-number` |
| undeclared handedness or mapping direction | `interchange.transform.matrix-invalid` |
| unsupported feature without loss record | `interchange.loss.incomplete` |
| `NOASSERTION` publication request | `interchange.licensing.noassertion-blocked` |
| prohibited proprietary payload | `interchange.content.prohibited` |
| unknown extension namespace | `interchange.extension.unapproved` |
| missing adjacent migrator | `interchange.migration.unavailable` |
| migration silently changes semantics | `interchange.migration.semantic-drift` |
| interrupted candidate publication | `interchange.package.partial`; published state unchanged |

## Round-trip evidence contract

Framework-owned evidence binds:

- source package ID and package fingerprint;
- result package ID and package fingerprint;
- exact producer, consumer, toolchain lock, and fixture revision;
- native binding changes;
- identity mapping changes;
- transformations and losses;
- comparison policy and tolerances;
- outcome class;
- failures and blockers;
- reviewer when human review is required.

A mapping claim becomes `fixture-verified` only when the exact fixture, lock, comparison policy, and evidence are
accepted. Process exit, import success, file presence, or compiler success alone is insufficient.

## Accepted conclusions

- Schema 1 uses one authoritative manifest with typed documents and ordered payload inventory.
- Schema 1 is directory-only.
- Canonical identity is engine-neutral.
- Merge and split are first-class mapping events.
- Native IDs are binding values.
- Canonical physical space is right-handed `+X` right, `+Y` forward, `+Z` up, metres, radians, seconds.
- Matrices use column vectors, matrix-on-left multiplication, and column-major storage.
- Schema 1 uses `foa-interchange-canonical-json-v1`, not an unqualified JCS claim.
- Fingerprint-participating tokens are ASCII; presentation strings remain UTF-8 and do not define semantic identity.
- Qualification evidence is Framework-owned and externally bound.
- `NOASSERTION` and prohibited content fail closed.
- Future versions and unknown extension namespaces fail closed.
- Migration is explicit, adjacent, non-mutating, deterministic, and evidence-bound.
- No host execution or runtime authority follows.

## Remaining implementation-design questions

The research conclusion intentionally does not decide:

- C++ type names, file ownership, public header layout, reflection, or build-graph wiring;
- the public JSON Schema packaging layout;
- exact maximum counts and byte limits;
- exact accepted Blender version and extension revision;
- exact accepted Unity Editor and package versions;
- provider or process APIs;
- O3DE Asset Processor publication implementation;
- runtime payload mapping.

Those belong to later focused design and qualification units.

## Recommended next focused question

> What exact Gate 5 Core contract API, source-file ownership, canonical serializer boundary, validator limits,
> public schema package, migration interface, and synthetic fixture acceptance matrix should FOA-SDK authorize
> for the first contract-only implementation slice while preserving zero filesystem, provider, process, native
> host, runtime, deployment, save, signing, publication, or evidence-promotion authority?

## Acceptance state

This research question is answered for schema structure, identity, canonicalization, spatial basis, migration,
error codes, and fixtures. The result is ready for maintainer review as a research conclusion.

It is not implementation authority. The next repository decision is explicit Phase 9/Gate 5 entry and focused
implementation-design acceptance.

## Permanent non-authority statement

This document does not authorize a schema implementation, migration service, serializer, validator registration,
filesystem operation, provider, Blender or Unity execution, O3DE source-root mutation, game inspection, runtime
adapter, build, package, deployment, launch, save access, evidence promotion, signing, or publication.
