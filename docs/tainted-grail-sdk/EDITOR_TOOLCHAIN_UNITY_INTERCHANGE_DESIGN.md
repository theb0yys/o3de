# Editor Toolchain and Unity Interchange Design

Status: proposed for design review

Target: Phase 9 ecosystem and automation, after ordered capability items 1–7 stabilize and the Phase 9 entry
gate is accepted

## Decision requested

Approve an O3DE-hosted tool-provider and interchange program for the unofficial FoA SDK. The program uses the
existing `ExternalToolchain` Tool Gem rather than adding another plugin loader, qualifies Blender as the first
external authoring provider, and defines a controlled O3DE-to-Unity authoring interchange for project-owned
content.

Approval authorises the staged design and qualification work described here. It does not authorise process
launch, arbitrary scripts, direct Unity or FoA API calls, game-project conversion, game-file discovery, asset
extraction, BepInEx or Harmony execution, deployment, save mutation, or live runtime connectivity.

The active Actor and Troop slice and all subsequent first-party domain ordering remain unchanged. This record
may be reviewed now; implementation gates do not begin until the Phase 9 entry prerequisite is satisfied.

## User problem

The SDK uses O3DE as its editor host and Unity as the separate FoA runtime context, but it does not yet have a
qualified set of external authoring tools or a reproducible way to transfer project-owned authoring data
between tool boundaries.

Without a shared contract, each integration would choose its own identities, paths, coordinate conversions,
material assumptions, process behavior, and failure reporting. That would make Blender exports, O3DE assets,
Unity test imports, and later runtime-adapter payloads difficult to reproduce or audit.

## Required outcomes

The completed program must let a mod author:

1. inspect which O3DE provider Gems and native external-tool integrations are registered;
2. see exact provider, application, plugin, schema, and compatibility versions;
3. distinguish read-only discovery enablement, location, compatibility, qualification, operation enablement,
   and execution permission;
4. author a project-owned asset in Blender and transfer it through a deterministic interchange package;
5. import the package into an isolated O3DE authoring project through the normal Asset Processor boundary;
6. inspect identity, provenance, licensing, transformations, losses, and validation evidence;
7. transfer a qualified package to or from a synthetic or user-owned Unity test project;
8. reproduce the result from an exact workspace lock without relying on mutable display names or paths;
9. keep Unity Editor interchange separate from the existing FoA runtime-adapter work-order path;
10. fail closed when a plugin, version, package, mapping, licence, proof, or path is missing or incompatible.

## Architecture ownership

### ExternalToolchain

The generic `ExternalToolchain` Gem owns provider descriptors, registration, layered configuration, bounded
local discovery, and generic diagnostics. It does not own FoA identities, interchange semantics, provider
qualification, process authority, or runtime permission.

### TG SDK Core

Core owns typed qualification states, interchange identities, schema contracts, canonical serialization,
intrinsic package validation, capability profiles, transformation declarations, and loss analysis. It does not
depend on Qt, filesystems, processes, networks, Blender, Unity, or FoA libraries.

### TG SDK Framework

Framework owns active workspace/profile/pack checks, evidence binding, contained staging, persistence,
candidate-before-publish orchestration, Asset Processor handoff planning, and later calls to a separately
approved host process supervisor.

### O3DE Editor

Editor panes remain thin clients over Framework and ExternalToolchain services. They display providers,
qualification, package content, validation, losses, and blockers; collect bounded inputs; and expose no hidden
conversion, runtime, deployment, or game action.

### Native extensions and runtime adapters

Blender add-ons and Unity Editor packages translate their native host data into the public interchange
contract. Separately reviewed FoA runtime adapters continue to own Unity, BepInEx, Harmony, game, persistence,
cleanup, and rollback operations after a reviewed work-order handoff.

## Existing foundation and located components

Research cut: 20 July 2026.

This inventory records what exists. A located component is not automatically approved, compatible, trusted,
redistributable, or enabled.

