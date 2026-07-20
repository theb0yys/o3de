# FOA-SDK O3DE to Unity Conversion and Runtime Bridge Research Report

## Executive conclusion

The most viable architecture is **a deterministic, reviewed file handoff from FOA-SDK into a host-supervised
Unity batch conversion project, with result envelopes returning into FOA-SDK as candidate evidence**. In
practice, that means: keep O3DE as the governed authoring system; add a **durable reviewed handoff envelope**
that binds an exact plan, an exact build manifest, and declared source-artifact inputs; let
**ExternalToolchain** own process supervision; let a **Unity Provider Gem** discover and validate a user-local
Unity installation and conversion project; let a **version-locked Unity conversion project** perform
import/build work in batch mode with `-executeMethod`; and return a typed **Unity conversion result** plus an
**external process execution result** back to FOA-SDK without auto-promoting evidence, permissions, or
deployment status. That direction fits FOA-SDK’s existing boundaries, matches the ordered follow-on work
already documented for `ExternalToolchain`, and avoids the two highest-risk shortcuts: direct runtime mutation
from the O3DE editor, and authoring Unity-native files outside Unity.
citeturn5view4turn5view3turn6view0turn31view0turn23view3

The strongest evidence in this research supports the **boundary design**, not the exact game runtime profile.
The repository already has a mature governed foundation, typed adapter contracts, deterministic work-order
planning, build manifests, and runtime-result evidence-return contracts, but it explicitly keeps execution and
build authority disabled. Unity’s official tooling supports batch automation, project-opening, static
entry-point execution, logging, exit codes, custom importers, post-processors, and programmatic AssetBundle or
Addressables builds. BepInEx’s official documentation, however, makes clear that Mono and IL2CPP have different
support assemblies and plugin base classes, and current IL2CPP support is still documented through
bleeding-edge or prerelease channels rather than the long-stable Mono path.
citeturn29view0turn9view2turn9view3turn5view1turn31view0turn23view1turn23view2turn23view4turn23view5turn23view6turn37view2turn37view0turn37view3

The largest unresolved risk is that **the exact Tainted Grail runtime profile still requires lawful local
capture**. Public official sources used in this pass establish the game’s release and continuing patch cadence,
but they do not authoritatively expose the installed build’s exact Unity player version, scripting backend,
assembly layout, Addressables use, or asset loading model. Public community observations strongly suggest that
the game’s normal branch is IL2CPP while a separate Mono branch exists for easier modding, but that is not
strong enough to replace local evidence for implementation authority. The correct repository decision is
therefore: **approve the architecture, the contracts, the host API delta, and the synthetic/process slices now;
do not approve runtime mutation, AssetBundle dependency on game content, or IL2CPP support until Experiment 0
captures the exact target profile from a lawful installation.**
citeturn20search0turn20search3turn34search0turn34search3turn34search4

### First-slice stage disposition

| Stage | Disposition for first implementation slice | Why |
| --- | --- | --- |
| Authoring-data handoff | **Required** | Existing plans/manifests are strong but transient; a durable reviewed handoff is needed. citeturn9view2turn9view3turn5view0 |
| Project-owned source-asset interchange | **Optional, narrow** | Needed only if the vertical slice includes one synthetic asset; otherwise defer. citeturn30view2turn30view0 |
| Unity import and Unity-native asset generation | **Required for Unity bridge proof** | Unity batch mode and `-executeMethod` support this cleanly. citeturn31view0turn23view2turn23view1 |
| BepInEx adapter compilation | **Required, but only for a no-op or identity-binding plugin first** | Proves build/deploy/evidence without save mutation. citeturn37view1turn37view2 |
| Package assembly | **Required at preview/inventory level; archive production optional** | Repository already treats package/release stages as separately gated. citeturn28view0turn5view0 |
| Deployment into a lawful local installation | **Required, manual-reviewed** | Needed to prove end-to-end load evidence; must remain explicit and local. citeturn5view1turn28view0 |
| Runtime mutation through FoA APIs | **Deferred** | Requires exact target profile, bounded capability choice, cleanup, rollback, and legal comfort. citeturn5view4turn29view0 |
| Post-execution evidence capture | **Required** | Already central to FOA-SDK’s model. citeturn5view1 |
| Optional live preview, hot reload, or IPC | **Explicitly deferred** | ExternalToolchain itself lists Unity IPC and hot loading as later research gates. citeturn6view0 |

## Current state and evidence base

### Repository state and what already exists

FOA-SDK is currently a **pre-alpha** O3DE-based modding editor and SDK that explicitly keeps O3DE as the editor
host while keeping **Tainted Grail: The Fall of Avalon** as a **separate Unity runtime target**. The README and
architecture documentation are consistent on the central boundary: the editor and knowledge layers may manage
workspaces, evidence, catalog records, permissions, blockers, plans, handoff documents, and editor-owned
packages, but they must not directly call FoA game APIs, patch the game, load BepInEx into the game, or perform
gameplay mutation inside the editor boundary. The current `main` branch head observed during this research
remains the inspected commit `f216155`, merged on 20 July 2026.
citeturn36view2turn5view4turn22view0turn3view0

The repository already persists the right **editor-side identity spine** for a bridge: workspaces, packs,
source intake, evidence, and catalog state are durable; source and evidence are bound to the exact profile ID,
game version, branch, and runtime target; and the status tool already tracks Mono versus IL2CPP, plus Unity and
BepInEx versions. That is a major advantage: the bridge does not need to invent identity or version tracking
from scratch. citeturn36view3turn36view4

The adapter pipeline is also materially ahead of what a typical modding SDK has. Slice 8 defines typed adapter
identities and the capability vocabulary. Slice 9 defines deterministic canonical work-order plans with stable
plan and step identity and `ExecutionAllowed: false`. Slice 10 defines runtime-result evidence return with step
outcomes, typed failures, cleanup, rollback, safe log references, and SHA-256 fingerprints. Slice 11 defines
reproducible build manifests, including Unity and BepInEx version fields, plan fingerprints, expected outputs,
and `BuildAllowed: false`. Those contracts are precisely the primitives a clean bridge should reuse rather
than bypass. citeturn29view0turn9view2turn5view1turn9view3turn5view0

