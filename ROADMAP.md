# Tainted Grail Modding Editor and SDK Roadmap

This roadmap describes capability order, not promised dates. Work is promoted when architecture, evidence, validation, documentation, tests, and build quality are sufficient.

## Guiding rule

Every authoring feature must use the shared workspace, pack ownership, source/evidence, canonical catalog, validation, risk, staleness, permission, and prohibition infrastructure. Domain tools must not create private identity systems, grant their own permissions, or bypass blockers.

## Phase 0 — Project foundation

Status: implemented, continuing hardening.

- O3DE editor Gem and host-tool registration.
- Editor-only product boundary.
- Focused repository validation.
- Full public README, user and contributor guides, architecture, quality, design-review, pre-commit review, PR review, security, conduct, governance, privacy, legal/content, accessibility, support, release, roadmap, changelog, issue forms, PR template, and CODEOWNERS.
- Two-branch development model.

## Phase 1 — Workspace and exact game profile

Status: implemented, continuing hardening.

- Workspace identity and paths.
- Exact FoA installation, version, branch, runtime target, Unity version, BepInEx version, assemblies, diagnostics, and extracted-data locations.
- Durable workspace JSON.
- Blockers for incomplete build identity and pipeline paths.

## Phase 2 — Mod and content-pack projects

Status: implemented, continuing hardening.

- Pack-owned stable identities.
- Semantic versions and compatibility.
- Dependencies, required mods, and incompatibilities.
- Save impact and content/resource declarations.
- Durable pack-manifest JSON.

## Phase 3 — Source and evidence intake

Status: implemented, continuing hardening.

- SHA-256 fingerprinting.
- Exact profile/build binding.
- Structured JSON and CSV extraction.
- Generic artifact intake without inferred evidence.
- Durable source/evidence documents.
- Import and schema issues.

## Phase 4 — Canonical catalog browser and record inspector

Status: implemented, continuing hardening.

- Durable `Catalog/catalog.tgcatalog.json` document bound to workspace/profile/version/branch.
- Stable canonical records, first-class relationships, validation history, and governance history.
- Search by exact native reference, GUID, record ID, subject, alias, domain, kind, pack, maturity, confidence, risk, validation, staleness, permission/prohibition, evidence, blocker state, and supersession.
- Inspector for identity, ownership, evidence, relationships, versions, history, permissions, conflicts, missing references, and blockers.
- Evidence-backed claim promotion into reviewed-but-unvalidated, staleness-unknown records.
- Native exact-ref uniqueness and synthetic pack ownership.
- No display-name identity merging.
- Transactional save-before-publish lifecycle.

## Phase 5 — Validation, maturity, risk, and permission engine

Status: implemented, continuing hardening.

- Independent maturity, confidence, operational risk, validation, staleness, permission, and prohibition states for records and relationships.
- Usage-specific allow, forbid, and clear decisions.
- Validation events bound to exact profile, game version, branch, evidence, method, and named validator.
- Permission grants require a separate reviewed decision and validated proof for the same subject.
- Stale and potentially stale subjects automatically lose allowed usages.
- Supersession records a replacement, marks the old subject stale, removes allowed usages, and preserves history.
- Append-only governance history with evidence, validation proof IDs, reviewer, time, and notes.
- Governance blockers for unknown assessments, stale subjects, missing proof, missing history references, and profile mismatch.
- Dedicated **Tainted Grail Catalog Governance** editor pane.
- Unit tests for validation/permission separation, proof requirements, stale-state revocation, relationship governance, and supersession.

## Phase 6 — Domain authoring tools

Status: active development.

All domain tools use canonical IDs, source/evidence provenance, governance decisions, blockers, and the same transactional catalog document.

### Economy and content

#### Item and Recipe Editor

Status: implemented, continuing hardening and evidence coverage.