| Component | Decision state |
| --- | --- |
| `ExternalToolchain` 0.2.0 | selected and implemented host foundation |
| `TaintedGrailModdingSDK` | selected and implemented FoA contract owner |
| `SceneProcessing` | engine-registered; not project-enabled; later handoff candidate |
| `DccScriptingInterface` 0.0.2 | reference scaffolding; qualification candidate |
| O3DE Blender Scene Exporter | prototype qualification candidate |
| `EditorPythonBindings` | later bounded-automation dependency candidate |
| `PythonAssetBuilder` | later importer and validator dependency candidate |
| Unity FBX Exporter | profile-pinned interchange candidate |
| Unity glTFast and Khronos UnityGLTF | later open-format qualification candidates |
| Khronos glTF Validator | later format-validation candidate |
| Unity USD packages | deferred research candidates |

Exact in-tree locations and roles are:

- `Gems/ExternalToolchain` provides registration, configuration, bounded local discovery, and diagnostics.
- `Gems/TaintedGrailModdingSDK` owns FoA identities, evidence, validation, orchestration, and UI.
- `Gems/SceneProcessing` is engine-registered and provides scene-source processing when enabled; current
  project activation and its exact Asset Processor handoff dependency remain a later reviewed gate.
- `Gems/AtomLyIntegration/TechnicalArt/DccScriptingInterface` contains the DCC bootstrap prototype.
- `DccScriptingInterface/Tools/DCC/Blender/Scripts/addons/SceneExporter` contains the Blender exporter.
- `Gems/EditorPythonBindings` and `Gems/PythonAssetBuilder` provide later bounded automation surfaces.

The external candidate inventory contains:

- Blender 5.2 LTS with bundled FBX, glTF, and OpenUSD import/export;
- Unity FBX Exporter 5.1.6 under the Unity Companion License;
- Unity glTFast 6.15.1 under Apache-2.0;
- Khronos UnityGLTF under MIT;
- Khronos glTF Validator under Apache-2.0;
- Unity's replacement USD importer, core, and exporter packages, which remain pre-release or experimental.

These current versions are research observations, not selected compatibility targets. Actual provider support
is bound to the exact application and package versions accepted for one workspace profile.

The O3DE fork describes its Blender integration as a prototype, records initial testing with Blender 3.0, and
defaults its Windows environment to Blender 3.1. Current Blender releases must not be declared compatible from
those observations. The Scene Exporter, DCC bootstrap, current Blender version, and supported operating systems
require an exact qualification matrix.

The in-tree DCCsi request surface, bootstrap, tests, and documentation do not establish a completed Blender
bridge. It remains reference scaffolding until the independent provider and round-trip fixtures pass.

O3DE documents FBX as its primary scene-source format and describes glTF support as in development. The first
interchange therefore uses FBX for qualified geometry and animation payloads plus a project-owned canonical
sidecar. glTF/GLB remains the next open-format candidate after the exact O3DE fork passes importer and
round-trip fixtures. USD remains research-only until both O3DE and the selected Unity profile have accepted,
redistributable, version-pinned implementations.

Unity packages remain native Unity dependencies. The SDK records their exact identities, versions, digests,
licences, and compatibility evidence but does not copy them into the O3DE repository or a FoA package.

### Located connectors not selected

No maintained official live O3DE-to-Unity connector was located in this research cut. File interchange and
new versioned engine-side extensions are therefore the accepted design basis.

The following projects remain research evidence only:

- `GenomeStudios/Unity_to_O3DE_Converter` is an early community converter with no release, unresolved mapping
  gaps, and conflicting licence metadata.
- `kursad-k/o3de_blender_bridge` labels itself work in progress, has no release, and exposes no accepted
  distributable licence.
- the O3DE Blender Whitebox Live Link is an open RFC and prototype, not a shipped Gem;
- `o3de/o3de-technicalart` explicitly contains non-canonical technical-art integrations and has no releases;
- AssetRipper analyzes Unity game files and is outside this authoring-only, no-game-scanning integration scope.

None of these components may be vendored, enabled, or represented as supported without a separate exact
source, licence, compatibility, security, and fixture review.

## Plugin topology

O3DE Gems remain the only editor-plugin packaging and activation mechanism.

### ExternalToolchain host

The existing host remains responsible for:

- stable provider and command descriptors;
- host API compatibility;
- project, user, and session configuration precedence;
- bounded inspection of explicit absolute local paths;
- deterministic discovery results and read-only diagnostics.