### Current-state and gap map

| Pipeline concern | Existing component | What it already guarantees | Missing capability | Proposed owner |
| --- | --- | --- | --- | --- |
| Workspace and exact profile | `FoundationService` and status/workspace surfaces | Exact workspace identity, game profile binding, path governance, blockers, and version-bound workspace state. citeturn36view2turn8view3 | Durable bridge handoff export review | TG SDK Core/Framework |
| Governance and permissioning | Catalog/evidence/governance | Validation, permission, prohibition, staleness, and blocker separation; no silent promotion. citeturn36view3turn8view3 | Export authority distinct from runtime authority | TG SDK governance layer |
| Typed adapter identity | `AdapterContractRegistry` and Slice 8 contracts | Exact adapter IDs, semantic versions, runtime targets, typed capabilities, fail-closed compatibility. citeturn29view0 | Durable binding into external handoff/result | TG SDK Core |
| Planning | `AdapterWorkOrderPlanningService` | Canonical step plans with stable step IDs and `ExecutionAllowed: false`. citeturn9view2 | Reviewed export document | TG SDK Core |
| Build definition | `AdapterBuildManifestService` | Exact plan fingerprint, builder metadata, Unity/BepInEx version fields, expected outputs, `BuildAllowed: false`. citeturn9view3turn5view0 | External-tool result binding | TG SDK Core |
| Runtime evidence return | Runtime-result evidence contracts | Step outcomes, typed failures, cleanup, rollback, safe log references, fingerprints. citeturn5view1 | Reuse for external-tool execution result, plus Unity-specific result body | TG SDK Core |
| Package/release preview | Release and package docs | Separate gates for preview, archive, deployment, checksums, release evidence. citeturn28view0 | Unity-generated inventory integration | TG SDK packaging/release layer |
| Tool discovery | `ExternalToolchain` host | Versioned API 1.1.0, deterministic provider registration, layered config, file/directory discovery, diagnostics, `EngineBridge` family. citeturn5view3turn6view0turn9view0 | Process launch, supervision, logs, cancellation, output-root policy | `ExternalToolchain` host |
| Unity discovery | none today | None | Unity Provider Gem | Separate Tool Gem via `ExternalToolchain` |
| Unity conversion | none today | None | Version-locked Unity conversion project plus Editor-only package | User-local Unity conversion project |
| Runtime adapter | external adapters are conceptual and planned | Architecture reserves runtime work for separate reviewed adapters. citeturn5view4turn36view2 | Mono loader path, IL2CPP path, evidence-return binding | Separate runtime package(s) |

### Exact target profile evidence sheet

The exact target profile is the most important missing evidence. Public research can frame the capture plan,
but it cannot currently replace a lawful local observation pass.

| Field | Current status | Classification | Evidence available now | What must capture it next |
| --- | --- | --- | --- | --- |
| Game version/build | **Unknown** | Unknown | Official store/news confirm release and ongoing patching, not the installed local build. citeturn20search0turn20search3 | Capture from local executable, manifests, or in-game/version logs |
| Game branch | **Unknown officially** | Unknown | Public community observation indicates a normal branch and a separate Mono branch for easier modding. citeturn34search0 | Steam branch selection and local manifest capture |
| Runtime target | **Unknown officially** | Unknown | Community evidence strongly suggests default IL2CPP and separate Mono branch. citeturn34search0turn34search4 | Local install inspection for `mono.dll`, managed layout, or IL2CPP markers |
| Unity player version | **Unknown** | Unknown | No official public source in this pass established it. BepInEx docs explain lawful capture methods. citeturn37view1 | Local executable metadata, `globalgamemanagers`, or BepInEx first-run log |
| Managed assembly layout | **Unknown** | Unknown | Community Mono-mod pages imply a Mono layout exists on the Mono branch. citeturn34search3turn34search5 | Local filesystem capture |
| BepInEx distribution/version | **Unknown officially** | Unknown | Community mod pages reference BepInEx 5.4.x for Mono mods. citeturn34search8turn34search5 | Local loader install inspection |
| Addressables use | **Unknown** | Unknown | No official/public evidence in this pass. | Local runtime/file observation |
| AssetBundle use | **Unknown** | Unknown | No official/public evidence in this pass. | Local runtime/file observation |
| Log capture path and load evidence | **Partially known** | Official-platform fact | Unity and BepInEx both document log-file generation mechanisms. citeturn31view0turn37view0 | Bind exact game-specific locations during Experiment 0 |

### Evidence ledger

| ID | Claim | Classification | Source/version | Applicability | Confidence | Limitation | Verification action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E-01 | FOA-SDK is an O3DE-hosted governed editor and not a Unity runtime replacement | Repository fact | README and architecture docs at `main` / commit `f216155` citeturn36view2turn5view4turn22view0 | All bridge design | High | Repository could change later | Reconfirm at implementation slice start |
| E-02 | Work-order plans are canonical but non-executable | Repository fact | `AdapterWorkOrderPlanningService.h` and Slice 9 docs citeturn9view2 | Handoff design | High | Header is compressed in raw view | Reconfirm against implementation files |
| E-03 | Build manifests are canonical but non-building | Repository fact | `AdapterBuildManifestService.h` and Slice 11 docs citeturn9view3turn5view0 | Build boundary | High | None material | Reconfirm |
| E-04 | ExternalToolchain supports discovery/config but not process launch | Repository fact | ExternalToolchain README/architecture/API 1.1.0 citeturn5view3turn6view0turn9view0turn9view1 | Host API delta | High | Provider surface may evolve | Reconfirm API before coding |
| E-05 | Unity supports batch automation, static entry-point execution, logs, and exit codes | Official-platform fact | Unity command-line docs | Unity provider/package | High | Exact editor version still needs binding to FoA | Recheck against exact discovered Unity version |
| E-06 | Unity `.meta` files hold asset IDs and import settings; manual mishandling breaks references | Official-platform fact | Unity asset metadata docs citeturn23view3 | Import/GUID strategy | High | Version-neutral statement; still recheck exact editor version | Keep Unity as sole author of generated asset metadata |
| E-07 | AssetBundles are platform-specific, not forward-compatible, and cannot carry assemblies | Official-platform fact | Unity AssetBundle docs citeturn24view0turn24view2turn23view4 | Asset strategy | High | Exact game loading model still unknown | Run build/load experiments on the exact game target |
| E-08 | BepInEx Mono and IL2CPP are separate support paths | Official-platform fact | BepInEx API/docs/releases citeturn37view2turn37view0turn37view3 | Runtime adapter strategy | High | Game-specific loader choice still unknown | Determine exact target profile locally |
| E-09 | Public community evidence points to default IL2CPP plus a Mono branch for TG modding | FoA-specific observation | Nexus mod page descriptions citeturn34search0turn34search3 | Prioritising Mono-first experiments | Medium | Not official; cannot authorize implementation alone | Confirm branch/runtime locally |
| E-10 | Deterministic C# compilation is supported and useful for trusted-source verification | Official-platform fact | Microsoft compiler/MSBuild docs citeturn19search0turn19search7 | Adapter builds | High | Path and embed settings still need project-specific design | Set and test deterministic build properties |