- Typed item profiles keyed to canonical `economy/item` records.
- Typed recipe profiles keyed to canonical `economy/recipe` records.
- Canonical crafting-station references.
- Ingredient joins with quantity, alternatives, consumption, conditions, and evidence.
- Output and by-product joins with quantity, chance, conditions, and evidence.
- Item flags and references for quest sensitivity, uniqueness, hidden state, localisation, icons, and assets.
- Recipe type, tab, unlock, duplicate key, and persistence description.
- First-class `sold_by`, `dropped_by`, `found_at`, `rewarded_by`, `learned_from`, `granted_by`, and `crafted_at` relationships.
- Separate existing-item, existing-recipe, runtime-append, custom-registration, asset/localisation, vendor/loot, and reward lanes.
- Read-only lane matrices; permission remains owned by Catalog Governance.
- Read-only station visibility and learnability evidence rows derived from exact recipe/station IDs, `crafted_at` and `learned_from` relationships, evidence, governance state, and blockers.
- Economy blockers for missing profiles, evidence, stations, outputs, unresolved joins, quest/unique risks, and identity-incompatible lanes.
- Transactional persistence inside `Catalog/catalog.tgcatalog.json`.
- Unit tests for profile identity, stations, joins, chance/quantity, round-trip persistence, acquisition defaults, lane status, deterministic evidence rows, fail-closed evidence/governance, and non-mutation.

Exit criteria:

- item and recipe profiles survive workspace reload;
- an item record cannot masquerade as a recipe record;
- native and synthetic action lanes remain separate;
- stations, ingredients, outputs, and acquisition relationships preserve canonical identity and evidence;
- profile and join writes reject missing or unrelated evidence;
- action lanes and evidence views remain read-only in the domain tool;
- station and learnability research never implies runtime capability;
- no item or recipe authoring command invokes FoA runtime code.

#### Economy acquisition coverage dashboard

Status: implemented, continuing hardening and Windows UI verification.

- Pure Core analysis over canonical economy records, acquisition relationships, exact evidence bindings, governance state, and open blockers.
- Item vendor, loot, and reward lanes.
- Recipe reward, learnability, and crafting lanes.
- Deterministic `covered`, `partial`, `blocked`, and `missing` statuses.
- Read-only Editor pane with relationship, evidence, blocker, and reason details.
- Fail-closed handling for unknown evidence, mismatched source bindings, unrelated evidence subjects, unresolved targets, stale or invalid governance, and open blockers.
- Unit coverage for deterministic lane separation and input non-mutation.
- Focused static validator, documentation contract, and CI integration.
- No schema change, permission grant, runtime adapter, deployment, game launch, or save mutation.

Exit criteria:

- every canonical economy item and recipe receives only its applicable lanes;
- lane and row aggregation remains deterministic and fail-closed;
- a covered relationship cannot hide another blocked or partial relationship in the same lane;
- the Core service remains free of Qt, AzToolsFramework, persistence, and Framework dependencies;
- the Editor dashboard remains non-editable and cannot author governance or acquisition state;
- the Windows manual UI checklist includes the pane and its synthetic-data display.

#### Economy cross-pack duplicate report

Status: implemented, continuing hardening and Windows UI verification.

- Pure Core analysis of pack-owned canonical economy items and recipes.
- Exact, case-sensitive grouping by record kind plus `subjectRef`.
- Exact, case-sensitive recipe grouping by typed `duplicateKey`.
- Cross-pack gating that requires at least two distinct owner packs.
- Deterministic `review_required`, `partial`, and `blocked` states.
- Evidence source/profile/build/branch verification and exact-subject checks.
- Fail-closed handling for missing profiles, invalid evidence, stale/failed state, missing refs, conflicts, supersession, and open blockers.
- Read-only Editor pane with exact keys, owner packs, canonical records, evidence, blockers, and reasons.
- No display-name, alias, localisation, tag, asset-path, case-folded, or fuzzy identity matching.
- Focused C++ tests, static validator, documentation contract, CI integration, and Windows manual UI coverage.
- No schema change, automatic merge, pack rejection, winner selection, permission grant, runtime adapter, deployment, launch, or save mutation.