An `installed` result continues to prove only that one configured local path exists with a caller-supplied
compatible version. It is not authenticity, licensing, qualification, execution, or runtime permission.

### Proposed Blender provider Gem

Add one ordinary O3DE Tool Gem with the stable provider ID `foa.blender`. Its discovery slice depends only on
`Gem::ExternalToolchain.API`. DCCsi and its Scene Exporter remain source references, not active dependencies.

The first provider slice declares and displays:

- Blender executable and application version;
- Blender plugin or add-on identity, exact version, source revision, and package digest;
- supported host platforms;
- interactive, batch, headless, and asset-source capabilities;
- FBX and sidecar input/output kinds;
- exact compatibility and qualification-fixture versions.

The first slice performs no process launch and installs no Blender add-on. Later export execution requires the
separate process-supervision gate in this design.

DCCsi must not become an active provider dependency unless a separate review proves its auto-bootstrap and
legacy Blender launch actions are removed or disabled and every provider launch routes through the accepted
host supervisor.

### Proposed Unity interchange provider Gem

Add one ordinary O3DE Tool Gem with the stable provider ID `foa.unity-editor`. It describes a separately
installed Unity Editor and an independently packaged Unity Editor extension.

The provider binds:

- exact Unity Editor version;
- exact FoA workspace profile, when the package targets a FoA compatibility context;
- Unity extension package ID, version, source revision, digest, and licence decision;
- supported interchange schema and payload-format versions;
- batch, headless, import, export, validation, and loss-report capabilities;
- one synthetic or user-owned Unity test-project root.

The provider never points at a proprietary FoA project and does not imply that the original game project is
available.

### Proposed native tool extensions

The O3DE providers describe native extensions; they do not replace them.

- Blender uses either a qualified revision of the existing O3DE Scene Exporter or a separately reviewed FoA
  Blender add-on.
- Unity uses a new editor-only package with the provisional ID `com.foa.sdk.interchange`.
- Both extensions consume and produce the same versioned interchange manifest and typed loss report.
- Neither extension contains a game runtime plugin or deployment path.

Native extension names and package IDs become final only when their manifests, licences, tests, and ownership
are reviewed.

## Qualification and trust model

Read-only discovery, TG SDK trust, and execution permission use separate state axes:

```text
ExternalToolchain discovery: registered -> configured -> discovery enabled -> located -> inspected
TG SDK trust/use: inspected -> compatible -> qualified -> explicitly operation enabled
Execution: denied -> provider-specific acceptance -> permitted for one bounded operation
```

The existing ExternalToolchain `Enabled` setting authorises bounded read-only discovery for one provider; it
does not mean qualified, safe to operate, or permitted to execute. The SDK must not collapse discovery
enablement, qualification, operation enablement, and execution permission into one installed/safe flag.

Every qualification record includes:

- stable provider, application, extension, and publisher identities;
- exact semantic versions and package or source revisions;
- lowercase SHA-256 package and executable observations where collection is separately authorised;
- supported operating system and architecture;
- O3DE host API, interchange schema, and application-version ranges;
- declared commands, formats, features, limitations, and required permissions;
- dependency identities and exact versions;
- SPDX licence expression or reviewed `LicenseRef`;
- redistribution and required-notice decisions;
- synthetic fixture version, results, reviewer, evidence IDs, and review time.

A separate provider-state record binds discovery enablement and operation enablement independently to one
workspace or user configuration layer. It references qualification evidence without changing that evidence.

Discovery does not execute plugin code or recursively scan disks, registry hives, Unity Hub data, Blender
configuration, game directories, network shares, or package managers. A tool update invalidates qualification
until the new exact version passes the applicable fixtures.

## Interchange boundary

The first connection is a file-backed, offline handoff:

```text
Blender or Unity test project
    -> immutable staging output
    -> TG interchange manifest and payloads
    -> validation and explicit loss report
    -> O3DE source-asset scan directory
    -> Asset Processor and reviewed catalog evidence
```

Reverse and round-trip directions use the same contract. Direct in-memory object sharing, sockets, network
services, and live Editor-to-Editor control are outside the first interchange slice.