## Exact meaning of conversion

“Conversion” should not be treated as one feature. In FOA-SDK’s architecture, it is a chain of **different
authorities**, and each authority should remain narrow. The first design decision, therefore, is semantic: the
authoritative editor output is **not** “a Unity mod” and **not** “a deployed game state”. The authoritative
editor output is a **reviewed handoff document** stating what should be imported, built, packaged, or validated
by a separate tool, under exact version and path policy, while keeping execution-allowing flags false until
those later gates exist. That is directly aligned with the repository’s current plan/build contracts and its
explicit refusal to let discovery, planning, or a green build imply runtime safety.
citeturn5view4turn5view0turn5view1turn28view0

### Conversion stages and their proper scope

| Stage | Correct technical meaning in this project | First-slice disposition |
| --- | --- | --- |
| Handoff | Durable, reviewed export of exact plan/build/profile/artifact identities | **Required** |
| Source interchange | Moving project-owned or synthetic source assets into a Unity-visible import root | **Optional, minimal** |
| Unity import | Turning neutral files into Unity-known source assets and importer settings | **Required** |
| Unity-native generation | Producing prefabs, ScriptableObjects, bundles, catalogs, or compiled assemblies inside Unity/.NET tooling | **Required, but minimal** |
| Runtime adapter build | Producing a BepInEx-compatible plugin or generated data package | **Required** |
| Packaging | Producing a declared output inventory and preview; optionally archive later | **Required at inventory level** |
| Deployment | Copying to a lawful local installation under explicit operator review | **Required, manual-reviewed** |
| Runtime mutation | Invoking game APIs/patches or content loads | **Deferred** |
| Evidence return | Returning logs, outputs, hashes, cleanup, rollback, and typed failures | **Required** |
| Live preview / IPC | Mutating or previewing state across processes | **Deferred** |

A practical consequence follows from Unity’s own platform model: **FOA-SDK should not attempt to author
Unity-native files directly**. Unity’s `.meta` files contain GUIDs and import settings, and losing or mismatching
them breaks asset references. Unity also provides first-class importer extension points through
`ScriptedImporter` and `AssetPostprocessor`, which is the right place to turn bridge inputs into Unity-native
representations. The safe baseline is therefore: FOA-SDK writes neutral handoff and source artifacts; Unity
owns `.meta`, import settings, GUID creation for generated assets, and any Unity-native serialized products.
citeturn23view3turn23view1turn23view2

### Domain-neutral interchange

The bridge should preserve a hard separation among five categories of content.

| Category | Where it belongs | Recommended first design |
| --- | --- | --- |
| Semantic game data | FOA-SDK canonical state and handoff | JSON-only, versioned, canonical, fingerprinted |
| Project-owned source assets | User workspace and declared source-artifact manifest | Preserve original project-owned sources; do not clone proprietary game assets |
| Unity-native generated assets | User-local Unity conversion project output root | Generated only by Unity import/build code |
| Runtime adapter configuration | Generated package data and adapter module inputs | Versioned JSON or generated strongly typed module data |
| Evidence/governance metadata | FOA-SDK only | Never promoted into runtime payload unless explicitly needed for verification |

For 3D scene interchange specifically, O3DE’s own documentation still treats **FBX as the primary supported
scene source format**, with glTF support still described as “in development.” That makes a strong case against
assuming a glTF-centric bridge from the O3DE side. The safer design is format-agnostic at the handoff level and
conservative in the initial slice: use semantic JSON everywhere, add PNG/TGA or CSV/JSON where plainly needed,
and only introduce 3D source formats after their exact transformation path has been tested in both authoring
and Unity import stages. citeturn30view0turn30view2

## Recommended end-to-end architecture

### Architectural judgement

The recommended architecture is **Option 1, refined**:

- a **durable reviewed handoff envelope** written by FOA-SDK;
- a **host-owned process supervision layer** inside `ExternalToolchain`;
- a **Unity Provider Gem** that contributes discovery, policy, and typed command descriptors;
- a **version-locked Unity conversion project** that contains an **Editor-only conversion package**;
- a **single authoritative batch command** per reviewed handoff, executed through
  `-batchmode -projectPath -executeMethod -logFile`;
- an output **inventory and result envelope** returned into FOA-SDK as candidate evidence;
- manual, explicit deployment into a lawful local installation only after separate review.
  citeturn6view0turn31view0turn23view0turn25search0turn25search11

This wins because it matches what the repository already is: an O3DE-hosted governed authoring environment
with existing handoff primitives and a host/provider direction for external tools. It also matches what Unity
officially supports best: opening a specific project, running a static method, writing logs, returning exit
codes, and performing import/build work from within the Editor’s own asset pipeline. A temporary project model
looks attractive for isolation, but it makes GUID stability, importer drift, package resolution, and repeated
deterministic builds harder. A pure runtime-adapter-only model looks attractive for simplicity, but it cannot
carry the full future scope once Unity-native assets, asset bundles, or editor-side imported representations
are needed. citeturn5view3turn6view0turn31view0turn23view3turn25search4