Exit criteria:

- exact shared subjects across distinct packs produce candidate groups without display-name heuristics;
- exact recipe duplicate keys can group different recipe subjects across packs;
- same-pack repeats and case-different keys do not produce cross-pack groups;
- candidate health escalates deterministically from `review_required` to `partial` or `blocked`;
- report generation never mutates catalog, typed profile, source/evidence, governance, or blocker state;
- the Core service remains free of Qt, AzToolsFramework, persistence, and Framework dependencies;
- the Editor report remains non-editable and does not decide which record is correct;
- the Windows manual UI checklist includes the eighth pane and synthetic duplicate candidates.

#### Remaining economy work

- Historical ordering rule: work-order generation after adapter contracts exist.
- Extend typed planning contracts as later domain tools become implemented.

### Actors and population

- Actor and Troop Editor.
- Templates, identities, unit classes, troop trees, pools, and upgrades.
- Spawn and Encounter Editor.
- Anchors, compositions, routes, lifecycle, uniqueness, density, and cleanup.

### World and societies

- World, Road, and Route Editor.
- Regions, scenes, locations, roads, segments, intersections, and routes.
- Faction and Authority Editor.
- Factions, cultures, territory, authority, and dispositions.

### Narrative and state

- Quest and State Inspector.
- State keys, decisions, consequences, overlays, and read/mutation permissions.

### Assets and localisation

- Asset and Localisation Manager.
- Addresses, bundles, source assets, cooked assets, localisation keys, and compatibility.

## Phase 7 — FoA adapter contracts

Status: active development.

### Adapter capability contract foundation

Status: implemented, continuing hardening and Windows UI verification.

- Typed lowercase namespaced adapter identity and strict semantic-version declarations.
- Exact `Mono` and `IL2CPP` runtime-target declarations.
- Typed capabilities for item grants, recipe learning/appending, custom item/recipe registration, vendors, loot, rewards, persistence, cleanup, and rollback.
- Existing pack `RequiredAdapterVersion` compatibility without a durable schema change.
- Conservative same-major semantic-version policy, with same-minor gating for major version zero.
- Exact adapter identity and capability evidence bound to active profile, game version, branch, runtime target, and source fingerprint.
- Catalog permission and same-subject validation-proof checks for governed capabilities.
- Deterministic `supported`, `unsupported`, `version_mismatch`, `permission_missing`, and `proof_missing` rows.
- Transient Core declaration registry cleared on Editor shutdown.
- Read-only **Tainted Grail Adapter Capability Matrix**.
- Focused Core tests, static validator, CI integration, public documentation, and Windows manual UI coverage.
- No runtime adapter implementation, BepInEx/Harmony execution, process access, deployment, game launch, save mutation, or work-order execution.

The Slice 8 ordering described deterministic work-order generation as plans only.

Exit criteria:

- malformed IDs, versions, runtime targets, and duplicate capabilities fail at the typed registry boundary;
- all eleven capability identifiers round-trip through the typed boundary;
- empty registries and undeclared capabilities fail closed as `unsupported`;
- version incompatibility is reported before permission or proof readiness;
- permission absence remains distinct from broken permission or adapter proof;
- valid same-subject permission, validation, source, and adapter proof can produce `supported`;
- matrix generation is deterministic and does not mutate declarations, packs, sources, evidence, catalog, or governance state;
- the matrix remains read-only and exposes no registration, execution, work-order, deployment, launch, or save action;
- the Windows manual UI checklist includes all nine panes and the no-declaration fail-closed state.

### Deterministic work-order plan generation

Status: implemented, continuing hardening and Windows UI verification.