The Unity authoring lane is not the FoA runtime lane. Runtime-facing output continues through the existing
catalog, permission, adapter declaration, work-order, build-manifest, package, deployment-preview, and result
evidence contracts.

## Proposed interchange package

The durable package is a contained directory or deterministic archive with one
`manifest.tginterchange.json`, project-owned payloads, and optional source-native payload references.

Schema 1 contains these field groups:

- schema, package, pack, workspace, and profile identities;
- exact producer application, provider, extension, and configuration identities;
- exact intended consumer and compatibility profile;
- stable asset, revision, binding, material, skeleton, clip, and dependency identities;
- relative payload paths, media types, byte sizes, and lowercase SHA-256 fingerprints;
- coordinate basis, units, transform order, pivot, time basis, and conversion matrices;
- mesh, texture, material, skeleton, animation, collider, and metadata declarations;
- source provenance, authorship where known, licence, attribution, modification, and redistribution state;
- ordered transformation and loss entries;
- validation evidence and exact toolchain lock.

Unknown top-level fields and unsupported schema versions fail closed. Absolute payload paths, traversal,
symlink escapes, case-colliding paths, duplicate identities, unlisted payloads, and fingerprint mismatches are
rejected.

Canonical serialization uses fixed property order, deterministic collection ordering, normalized package
paths, locale-independent numbers, and normalized Unicode where the schema explicitly requires it. Capture
times may be retained as evidence but do not participate in semantic revision identity.

## Identity and binding rules

Filenames, display names, Unity hierarchy paths, Blender object names, and O3DE labels are not durable asset
identities.

The contract uses:

- `PackageId` for one interchange-package lineage;
- `AssetId` for one stable project-owned logical asset;
- `RevisionFingerprint` for normalized semantic content;
- `BindingId` for one canonical-to-native identity mapping;
- exact native identifiers such as Unity GUIDs or O3DE asset identities as binding values;
- exact source locators and fingerprints as provenance, not as display names.

Renames preserve stable identity. A duplicate or fork requires an explicit new-identity or same-lineage
decision. Merge, split, one-to-many, and many-to-one conversions require typed mappings and loss entries.

## Spatial, material, and animation contract

The interchange uses the O3DE authoring basis as its canonical physical space: right-handed, Z-up, metres,
and seconds. Every adapter still records its complete source and target basis and one explicit conversion
matrix. Engine or application names never substitute for the matrix.

Validation covers:

- handedness, up and forward axes, units, scale, winding, and tangent basis;
- local and global transform order, pivots, negative scale, and non-uniform scale;
- normals, tangents, bitangents, UV sets, vertex colours, and level-of-detail declarations;
- stable skeleton hierarchy, bone identities, rest/bind transforms, skin weights, and root motion;
- clip ranges, rational sample rate, interpolation, animation events, and resampling;
- a bounded PBR material subset with colour space, channel packing, opacity, and double-sided state;
- texture transformations, rebakes, recompression, and unsupported shader features.

Application-native graphs, constraints, and procedural rigs may be preserved as source-native references. They
must be baked or mapped explicitly before another host can claim support.

## Loss reporting

Every conversion produces a deterministic typed report. Each entry records:

- affected asset and property path;
- source and target provider;
- conversion phase and stable reason code;
- `information`, `warning`, `error`, or `blocker` severity;
- source feature and resulting representation;
- reversibility and numeric tolerance where applicable;
- supporting evidence identities.

Unsupported information never disappears silently. Preserving a source-native file does not make a lossy
conversion lossless. A `lossless` claim requires the declared feature set and accepted round-trip fixtures to
prove it.

## Process-supervision gate

The current `ExternalToolchain` host cannot execute providers. A later high-risk design unit may add one
host-owned supervisor using argument vectors rather than shell strings.

Before any provider command or native extension runs, that unit must define:

- executable trust and exact-version checks;
- immutable input and isolated writable staging roots;
- environment-variable allowlists and secret redaction;
- bounded runtime, cancellation, process-tree cleanup, output limits, and captured exit status;
- no implicit network access;
- schema-validated structured result output;
- output fingerprinting, containment checks, and atomic publication after validation;
- actionable failure, cleanup, and retry evidence;
- Editor responsiveness and shutdown behavior.