### Component diagram

```text
FOA-SDK O3DE Editor
  ├─ Foundation / Catalog / Governance
  ├─ Adapter compatibility + planning
  ├─ Build manifest service
  ├─ Reviewed ExternalToolHandoff writer
  └─ Evidence intake for returned results
           │
           │ reviewed durable JSON + source-artifact manifest
           ▼
ExternalToolchain host
  ├─ provider registry/discovery/config
  ├─ process supervision
  ├─ project lock / concurrency guard
  ├─ log capture + masking
  └─ output-root policy
           │
           ▼
Unity Provider Gem
  ├─ validate Unity install
  ├─ validate conversion project
  └─ execute-handoff
           │
           ▼
Version-locked Unity conversion project
  ├─ Editor-only FOA conversion package
  ├─ importers/postprocessors
  ├─ adapter/data generation
  ├─ optional bundle/addressables build
  └─ UnityConversionResult writer
           │
           ▼
Generated package inventory
  ├─ plugin dll / pdb
  ├─ data json / typed module
  ├─ optional bundles/catalogs
  └─ logs + fingerprints
           │
           ▼
Lawful local game installation
  └─ manual deployment / runtime observation / cleanup / rollback
```

### Trust-boundary diagram

```text
[Public repository boundary]
  FOA-SDK source, schemas, synthetic fixtures, provider descriptors
  NO proprietary game assets or assemblies

[User workspace boundary]
  reviewed handoffs, source-artifact manifests, logs, inventories,
  fingerprints, package previews, user-local configuration

[User local tools boundary]
  Unity editor install path, conversion project path, SDK caches,
  temporary build output, BepInEx build artifacts

[Lawful game installation boundary]
  executable, game assets, user-installed loader/plugin location,
  runtime logs, saves

[Prohibited shortcuts]
  O3DE editor directly calling FoA runtime APIs
  O3DE writing Unity .meta/.prefab/.unity files directly
  auto-promoting evidence as permission or deployment success
```

### Offline conversion sequence

```text
Author reviews pack/profile/plan
  -> FOA-SDK writes ExternalToolHandoff v1
  -> ExternalToolchain validates provider/project/install
  -> host acquires project lock and computes command identity
  -> Unity launched in batch mode with argument vector
  -> Unity package imports neutral inputs
  -> Unity package generates minimal outputs
  -> Unity writes UnityConversionResult v1
  -> host captures exit code/stdout/stderr/log references
  -> FOA-SDK ingests result as candidate evidence only
```

### Runtime execution and evidence-return sequence

```text
Operator explicitly selects lawful installation
  -> deployment preview confirms declared outputs only
  -> operator copies plugin/data into local install
  -> game runs under chosen target (Mono or IL2CPP branch)
  -> runtime plugin records exact profile/plan binding in log/result
  -> FOA-SDK ingests runtime-result evidence
  -> validation/gates remain separate human-reviewed decisions
```

### Failure and rollback sequence

```text
Any mismatch or failure
  -> host stops trusting current run
  -> mark result failed/partial with typed cause
  -> collect logs and inventory of created files
  -> run declared cleanup procedure
  -> if deployment happened, run rollback plan
  -> emit cleanup/rollback outcomes as evidence
  -> never mark package/deployment/runtime validated automatically
```

### Optional later IPC sequence

```text
FOA-SDK request file or IPC message
  -> Unity helper or runtime preview service
  -> read-only preview or bounded status update
  -> durable result still written to file-based envelope
```

The important architectural point is that even after IPC exists, **file-based handoff and result documents
stay authoritative**. `ExternalToolchain` itself already treats Unity IPC and hot loading as later research
gates, and O3DE’s Remote Tools Gem is documented as a debugging-oriented networking feature that is compiled
out for release builds. That makes Remote Tools a poor baseline authority channel for this bridge.
citeturn6view0turn12view5

## Contracts, provider boundaries, and runtime strategy

### Durable contract recommendation

The cleanest contract stack is a **generic outer envelope** plus a **Unity-specific inner request/result body**.

- **Outer request**: `ExternalToolHandoffV1`
- **Inner request**: `UnityConversionRequestV1`
- **Outer result**: `ExternalToolExecutionResultV1`
- **Inner result**: `UnityConversionResultV1`

That is better than handing `AdapterWorkOrderPlan` or `AdapterBuildManifest` directly to Unity, because those
documents were intentionally designed as non-executable, read-only planning/build surfaces. A new envelope can
preserve that invariant by **binding to them** rather than redefining them as execution authority. It also
leaves room for future providers beyond Unity.
citeturn9view2turn9view3turn5view0turn6view0

### Proposed field sets

#### ExternalToolHandoff v1

| Field | Purpose |
| --- | --- |
| `formatVersion` | Schema version |
| `handoffId` | Stable identity for review/export |
| `toolFamily` | `engine_bridge` |
| `providerId` | e.g. `unity.foa.conversion` |
| `providerVersionRange` | Expected provider semver range |
| `profileBinding` | `profileId`, `gameVersion`, `branch`, `runtimeTarget`, `unityVersion`, `bepInExVersion` |
| `packBinding` | `packId`, `packVersion` |
| `planBinding` | `planId`, `planFingerprint`, `planCanonicalJsonSha256` |
| `manifestBinding` | `manifestId`, `manifestFingerprint`, `manifestCanonicalJsonSha256` |
| `catalogFingerprint` | Exact authoring-state invalidation anchor |
| `sourceArtifactManifestFingerprint` | Declared neutral/project-owned inputs |
| `expectedResultId` | Result envelope identity the tool must emit |
| `outputPolicy` | safe relative output roots and collision policy |
| `redistributionPolicy` | declared redistributability decisions |
| `reviewBinding` | reviewer/export approval identity |
| `buildAllowed` | default `false` |
| `executionAllowed` | default `false` |
| `deploymentAllowed` | default `false` |
| `canonicalJson` | canonical serialized body |
| `handoffSha256` | lowercase fingerprint of canonical JSON |

#### UnityConversionRequest v1