- Pure Core planning over exact packs, transient adapter declarations, the Slice 8 compatibility matrix, reviewed catalog subjects, source/evidence, governance history, and blockers.
- Whole-plan refusal unless all eleven compatibility rows are `supported`.
- Independent rebuilding of each exact subject's identity, permission, validation, evidence, relationship, target, typed payload, and blocker readiness.
- Stable plan and step identities containing exact pack, adapter, profile, game-version, branch, runtime-target, capability, and subject bindings.
- Record steps for governed item/recipe capabilities and relationship steps for vendor, loot, and reward capabilities.
- Resolved current relationship targets and relationship validation proof.
- Complete typed item/recipe payload arguments with exact input evidence.
- Deterministic step order, one-based sequence numbers, sorted evidence/proof/argument collections, fixed JSON property order, escaping, and locale-independent numeric formatting.
- Canonical JSON with `ExecutionAllowed: false` on the plan and every step.
- Deterministic refusals containing failed capabilities, compatibility statuses, subjects, and reasons.
- Read-only **Tainted Grail Adapter Work-Order Plans** pane.
- Production-linked tests, focused static validator, validator negative tests, CI integration, public documentation, and ten-pane Windows UI coverage.
- No plan persistence, export, dispatch, adapter call, code generation, process access, deployment, launch, telemetry, save mutation, or execution.

Exit criteria:

- one non-supported capability refuses the complete pack/adapter candidate;
- aggregate compatibility cannot leak an independently unreviewed subject into a step;
- custom-registration and recipe-append steps require complete typed payloads and exact evidence;
- vendor, loot, and reward steps require resolved current targets and relationship validation proof;
- equivalent reviewed inputs produce byte-identical canonical JSON;
- plans and steps always retain `ExecutionAllowed: false`;
- planning does not mutate packs, declarations, sources, evidence, catalog, governance, or blockers;
- the Editor pane remains non-editable and exposes no save, export, dispatch, execution, deployment, launch, or adapter-registration control;
- the Windows manual UI checklist includes all ten panes and the default no-declaration refusal state.

### Runtime-result evidence envelope

Status: implemented, continuing hardening and Windows UI verification.

- Typed attempted-plan and attempted-step identities bound to exact canonical work-order plans.
- Exact step sequence, capability, subject kind, subject ID, and subject-reference matching.
- Typed `not_attempted`, `succeeded`, `failed`, and `skipped` outcomes with explicit attempted state.
- Typed contract, capability, runtime, persistence, cleanup, rollback, and unknown failures.
- Exact cleanup and rollback summaries that must match their corresponding canonical step results.
- Safe relative log references with typed log kinds and lowercase SHA-256 fingerprints.
- Exact plan, result, step-output, and log fingerprints.
- Fail-closed rejection for missing, duplicate, unknown, or changed plan/step/failure/log bindings.
- Candidate source and evidence documents returned by value for step results, failures, cleanup, rollback, plan binding, and referenced log fingerprints.
- Transient `AdapterRuntimeResultRegistry` cleared on Editor shutdown.
- Read-only **Tainted Grail Adapter Runtime Result Evidence** pane.
- Production-linked tests, focused static validation, negative validator tests, CI, documentation, and eleven-pane Windows UI coverage.
- No automatic source/evidence registration, persistence, catalog promotion, validation, permission, adapter call, process access, deployment, launch, telemetry, or save mutation.

Exit criteria:

- every accepted envelope binds to one exact generated plan and exactly one result for every plan step;
- attempted-plan and attempted-step identities cannot drift from canonical JSON;
- failed and skipped outcomes carry typed failures, while succeeded outcomes carry output fingerprints;
- cleanup and rollback summaries match the corresponding step result exactly;
- log references remain safe, relative, fingerprinted, and bound to known steps;
- accepted envelopes return new evidence candidates without importing, publishing, validating, or permitting them;
- malformed or mismatched envelopes return deterministic issues and no evidence candidates;
- result validation and evidence return do not mutate plans, envelopes, registries, sources, catalogs, governance, or blockers;
- the Editor pane is non-editable and exposes no input, import, save, execution, deployment, or launch control;
- the Windows manual UI checklist includes all eleven panes and the default zero-envelope state.