No provider-specific Gem may build a shell command, launch a detached process, write directly to an O3DE
source root, or publish partial output.

## Version lock and reproducibility

Each accepted interchange operation binds one exact lock containing:

- O3DE source revision and TG SDK version;
- interchange schema and profile versions;
- provider Gem and host API versions;
- Blender or Unity Editor version;
- native extension package version, revision, and digest;
- payload-format and converter versions;
- conversion configuration fingerprint;
- synthetic qualification-fixture revision.

Compatibility ranges guide selection only. Every actual result records exact versions. Updating any locked
component creates a new qualification result and never rewrites prior interchange evidence.

## Security, privacy, legal, and runtime boundary

The program must not:

- discover or convert a proprietary FoA Unity project;
- scan a FoA installation or extract copyrighted assets;
- load game assemblies as editor plugins;
- bundle Blender, Unity Editor, Unity packages, or third-party applications without reviewed rights;
- execute imported scripts, Blender files, Unity packages, or O3DE assets during passive inspection;
- accept unrestricted absolute paths, network locations, traversal, or symlink escapes;
- treat plugin signatures, fingerprints, parsing, or import success as runtime permission;
- call Unity, FoA, BepInEx, Harmony, or game APIs from Core, Framework, or Editor;
- deploy content, launch FoA, mutate saves, or automatically promote returned evidence.

Synthetic fixtures use only invented project-owned content. Unknown or incompatible asset or plugin licensing
blocks redistribution and publication while preserving a clearly labelled local review result.

## Failure and rollback

Required failure paths include:

- unknown, duplicate, late, or incompatible provider registration;
- ambiguous tool paths and unsupported application or extension versions;
- missing or rejected licence and redistribution decisions;
- stale qualification evidence or a lock mismatch;
- unsupported interchange schema or payload format;
- malformed, oversized, truncated, or fingerprint-mismatched packages;
- unsafe paths, archive traversal, symlink escapes, and case collisions;
- duplicate, missing, conflicting, or changed identities and native bindings;
- unrecorded coordinate, unit, material, skeleton, animation, or metadata loss;
- process timeout, cancellation, crash, excess output, or incomplete cleanup in a later execution slice;
- Asset Processor rejection or target-host import mismatch;
- persistence failure or round-trip non-equivalence.

Failures leave published workspace, catalog, provider qualification, and source assets unchanged. Rollback of
an implementation is reversion of provider Gems, native extensions, schemas, services, UI, validators,
fixtures, and docs. Existing interchange packages remain preserved or are rejected explicitly; they are never
silently downgraded or truncated.

## Test strategy

### Contract and package tests

Cover canonical serialization, identity stability, dependency order, exact bindings, fingerprints, path
containment, future-schema rejection, duplicate and case-colliding paths, unusual UTF-8, oversized input,
archive traversal, symlink escapes, input non-mutation, and candidate-before-publish failure.

### Geometry and animation fixtures

Use synthetic assets with mirrored transforms, negative and non-uniform scale, multiple UV sets, vertex
colours, packed textures, unsupported material features, morph targets, non-trivial skeletons, root motion,
multiple clips, animation events, and rational sample rates.

### Provider qualification tests

Cover missing, ambiguous, disabled, incompatible, stale, and exact supported versions; extension identity and
digest mismatch; licensing blockers; deterministic capability order; requalification after update; and
ordinary zero-provider Editor state.

### Cross-host tests

Cover Blender-to-package-to-O3DE, O3DE-to-package-to-Blender, O3DE-to-package-to-Unity-test-project, reverse
Unity test export, stable identity, declared numeric tolerances, complete loss reporting, and repeatable output
under the exact lock.

No fixture contains FoA assets, private assemblies, extracted metadata, or a proprietary Unity project.

## Ordered implementation gates

After design approval and satisfaction of the Phase 9 entry prerequisite, proceed in focused units that
preserve the existing `ExternalToolchain` follow-on order:

1. separately reviewed host process supervision, disabled by default and with no provider execution approved;
2. descriptor-generated provider and command UI over the existing registration and configuration services;
3. source-artifact manifests and Asset Processor handoff contracts with candidate evidence return;
4. read-only provider inventory, typed qualification contracts, and Blender Provider Gem discovery;
5. interchange schema-1 contracts, canonical identity, transformation, loss, lock, package validation, and
   synthetic fixtures;