| Field | Purpose |
| --- | --- |
| `requestedOperations` | `import`, `generate_adapter`, `build_bundles`, `validate_package` |
| `unityProjectPolicyId` | Bind to expected project config |
| `projectRelativeImportRoot` | Where declared neutral files are staged |
| `projectRelativeOutputRoot` | Where generated outputs may appear |
| `assetInputs` | Media kinds, relative locators, fingerprints, redistributable flags |
| `semanticInputs` | JSON payload locators/fingerprints |
| `importSettingsPolicy` | Names importer/postprocessor preset set |
| `bundlePolicy` | Absent or explicit; off by default |
| `addressablesPolicy` | Absent or explicit; off by default |
| `adapterTarget` | `mono` or `il2cpp`, never both in one execution |
| `resultSchema` | Expected Unity result schema/version |

#### ExternalToolExecutionResult v1

| Field | Purpose |
| --- | --- |
| `resultId` | Stable identity |
| `handoffId` / `handoffSha256` | Exact request binding |
| `providerId` / `providerVersion` | Provenance |
| `commandId` | What was executed |
| `installationIdentity` | Discovered install path fingerprint + version |
| `startTimestampUtc` / `endTimestampUtc` | Trusted host timing |
| `argumentVectorFingerprint` | Deterministic command identity |
| `workingDirectoryFingerprint` | Containment evidence |
| `stdoutRef` / `stderrRef` | Safe references plus hashes |
| `exitCode` | Process outcome |
| `outcome` | `success`, `failed`, `timed_out`, `cancelled`, `policy_refused`, `partial` |
| `cleanupOutcome` | Host-side cleanup result |
| `childCleanupOutcome` | Process-tree cleanup result |
| `outputInventoryFingerprint` | Result artifact manifest hash |
| `typedFailures` | Structured host/provider failures |

#### UnityConversionResult v1

| Field | Purpose |
| --- | --- |
| `resultId` | Must equal expected result identity |
| `handoffBindings` | Exact plan/manifest/profile/pack references |
| `unityEditorVersion` | Actual editor version used |
| `conversionProjectFingerprint` | Proves project identity |
| `importSummary` | Counts and statuses by media kind |
| `generatedAssetInventory` | Paths, roles, media types, hashes |
| `generatedAdapterInventory` | DLL/PDB/generated-data/module hashes |
| `bundleInventory` | Optional; absent in first slice |
| `addressablesInventory` | Optional; absent in first slice |
| `warnings` | Structured warnings |
| `typedFailures` | Import/compiler/build failures |
| `unityLogRef` | Safe reference + hash |
| `compilerLogRef` | Safe reference + hash |
| `cleanupSuggested` | Whether rollback/cleanup is required before retry |
| `canonicalJson` / `sha256` | Deterministic result verification |

The important constraint is that **no durable contract should contain private absolute paths**.
`ExternalToolchain` today already uses user/session/project/provider-default configuration layering and bounded
inspection of configured absolute local paths. That pattern should continue: absolute paths stay in Settings
Registry or ephemeral execution state; durable envelopes only store safe relative locators, fingerprints, and
discovered-installation IDs. citeturn6view0turn9view0turn12view2

### ExternalToolchain API delta

`ExternalToolchain` should grow by **separate reviewed slices**, not by burying launch logic inside a provider.

| New host capability | Why it belongs in host, not provider |
| --- | --- |
| `ExecuteCommand(request)` | Central policy, diagnostics, timeout, locking, masking |
| `CancelCommand(commandRunId)` | Uniform cancellation surface |
| `GetCommandRunResult(commandRunId)` | Read-only result inspection |
| `OnCommandRunUpdated` notifications | UI/progress without provider-specific polling |
| Output-root enforcement | Prevent path escape and overwrite |
| Environment allowlist | Stop secret leakage and provider-specific surprises |
| Per-project concurrency lock | Unity only allows one instance per project |
| Log capture and hashing | Evidence consistency |

The technical basis is already present in O3DE. The official `AzFramework::ProcessLaunchInfo` supports a
process executable path, a working directory, environment variables, `m_tetherLifetime`, and command-line
parameters represented as either a string or a `vector<string>`. That is enough to justify using **argument
vectors** as the baseline representation while forbidding ad hoc shell strings in FOA-SDK’s new host API.
`AZ::Interface` is also the right performance-oriented singleton pattern for the host service, while EBus
remains suitable for notifications and Editor-facing decoupling.
citeturn32search0turn30view3turn30view4

A minimal proposed request/result pair is:

```text
ExternalToolCommandRequest
  providerId
  commandId
  discoveredInstallationId
  executablePathToken
  argumentVector[]
  workingDirectoryToken
  handoffId
  handoffSha256
  permittedOutputRootToken
  environmentAllowlist[]
  timeoutMs
  supportsCancellation
  projectLockKey

ExternalToolCommandResult
  commandRunId
  outcome
  exitCode
  startTimestampUtc
  endTimestampUtc
  stdoutRef + sha256
  stderrRef + sha256
  processLogRef + sha256
  outputInventoryRef + sha256
  cleanupOutcome
  childCleanupOutcome
  typedFailures[]
```

### Unity Provider Gem specification

The provider should be a **separate O3DE Tool Gem** that registers as an `EngineBridge` provider with minimum
host API `1.2.0` or whatever the first process-capable host version becomes.

Recommended descriptor shape:

| Field | Proposed value |
| --- | --- |
| `providerId` | `unity.foa.conversion` |
| `displayName` | `Unity FOA Conversion` |
| `toolFamily` | `EngineBridge` |
| `minimumHostApiVersion` | first process-capable host version |
| `platforms` | Windows first; others only after FoA target support is evidenced |
| `capabilities.supportsBatch` | `true` |
| `capabilities.supportsHeadless` | `true` |
| `capabilities.producesAssetSources` | `false` in first slice |
| `capabilities.supportsStructuredIpc` | `false` in first slice |

Recommended command set:

| Command | First-slice status | Notes |
| --- | --- | --- |
| `validate-unity-installation` | Keep | `-version` plus path validation and version policy |
| `validate-conversion-project` | Keep | Fingerprint project manifest/settings/packages |
| `execute-handoff` | Keep | One authoritative batch run per reviewed handoff |
| `validate-generated-package` | Optional | Could be split from execute at later stage |
| `build-asset-bundles` | Defer | Only after target profile proves bundles are needed |
| `build-runtime-adapter` | Fold into `execute-handoff` first | Avoid multiple Unity launches per slice |
| `emit-conversion-result` | Internal to `execute-handoff` | Result document written by Unity package |

That split deliberately favours **one Unity launch per handoff**. Unity’s own batch documentation makes
single-project concurrency a hard operational fact, and repeated launches increase import noise and lock
contention. citeturn23view0turn31view0

### Unity conversion project and package specification

The best Unity-side boundary is **Model 1 with an embedded package discipline**: a **dedicated version-locked
Unity conversion project** that includes a reusable **Editor-only conversion package**. The project owns exact
editor version, project settings, package lock state, samples, and GUID-bearing scaffold files. The package owns
the import/build logic, tests, and batch entry points. Unity’s official package workflow supports reusable
packages, but package-only reuse does not by itself solve project-level reproducibility, GUID stability, or
build-graph determinism. citeturn25search0turn25search4turn25search11turn25search12

Recommended layout:

```text
FOA-Unity-ConversionProject/
  Packages/
    com.foa.conversion/
      Editor/
        BatchEntryPoints.cs
        Importers/
        Postprocessors/
        Builders/
        ResultWriters/
      Runtime/           # optional later, likely empty in first slice
      Tests/
      package.json
  Assets/
    SyntheticFixtures/
    Generated/           # ignored or cleaned
  ProjectSettings/
  Packages/manifest.json
```

Recommended Unity entry points:

- `FOA.Conversion.Batch.ValidateProject`
- `FOA.Conversion.Batch.ExecuteHandoff`
- `FOA.Conversion.Batch.ValidateGeneratedPackage`

Batch invocation should use `-batchmode -quit -projectPath ... -executeMethod ... -logFile ...`, optionally
`-accept-apiupdate` and `-buildTarget` where required. The host should also pass `-version` for install
validation. All scripts used with `-executeMethod` must live in an Editor folder and be static, exactly as Unity
documents. citeturn31view0

### Runtime adapter strategy

The best long-term runtime strategy is **Strategy C: a hybrid adapter**.

- A **stable runtime core** owns loader metadata, exact handoff/result binding, capability dispatch, logging,
  cleanup, rollback, and evidence return.
- **Generated data or strongly typed registration modules** describe the specific mod payload for a reviewed
  handoff.
- When no Unity-native assets are needed, the generated payload can stay mostly neutral and data-driven.
- When Unity-native representations are needed, the payload can include references to assets produced by the
  conversion project.

That is a better fit than a fully generic adapter, because FOA-SDK already models typed capabilities and exact
step identities, and future domains will likely need some generated strongly typed binding without forcing
complete source generation for every mod. It is also a better fit than fully generated adapter source, which
would maximize code-review surface, legal risk, and attack surface at the precise point where the repository is
trying to stay fail-closed. citeturn29view0turn5view1turn36view2

**Mono and IL2CPP must be treated as separate targets from the start.** Official BepInEx documentation shows
different support assemblies and base plugin classes for Mono and IL2CPP, and official IL2CPP installation
guidance remains tied to bleeding-edge builds. The first runtime implementation slice should therefore target
**one runtime only**, and the current best inference is **Mono first** if Experiment 0 confirms the user intends
to work against the Mono branch. If Experiment 0 instead proves the target branch is IL2CPP-only, then the
architecture still stands, but the runtime slice becomes riskier and should not be merged without an
additional design review.
citeturn37view2turn37view0turn37view3turn34search0turn34search3

## Options, security, and legal assessment

### Options decision matrix

The scores below are an evidence-based inference, not a repository fact. Weighting favours architectural fit,
determinism, security, and future domain coverage.

| Option | Contract fit | Reproducibility | Runtime coverage | Security/trust | Legal/distribution clarity | Weighted judgement |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Deterministic file handoff + headless Unity project | 5 | 5 | 4 | 5 | 4 | **Best overall** |
| Interactive Unity Editor bridge | 3 | 2 | 4 | 3 | 4 | Useful later, not baseline |
| Generic BepInEx runtime adapter with neutral data only | 4 | 4 | 2 | 4 | 4 | Good fallback for asset-free domains |
| Generated adapter source + Unity/.NET build | 3 | 4 | 4 | 2 | 3 | Too much codegen surface too early |
| Hybrid offline conversion + optional live IPC | 5 | 4 | 5 | 4 | 4 | **Second-best target state**, but IPC later |

Option 1 ranks highest because it is the closest match to FOA-SDK’s present contract stack and to Unity’s
officially documented automation path. Option 5 is the likely **future target architecture**, but only once the
file-based authority path is proven first. Option 3 remains strategically important: for some semantic-only
domains, the bridge should be able to bypass Unity-native asset generation entirely and ship only a data
package plus stable runtime core. That is why the recommended contract stack is provider-neutral at the outer
envelope. citeturn6view0turn31view0turn24view0turn23view5turn37view2

### AssetBundle and Addressables judgement

AssetBundles should be treated as **deferred and experimental**, not assumed. Unity’s official documentation
is explicit that AssetBundles are platform-specific, not forward-compatible, and cannot carry assemblies.
Addressables in turn build catalogs and bundles, support remote catalogs, and can even load catalogs from other
projects, but none of that answers whether **FoA itself** uses Addressables, raw AssetBundles, `Resources`, or
custom loaders. Until the exact local runtime profile is captured, the bridge should not make AssetBundles part
of the first slice. The first slice can prove the architecture with a no-op or identity-bound plugin plus
optional synthetic asset import only.
citeturn24view0turn24view2turn23view4turn23view5turn23view6

### Threat model and risk register