No actual FoA adapter implementation or execution path is introduced or authorised by this contract.

## Phase 8 — Build, package, deploy, and test

Status: active development.

### Reproducible adapter build manifests

Status: implemented, continuing hardening and Windows UI verification.

- Pure Core generation of a reproducible build definition for one exact canonical work-order plan.
- Exact pack, adapter, profile, game-version, branch, runtime-target, Unity, and BepInEx bindings.
- Stable builder identity/version, source commit, O3DE revision, configuration, target framework, compiler identity/version, deterministic-build, CI-normalisation, and path-map declarations.
- BepInEx plugin GUID, name, version, safe `BepInEx/plugins/` package root, and typed hard/soft dependency metadata.
- Required resolved materials for work-order plan, source tree, dependency lock, toolchain lock, and licence, each with safe relative locators and lowercase SHA-256 fingerprints.
- Expected plugin binary, readme, changelog, manifest, and licence outputs constrained beneath the package root.
- Explicit redistribution decisions that keep non-redistributable materials out of package contents.
- Deterministic `plan_mismatch`, `toolchain_unresolved`, `input_missing`, `fingerprint_missing`, `path_invalid`, `redistribution_blocked`, and `ready` statuses.
- Canonical JSON with fixed ordering and `BuildAllowed: false`.
- Read-only **Tainted Grail Adapter Build Manifests** pane.
- Production-linked tests, focused validator and negative tests, CI integration, public documentation, and twelve-pane Windows UI coverage.
- No compilation, packaging, deployment, launch, or execution is introduced or authorised.

Exit criteria:

- a manifest cannot reinterpret a canonical plan for another pack, adapter, profile, branch, or runtime target;
- exact toolchain and source revisions are required before a definition is `ready`;
- required material roles and fingerprints remain distinct fail-closed gates;
- all expected outputs remain safe relative paths beneath the declared BepInEx package root;
- non-redistributable materials never enter declared package contents;
- equivalent inputs produce byte-identical canonical JSON;
- `BuildAllowed` remains false for every status, including `ready`;
- manifest generation does not mutate plans, packs, profiles, declarations, materials, dependencies, or output declarations;
- the Editor pane remains non-editable and exposes no save, export, build, package, deployment, launch, or execution action;
- the Windows manual UI checklist includes all twelve panes and the default zero-ready-definition state.

### Next ordered slice — deterministic package assembly preview

Compare a reviewed build manifest with a project-owned staging inventory and derive a deterministic package layout, output digests, omissions, collisions, and redistribution blockers. The preview must not copy files, create archives, deploy content, launch FoA, or execute an adapter.

Controlled pipeline:

```text
validate → generate → build → package → deploy → launch → capture → attach evidence
```

- Reproducible build manifests.
- Mod-owned output only.
- Staging and deployment previews.
- Explicit user confirmation.
- Restoration and rollback plans.
- Compatibility reports.
- Log and diagnostic capture.
- Release archives and checksums.

## Phase 9 — Ecosystem and automation

- Importer plugin SDK.
- Domain tool extensions.
- Headless validation and packaging.
- Public schema packages.
- CI fixtures and compatibility matrices.
- Migration tooling.
- Documentation and examples for third-party adapters.

## Cross-cutting requirements

Every phase must preserve:

- exact identity;
- pack ownership;
- evidence provenance;
- independent governance axes;
- fail-closed validation and permission;
- editor/runtime separation;
- durable schema versioning;
- legal redistribution boundaries;
- accessibility and usable error reporting;
- public documentation and executable tests.

## Not roadmap commitments

This document does not promise release dates, support every game patch, guarantee compatibility with private mods, or authorise runtime actions that have not passed the required validation and permission gates.