6. separately reviewed Blender native-extension execution through the host supervisor into isolated staging,
   with any DCCsi auto-bootstrap or legacy launch action removed or disabled;
7. reviewed project activation and binding of `SceneProcessing`, O3DE handoff, qualified reverse export, and
   Blender round-trip evidence;
8. Unity Provider Gem plus the editor-only Unity interchange package for synthetic test projects;
9. separately reviewed Unity native-extension execution through the host supervisor;
10. O3DE-to-Unity and Unity-to-O3DE qualification, compatibility matrices, and loss reports;
11. validators, public schemas, headless validation, documentation, and exact-head UI evidence;
12. separately reviewed structured IPC, hot-loading, signing, and third-party trust research;
13. separately reviewed FoA mapping and runtime-adapter payload extensions.

Each unit requires focused design review when it introduces a durable schema, dependency, process execution,
new licence obligation, runtime-facing behavior, or different security boundary.

## Acceptance criteria

The program is accepted only when:

- O3DE Gems remain the editor plugin mechanism and no second loader exists;
- discovery enablement, provider qualification, operation enablement, and execution permission remain separate;
- exact application, extension, provider, schema, and configuration versions are reproducible;
- Blender can transfer a synthetic project-owned asset through the accepted package into O3DE;
- one synthetic Unity test project can exchange the accepted package without implying access to FoA sources;
- canonical identities and exact native bindings survive qualified renames and round trips;
- coordinate, material, skeleton, animation, and metadata changes are explicit and evidence-backed;
- unsupported features produce loss entries or blockers and never disappear silently;
- malformed or hostile packages cannot escape staging or mutate published state;
- licensing, provenance, attribution, and redistribution decisions are complete;
- no game extraction, runtime API call, deployment, FoA launch, or save mutation is introduced;
- focused validators, compiled tests, applicable host builds, documentation, and Windows UI coverage pass for
  the exact accepted head.

## Review boundary

Approval establishes the provider topology, initial located-component inventory, file-backed interchange
boundary, qualification model, and ordered delivery gates.

It does not approve a current Blender version, Unity package version, third-party binary, native add-on,
process supervisor, live bridge, runtime adapter, game mapping, or redistributable bundle until the exact
component passes its own compatibility, licensing, test, and evidence gate.

## Primary research references

- [O3DE scene format support](https://docs.o3de.org/docs/user-guide/assets/scene-settings/scene-format-support/)
- [O3DE scene source assets](https://docs.o3de.org/docs/user-guide/assets/scene-settings/)
- [O3DE DCCsi and Blender prototype notes](https://www.docs.o3de.org/docs/release-notes/archive/2305-0-release-notes/)
- [Blender current release](https://www.blender.org/download/)
- [Blender FBX manual](https://docs.blender.org/manual/en/latest/files/import_export/fbx.html)
- [Unity FBX Exporter](https://docs.unity3d.com/Packages/com.unity.formats.fbx@5.1/manual/index.html)
- [Unity FBX licence](https://docs.unity3d.com/Packages/com.unity.formats.fbx@5.1/license/LICENSE.html)
- [Unity glTFast](https://docs.unity3d.com/Packages/com.unity.cloud.gltfast@6.15/manual/installation.html)
- [Khronos UnityGLTF](https://github.com/KhronosGroup/UnityGLTF)
- [Khronos glTF Validator](https://github.com/KhronosGroup/glTF-Validator)
- [Unity USD package status](https://docs.unity3d.com/Packages/com.unity.exporter.usd@1.0)
- [Community Unity-to-O3DE converter](https://github.com/GenomeStudios/Unity_to_O3DE_Converter/)
- [Community O3DE Blender bridge](https://github.com/kursad-k/o3de_blender_bridge)
- [O3DE Blender Whitebox Live Link RFC](https://github.com/o3de/sig-content/issues/149)
- [O3DE technical-art repository](https://github.com/o3de/o3de-technicalart)
- [AssetRipper](https://github.com/AssetRipper/AssetRipper)