| Threat or failure | Consequence | Prevention | Detection | Recovery |
| --- | --- | --- | --- | --- |
| Replaced/malicious Unity executable | Arbitrary code execution | Discover only configured local absolute paths; fingerprint install; host allowlist | Install fingerprint mismatch | Refuse execution |
| Shell/argument injection | Arbitrary commands | Host API accepts argument vectors, not free-form shell strings | Command fingerprint mismatch / audit | Refuse and log |
| Unsafe working directory or output root | File overwrite / path escape | Host-issued root tokens, relative outputs only | Output path validation | Abort, clean partials |
| Unity project opened concurrently | Corrupt import/build state | Per-project host lock | Lock failure | Refuse second run |
| Manual `.meta` editing outside Unity | Broken GUID references | FOA-SDK never authors Unity-native metadata | Import/reference errors | Reimport from trusted sources |
| Wrong Unity version | Invalid import or bundle output | Provider version policy and `-version` validation | Version mismatch at validate stage | Refuse execution |
| Wrong runtime target | Plugin load failure | Separate Mono/IL2CPP target profiles and builders | Runtime logs / evidence mismatch | Cleanup and retry on correct target |
| Stale plan/handoff mismatch | Output no longer matches reviewed state | Bind all envelopes by fingerprint | Fingerprint validation failure | Regenerate handoff |
| Child process survives editor shutdown | Orphan process / locked project | Host tethered lifetime + process tree cleanup | Cleanup outcome | Terminate tree, mark partial |
| Malicious imported asset or package dependency | Import-time exploit / unstable project | Minimise dependencies, pin package versions, review package manifest | Project fingerprint drift | Recreate from trusted project state |
| Save/game installation corruption | User data loss | First slice avoids mutation; later slices require backup + rollback | Deployment/result evidence | Explicit rollback and manual restore |
| Spoofed result envelope | False evidence | Result ID and SHA-256 must bind to expected handoff/result contract | Hash mismatch | Reject result |

The legal/content boundary materially narrows what the bridge is allowed to do. FOA-SDK’s own policy allows
original code, documentation, lawfully shared metadata and observations, synthetic fixtures, and tools acting
on a user’s own lawful installation, while prohibiting the public redistribution of proprietary executables,
assemblies, archives, extracted assets, ripped media, decompiled classes, credentials, or private paths. That
means the repository may contain schemas, fingerprints, synthetic fixtures, provider/package code, and
import/build logic; a user workspace may contain reviewed handoffs, local logs, and references to lawful local
game inputs; but proprietary game files should remain user-local and generally referenced, not copied, by the
bridge. citeturn5view2turn28view0

### Legal and redistribution checklist

| Content class | Public repository | User-local workspace | Runtime-only observation |
| --- | --- | --- | --- |
| FOA-SDK C++/docs/schemas/tests | Allowed citeturn5view2 | Yes | N/A |
| Synthetic JSON/CSV/image fixtures | Allowed citeturn5view2 | Yes | N/A |
| Unity Provider Gem source | Allowed | Yes | N/A |
| Unity conversion package/project scaffold without proprietary content | Allowed, if licence-compliant | Yes | N/A |
| Machine-specific Unity install paths | No | Yes, in user/session config | N/A |
| Game executable / assemblies / assets | No | Read-only local reference only | Yes |
| Extracted proprietary bundles/media/classes | No | Prefer not stored; if observed, keep local and controlled | Yes |
| Logs containing private paths | No | Yes, but redact before promotion | Yes |
| Generated plugin DLLs from user-local lawful build | Generally user-local unless legal review says otherwise | Yes | Yes |
| Editor/build server licensing assumptions | No blanket claim | User must satisfy Unity plan terms | N/A |

Unity’s current Editor terms also define a “Machine” in Build Server terms and make clear that software access
rights and plan terms govern how editor automation can run. This report cannot conclude which exact Unity plan
is required for a given setup, but it does conclude that **licensing review must be part of public distribution
planning** if the bridge relies on unattended batch builds or shared build machines. citeturn23view7

## Smallest vertical slice, experiments, roadmap, and ADR

### Smallest vertical slice

The best smallest end-to-end slice is **smaller than the candidate item/recipe slice in the brief**:

**reviewed handoff → supervised Unity batch run → generated no-op BepInEx plugin → package inventory → manual
local deployment → plugin load evidence → cleanup → rollback evidence**

This is the right smallest slice because it proves all the new boundaries that actually matter:

- durable reviewed export;
- ExternalToolchain process supervision;
- Unity install/project validation;
- exact batch invocation;
- deterministic generation;
- output inventory;
- deployment preview/manual install;
- runtime log evidence;
- cleanup and rollback reporting.

By contrast, a synthetic non-Unity process fixture is **too small** because it does not prove the Unity
boundary, and an item/recipe mutation slice is **too large** because it introduces gameplay mutation and
save-state risk before the bridge foundations are proven.
citeturn6view0turn31view0turn37view1turn5view1

### Experiment and validation plan

| Experiment | Hypothesis | Acceptance criterion |
| --- | --- | --- |
| Exact environment inventory | Exact FoA profile can be captured without public redistribution of proprietary files | Redacted evidence sheet with version/build/branch/runtime/Unity/BepInEx/paths/fingerprints |
| Synthetic process supervision | Host can launch, time out, cancel, lock, and capture logs safely | Canonical result for success/failure/timeout/cancel cases |
| Unity discovery and version binding | Provider can identify and refuse wrong or ambiguous installs/projects | Deterministic discovery result and failure states |
| Minimal handoff import | Unity package can consume reviewed handoff and emit a result envelope | Success without proprietary assets |
| Project-owned asset conversion | One synthetic asset can round-trip with known import policy | Stable import summary and known loss budget |
| Deterministic rebuild | Same inputs repeat to byte-identical or semantically identical outputs | Hash equivalence where possible; normalized semantic compare elsewhere |
| No-op plugin load | Generated plugin binds to exact plan/profile and loads without gameplay mutation | Runtime log proves load and identity |
| One bounded capability | Chosen smallest capability can execute with backup/cleanup/rollback | Independent verification and reversible outcome |
| Negative compatibility tests | Wrong versions, stale handoffs, collisions, missing inputs all fail closed | Typed failure precedence and no false success |
| Recovery/idempotence | Re-running import/build/deploy does not duplicate or corrupt state | Stable identities, explicit replacement rules, complete cleanup |

### Phased implementation roadmap

