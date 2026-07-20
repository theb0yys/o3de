# External Tool Interchange Gate 0

Status: in development on `FOA-plug-in-development`

Owner: `TaintedGrailModdingSDK.Core.Static`

## Decision

Gate 0 introduces typed, canonical, fail-closed documents for a future external-tool handoff. It is a
contract-only precursor to the Phase 9 editor-toolchain program. It does not start the process-supervision,
provider, source-package, Unity, or runtime gates.

The gate is deliberately inert. No service consumes these documents, no registry persists them, and no code
in this gate can inspect a path, launch a process, import an asset, build an assembly, mutate a project, deploy
content, connect to FoA, or promote evidence.

## Contracts

Gate 0 owns four version-1 envelopes:

| Contract | Meaning at Gate 0 |
| --- | --- |
| `ExternalToolHandoffV1` | Exact non-executable intent binding for a provider command, with later-gate evidence/source bindings optional |
| `UnityConversionRequestV1` | Exact Unity Editor interchange request bound to the handoff; never a runtime request |
| `ExternalToolExecutionResultV1` | Disabled, `NotAttempted` observation bound to the handoff |
| `UnityConversionResultV1` | Disabled, `NotAttempted` observation bound to the request and external result |

Each envelope has deterministic canonical JSON and a lowercase SHA-256 fingerprint. The envelope fingerprint
is excluded from its own canonical projection. Embedded upstream canonical JSON must equal the canonical
serialization of the supplied upstream envelope; matching only a caller-supplied digest is insufficient.

Provider, command, application, extension, profile, direction, and version bindings are repeated where
necessary and must match exactly. Qualification evidence and source-package bindings may remain absent because
Gates 3–5 own those contracts; when present they must be complete and exact. Gate 0 records interchange schema
version `0` (unselected), not schema 1. Provider and extension versions use strict SemVer. Application versions
use bounded exact tokens because values such as Unity's `2022.3.22f1` are not SemVer.

Durable contracts contain stable identities and safe relative paths only. Absolute executable, Unity project,
workspace, game-installation, and output paths stay outside Core.

## Authority matrix

| Capability | Gate 0 value | Earliest owning gate |
| --- | --- | --- |
| Process launch or cancellation | prohibited | Gate 1 after Phase 9 entry |
| Provider command UI | prohibited | Gate 2 |
| Source-artifact publication | prohibited | Gate 3 |
| Provider discovery/qualification | prohibited | Gate 4 |
| Interchange package conversion | prohibited | Gates 5–10 |
| Unity project mutation | prohibited | separately reviewed Unity execution gate |
| Runtime adapter build or execution | prohibited | post-Gate-13 runtime program |
| Game discovery, deployment, launch, or save mutation | prohibited | separately reviewed runtime/deployment gates |

All authority and performed flags are `false`. Execution and conversion outcomes are `NotAttempted`.
Attempt-scoped output, exit-code, start/completion, project-mutation, build, deployment, and loss-report fields
must be absent. A capture timestamp may record when a disabled result document was created; it is not execution
evidence or a trusted-clock claim.

Version 1 remains permanently inert. A later gate must introduce a separately reviewed contract version for
attempted or successful work; it must not loosen version-1 validation in place.

## Validation rules

Validation is pure Core logic with deterministic error precedence. It requires:

- contract version `1` and exact typed enum values;
- stable IDs and lowercase SHA-256 fingerprints;
- exact upstream canonical JSON and fingerprint bindings;
- exact provider, command, version, extension, direction, and profile bindings;
- an unselected interchange schema plus absent-or-complete future source bindings;
- duplicate-free, bounded, canonicalized set-like collections without mutating caller input;
- a contained relative path identity with traversal, absolute-path, reserved-name, and ambiguous-syntax rejection;
- all-or-none optional identity/fingerprint pairs;
- disabled authority, attempt, mutation, build, and deployment state.

Hashes observe identity and integrity only. They do not prove authenticity, qualification, safety, licence,
permission, or approval.

"Core-only" describes production-source ownership and dependencies. Focused compiled tests are wired into the
repository's existing aggregate catalog-test target, which has broader test-only dependencies; that aggregate
linkage is not evidence that Gate 0 production code may depend on Framework or `AzToolsFramework`. The source-
family validator enforces the production boundary independently.

## Gate acceptance

Gate 0 is complete only when:

1. the four contracts and canonical helpers are owned by Core and compile through the existing build graph;
2. focused tests cover valid disabled envelopes, exact upstream binding, stale fingerprints, mismatches,
   unsafe paths, duplicates, canonical ordering, input non-mutation, enum rejection, and authority rejection;
3. a repository validator locks the exact contract-family source set and screens it for filesystem, process,
   shell, socket, registry, persistence, Qt, and `AzToolsFramework` dependencies;
4. public data-format and research-gate documentation matches the implementation;
5. the authoritative local validation command passes at the exact accepted head.

Passing Gate 0 grants no permission to begin Gate 1. Phase 9 entry and the separately reviewed generic process
supervisor remain independent prerequisites.

## Research reconciliation

The supplied research report recommends a file-backed Unity batch boundary, which remains a later candidate.
Its proposed no-op BepInEx build/deploy/load slice is not Gate 0: even a no-op plugin crosses build, game
deployment, process launch, runtime execution, evidence, cleanup, and rollback authorities. Those activities
remain in the existing runtime work-order and deployment sequence after the authoring interchange gates.

The durable research input, sources, claims, unresolved target-profile facts, and gate mapping live in the
[O3DE-to-Unity bridge research archive](../../Research/o3de-to-unity-conversion-and-runtime-bridge/README.md).
