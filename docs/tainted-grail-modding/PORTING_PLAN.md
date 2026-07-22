# Tainted Grail Modding Handbook Porting Plan

## Goal

Port the useful information and proven process structure from the pinned Tainted Grail mod repository into FOA-SDK as a coherent public handbook, while preserving exact provenance, current SDK ownership, version boundaries, legal restrictions, and fail-closed research status.

This is a selective migration and synthesis programme, not a directory copy.

## Migration principles

1. Inventory before moving content.
2. Classify every source by purpose, licence state, version scope, evidence state, and destination owner.
3. Adapt guidance to current FOA-SDK architecture instead of preserving obsolete repository assumptions.
4. Extract claims and patterns from implementations; do not import entire experimental mods as documentation.
5. Preserve negative results, blockers, conflicts, and unknowns.
6. Keep canonical data and schemas in their current owners.
7. Require exact game/runtime profiles for hooks and compatibility claims.
8. Validate every tutorial against the current SDK before marking it reviewed.

## Source handling decisions

| Decision | Use when | Result |
|---|---|---|
| `adapt` | Process or guidance is useful but source paths/tooling changed | Rewrite for FOA-SDK and retain source provenance |
| `extract` | Source code or mod evidence contains reusable facts/patterns | Create concise records, examples, or research claims |
| `link` | FOA-SDK already has a canonical document or contract | Add navigation and explanation only |
| `retain-in-research` | Material is uncertain, dated, raw, private, or not ready for users | Register it under `Research/`; do not publish as guidance |
| `block` | Payload is proprietary, unlicensed, unsafe, or contains private/generated data | Record the blocker and do not copy it |
| `supersede` | Current SDK behavior replaces the source workflow | Document migration and point to the current owner |

## Phase 0 — Establish the handbook contract

Deliverables:

- canonical handbook root and navigation;
- information architecture and required metadata;
- source map and migration status vocabulary;
- research backlog and hook-record contract;
- links from the SDK documentation indexes.

Exit criteria:

- no new top-level product root;
- no duplicate schema or authority owner;
- exact upstream source pin recorded;
- legal and proprietary-content boundaries explicit.

## Phase 1 — Complete the source inventory

Inventory these source groups at the pinned commit:

- top-level documentation and ordered read path;
- research taxonomy, game-knowledge domains, templates, registers, and scopes;
- mod template and build conventions;
- engineering, review, UI, validation, promotion, debugging, lifecycle, release, and ecosystem processes;
- reusable framework, UI, diagnostics, road, AI, provider, and adapter knowledge;
- each mod's README, design, research, compatibility, validation, decision, review, release, and support material;
- patch targets, reflection targets, lifecycle hooks, registries, services, config patterns, and compatibility guards in source;
- generated evidence, failed incidents, private paths, binaries, assets, and other blocked material.

Every inventory row must name the exact source path, source blob or commit, intended destination, decision, status, and blocker.

## Phase 2 — Port the universal mod-development process

Adapt and consolidate:

1. environment and runtime selection;
2. research and target discovery;
3. mod design and risk review;
4. project scaffolding and identity;
5. implementation patterns;
6. configuration and logging;
7. compatibility and collision review;
8. build and controlled local deployment;
9. in-game validation and evidence;
10. packaging, release, support, and migration.

The resulting process must use current SDK validation, catalog, provider, installer, ExtensionAPI, and adapter boundaries rather than obsolete direct assumptions.

## Phase 3 — Build the system reference

Create one canonical index for each domain:

- runtime and loader lifecycle;
- game bootstrap and scene lifecycle;
- input and player state;
- actors, troops, factions, cultures, and dispositions;
- combat, damage, status, equipment, and progression;
- items, recipes, crafting, vendors, loot, and rewards;
- quests, dialogue, events, objectives, and world state;
- spawning, encounters, patrols, navigation, and cleanup;
- worldspaces, scenes, locations, roads, map, travel, and anchors;
- UI, HUD, menus, prompts, icons, accessibility, and localization;
- audio, VFX, animation, materials, and asset loading;
- AI, blackboards, goals, actions, and planning;
- saves, persistence, configuration, migration, and rollback;
- mod identity, dependencies, interoperability, and diagnostics.

Each page links to canonical records and reviewed hooks instead of embedding an uncontrolled private catalog.

## Phase 4 — Extract and verify the hook catalogue

For each source patch or extension point:

1. identify the exact source implementation and purpose;
2. resolve the game/runtime profile it was used against;
3. record assembly, type, member, signature, lifecycle, and patch style;
4. classify direct, reflective, event-driven, service, data, UI, or adapter access;
5. record side effects, thread/context, ordering, conflict, and cleanup risks;
6. bind concise permitted evidence;
7. verify the target against the exact intended profile;
8. perform load and behavior validation where authorised;
9. mark unsupported, stale, replaced, or blocked targets honestly.

A source code occurrence is only a candidate. It does not become a supported hook merely because a mod once compiled.

## Phase 5 — Produce reviewed examples

Examples must be project-owned, minimal, buildable, and scoped to one lesson. Planned examples include:

- basic plugin identity, logging, and configuration;
- narrow Harmony postfix and prefix patterns;
- lifecycle-safe registration and unpatching;
- read-only game observation;
- safe UI/HUD addition;
- catalog and ExtensionAPI queries;
- evidence submission without promotion;
- Mono and IL2CPP adapter handoff examples;
- compatibility guard and failure reporting;
- package layout and deterministic release metadata.

Do not convert a large real mod into the starter template. Mine it for small reviewed patterns.

## Phase 6 — Validate and publish the handbook

Required checks:

- every page is reachable from an index;
- every technical claim has a profile and source;
- every hook ID resolves to one record;
- every source-map row has a disposition;
- every open question exists in the research backlog;
- links and code samples are checked;
- tutorials are exercised against the exact SDK head and declared runtime profile;
- legal, security, privacy, and proprietary-content scans pass;
- deprecated material remains traceable;
- documentation does not claim runtime support beyond actual evidence.

## Per-item workflow

```text
source discovered
→ inventory row
→ licence and payload classification
→ claim/pattern extraction
→ target owner selected
→ draft adaptation or research brief
→ exact-profile review
→ validation evidence
→ handbook review
→ index and backlink update
→ reviewed status
```

Failure at any step keeps the item draft, blocked, or research-only. It is not silently omitted or represented as complete.

## Completion definition

The handbook is complete only when a new mod author can move from environment setup through a validated release, and an advanced author can find the known system model, exact reviewed hooks, compatibility constraints, SDK authoring surface, and unresolved research for any supported domain without consulting an undocumented private source.