| Slice | Purpose | New authority introduced | Authority still prohibited | Gate to next slice |
| --- | --- | --- | --- | --- |
| Research and schema slice | Approve contracts, ADR, provider design | Durable reviewed handoff documents | No process launch | Design review accepted |
| Host process supervision slice | Add command execution, logs, cancellation, locking | Launch trusted local process under host policy | No Unity provider, no game deployment | Synthetic process fixture passes |
| Unity provider validation slice | Add Unity/project discovery and validation | Validate configured local Unity/project paths | No handoff execution yet | Provider validation passes |
| Unity execution slice | Execute reviewed handoff in batch mode | Unity import/build and result emission | No gameplay mutation, no AssetBundles unless explicitly included | No-op plugin slice passes |
| Runtime load evidence slice | Manual install and no-op plugin load | Local deployment into lawful install | No save mutation, no capability execution | Load/cleanup/rollback evidence passes |
| First bounded capability slice | Execute one safe typed capability | Minimal runtime mutation | No broad gameplay mutation, no IL2CPP unless separately approved | Independent verification passes |
| Asset/native content slice | Add bundles or Addressables only if required | Unity-native asset generation and loading | No live IPC authority | Exact compatibility experiments pass |
| Optional IPC slice | Add preview/status IPC | Bounded read-only or preview communication | No replacement of file authority | Security and replay tests pass |

### Recommended design-review decision

Approve **the architecture, schemas, host API delta, Unity Provider design, and smallest vertical slice**. Do not
yet approve runtime mutation, automatic deployment, AssetBundle-based first-slice assumptions, IL2CPP support,
or any feature that treats a discovered tool, a successful build, or a successful process exit as proof of
compatibility or safety. citeturn6view0turn28view0turn24view0turn37view3

### Explicitly deferred capabilities

Deferred until later gates:

- live IPC and hot reload;
- AssetBundle/Addressables assumptions;
- IL2CPP runtime path;
- generated broad gameplay mutation;
- direct authoring of Unity-native project files outside Unity;
- auto-promotion of result evidence into permission, validation, or deployment success.
  citeturn6view0turn24view0turn23view3turn5view1

### Blocking unknowns

The following remain blocking unknowns before runtime implementation authority:

- exact FoA installed version/build;
- exact branch selection in use;
- exact runtime target for the chosen branch;
- exact Unity player version;
- managed assembly layout;
- actual use or non-use of Addressables/AssetBundles/Resources/custom loaders;
- exact runtime APIs available for the chosen capability;
- exact Unity licensing posture for the intended automation/deployment model.
  citeturn20search0turn34search0turn37view1turn23view7

### Experiments needed before implementation authority expands

Implementation should not move beyond the no-op runtime slice until:

- Experiment 0 captures the exact target profile;
- synthetic process supervision passes;
- Unity provider validation passes;
- deterministic rebuild evidence exists;
- cleanup and rollback evidence passes;
- at least one negative compatibility matrix is run successfully.
  citeturn5view1turn28view0turn6view0

### Draft architecture decision record

**Context.** FOA-SDK already has governed authoring, exact profile tracking, typed adapter contracts,
deterministic plan/build definitions, and result-evidence concepts. It also has a host/provider external-tool
direction through `ExternalToolchain`, but no process execution or Unity provider yet. Unity provides official
batch automation and importer/build APIs, while forcing project-level control over GUID-bearing metadata and
import state. BepInEx Mono and IL2CPP are distinct runtime targets.
citeturn5view4turn6view0turn31view0turn23view3turn37view2

**Decision.** Introduce a durable reviewed `ExternalToolHandoff` envelope, add host-owned process supervision
to `ExternalToolchain`, create a Unity Provider Gem, and use a version-locked Unity conversion project
containing an Editor-only conversion package. Start with a no-op BepInEx plugin slice and Mono-first only if
Experiment 0 confirms a Mono target branch. Keep runtime-result and evidence promotion separate from
build/process success. citeturn6view0turn31view0turn37view1turn5view1

**Alternatives considered.** An interactive Unity bridge is useful later but too weak on determinism. A pure
generic runtime adapter is attractive for asset-free domains but insufficient as the only path for future
Unity-native assets. Fully generated adapter source expands review and attack surface too early. Optional IPC
is valuable only after file-based authority is proven.
citeturn31view0turn24view0turn37view2

**Consequences.** The repository gains new durable schemas and a reviewed host-execution boundary, but
preserves the editor/runtime separation. Machine-specific Unity paths remain in user/session configuration.
Unity-native files remain authored by Unity. Mono and IL2CPP stay separate. AssetBundles and Addressables
remain experimental. citeturn6view0turn12view2turn23view3turn24view0

**Security and privacy.** Use argument vectors, output-root containment, project locks, environment allowlists,
log hashing, and cleanup reporting. Do not store private absolute paths or proprietary game files in public
artifacts. citeturn32search0turn6view0turn5view2

**Schema and migration.** Add `ExternalToolHandoffV1`, `UnityConversionRequestV1`,
`ExternalToolExecutionResultV1`, and `UnityConversionResultV1` as new versioned contracts. Keep unknown-version
handling fail-closed. Bind all document identities with lowercase SHA-256 of canonical JSON.
citeturn9view2turn9view3turn5view1

**Tests.** Require synthetic host command tests, Unity validation tests, deterministic rebuild tests, no-op
plugin load tests, negative compatibility tests, and rollback/idempotence tests before any bounded gameplay
mutation. citeturn28view0turn31view0turn37view0

**Rollout.** Research/design → host supervision → provider validation → Unity execution for no-op plugin →
runtime load evidence → one bounded capability. citeturn6view0turn28view0

**Rollback.** Revert new host/provider slices independently; durable handoff/result documents remain review
artefacts only and do not automatically mutate game or validation state. Remove deployed outputs using
declared cleanup/rollback steps and preserve evidence of the removal.
citeturn5view1turn28view0

**Unresolved questions.** Exact FoA runtime profile, exact loading model for Unity-native content, exact first
safe capability, exact Mono/IL2CPP branch strategy for the user’s workflow, and final legal comfort for
unattended Unity automation against public distribution goals.
citeturn34search0turn23view7
