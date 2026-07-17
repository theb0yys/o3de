# Recipe Station Visibility and Learnability Evidence View Design

Status: proposed for design review

Target: Phase 6 — Domain authoring tools, remaining economy work

## Decision requested

Approve a schema-neutral, read-only evidence view for canonical recipe–station associations and recipe learnability research.

The first implementation will derive a deterministic review model from the existing catalog, economy profiles, relationships, evidence registry, governance state, and blockers. It will not add runtime behavior, grant permission, or persist a second representation of recipe visibility or learnability.

## User problem

The Item and Recipe Editor currently stores and displays:

- canonical recipe profiles;
- canonical station record IDs;
- recipe unlock mode and unlock subject references;
- profile evidence IDs;
- first-class `crafted_at` and `learned_from` relationships;
- read-only action-lane status.

Those facts are reviewed in separate surfaces. A reviewer cannot currently inspect one recipe and answer, per station and learnability source:

- which exact canonical records are involved;
- which evidence supports each association;
- whether evidence is present and subject-compatible;
- whether the relevant records and relationships are current and validated;
- which blockers prevent the research from supporting later adapter planning;
- whether a displayed result is only research evidence rather than runtime proof.

## Product boundary

This change remains inside editor-side knowledge and review tooling.

It must not:

- call FoA, BepInEx, Harmony, or Avalon Core runtime APIs;
- append recipes to station lists;
- learn or forget recipes;
- register custom recipes;
- grant validation or permission;
- generate adapter work orders;
- mutate vendors, loot, rewards, quests, saves, deployment state, or game state;
- infer runtime visibility or learnability from display names or incomplete research.

## Owning architecture layer

The feature belongs to the economy domain read-model layer.

Proposed responsibilities:

- a focused service builds recipe–station evidence rows from immutable inputs;
- the service consumes `CatalogDatabase`, `SourceEvidenceRegistry`, and evaluated blockers;
- `ItemRecipeEditorWidget` renders and filters returned rows but does not evaluate domain truth;
- existing catalog, evidence, governance, and blocker services remain authoritative;
- `FoundationNotificationBus` continues to trigger refresh when shared state changes.

A focused service is preferred over adding evidence interpretation directly to the widget. Final names may follow established source conventions, but the intended shape is equivalent to:

```cpp
struct EconomyRecipeStationEvidenceRow;

class EconomyEvidenceViewService
{
public:
    AZStd::vector<EconomyRecipeStationEvidenceRow> BuildRecipeStationEvidence(
        const AZStd::string& recipeRecordId,
        const SourceEvidenceRegistry& sourceRegistry,
        const CatalogDatabase& catalog,
        const AZStd::vector<BlockerRecord>& blockers) const;
};
```

The service must be deterministic, side-effect free, and safe to call during UI refresh.

## Read-model contents

A row represents one exact recipe–station association or one unresolved station reference. It should expose enough structured data for the widget and unit tests without returning formatted UI strings as domain truth.

Expected fields include:

- recipe record ID;
- recipe exact native reference or pack owner summary where available;
- station record ID or unresolved station subject reference;
- station exact native reference or pack owner summary where available;
- association sources, such as profile station reference and matching `crafted_at` relationship IDs;
- unlock mode;
- exact unlock subject references;
- matching `learned_from` relationship IDs;
- relevant profile and relationship evidence IDs;
- evidence-health status and reasons;
- relevant validation and staleness state;
- conflict, missing-reference, and supersession state;
- current read-only action-lane statuses;
- blocker IDs and actionable blocker reasons.

The read model must preserve exact IDs. Display names may be shown as labels only and must never be used to join records.

## Evidence semantics

The view reports research support; it does not claim runtime behavior.

### Station association

A station association may be sourced from:

- `EconomyRecipeProfile::m_stationRecordIds`;
- a canonical `crafted_at` relationship from the recipe to the station;
- both sources.

The row should show which source exists rather than silently collapsing them into one inferred fact.

A profile station reference without supporting evidence remains visible as incomplete research. A `crafted_at` relationship with missing, unknown, or incompatible evidence remains visible but blocked.

### Learnability research

Learnability information may be sourced from:

- recipe unlock mode;
- exact unlock subject references;
- canonical `learned_from` relationships;
- evidence attached to the recipe profile and relevant relationships.

The service must not infer that a recipe is learnable merely because an unlock mode or source reference is populated. It should report the available components and their evidence health.

### Evidence compatibility

Use the existing source/evidence registry and catalog identity rules. At minimum, fail closed when:

- an evidence ID is unknown;
- evidence is outside the active source/profile/build binding;
- evidence is unrelated to the recipe, station, relationship, or explicit unresolved subject under the existing evidence rules;
- a referenced relationship is missing or malformed;
- a canonical record is unresolved, conflicted, missing references, or superseded.

Do not invent broader compatibility rules inside the widget.

## Research status vocabulary

The UI may use neutral research statuses such as:

- `supported evidence` — the represented association has resolvable canonical identities and no relevant evidence or governance blocker;
- `partial evidence` — some expected association or learnability evidence exists, but coverage is incomplete;
- `missing evidence` — the association is represented without usable supporting evidence;
- `unresolved` — a station or learnability subject is not reconciled to a canonical identity;
- `blocked` — existing blockers, governance state, or invalid evidence prevent the research from supporting downstream planning.

These statuses are not validation states, permission decisions, adapter capability declarations, or runtime test results.

## Fail-closed rules

The view must never present a recipe as supported, visible, learnable, or ready when any applicable input is:

- missing;
- unresolved;
- bound to the wrong subject or active game profile;
- unvalidated, failed, stale, potentially stale, or blocked where current validated proof is required;
- conflicted;
- missing references;
- superseded;
- explicitly forbidden for the relevant usage;
- lacking the station or learnability evidence needed for the displayed conclusion.

An `allowed` editor-side action lane may be displayed, but it must not override contradictory evidence or blockers and must not be described as runtime capability.

## Persistence and schema

This first slice adds no persisted fields and does not change catalog schema 1.

The read model is rebuilt from existing authoritative state. Opening, filtering, selecting, or refreshing the view must not:

- mutate the catalog;
- append history;
- change validation or permission;
- save the catalog;
- publish a candidate catalog;
- create identities or relationships.

If implementation shows that station-specific evidence cannot be represented faithfully from the current recipe profile, evidence, and relationship data, implementation must stop and return to design review before adding a field or schema.

## User interface

Add a read-only station and learnability evidence surface to the existing Item and Recipe Editor.

The surface should:

- follow the currently selected canonical recipe;
- show one deterministic row per exact station association, including unresolved references;
- expose association source, evidence health, governance state, blockers, and read-only lanes;
- expose unlock and `learned_from` research without implying runtime behavior;
- provide accessible column labels and actionable detail text;
- avoid editable controls for evidence status, validation, permission, or blocker suppression.

A new top-level dock is not required for this slice.

## Validation plan

Add unit coverage for at least:

- one recipe with one evidenced canonical station;
- one recipe with multiple stations and independent evidence health;
- a profile station reference with a matching `crafted_at` relationship;
- duplicate profile/relationship association suppression without losing source detail;
- matching and absent `learned_from` relationships;
- unresolved station and unlock subjects;
- unknown evidence IDs;
- evidence bound to the wrong subject;
- evidence bound to the wrong game profile or build;
- stale, blocked, conflicted, missing-reference, and superseded records or relationships;
- deterministic row ordering;
- native and synthetic recipe identities remaining distinct;
- read-only action-lane presentation;
- proof that building and refreshing the view does not mutate or persist the catalog.

Update the focused foundation validator and catalog/economy test contract so required source files, tests, and documentation cannot be omitted accidentally.

## Documentation impact

Implementation should update:

- the Item and Recipe Editor guide;
- the Gem and root capability summaries where appropriate;
- the roadmap remaining-economy status;
- the changelog;
- the development or architecture guide only if the final service boundary differs from this proposal.

`DATA_FORMATS.md` does not require a format change for the schema-neutral implementation.

## Security, privacy, legal, and compatibility impact

- No new filesystem scanning, process execution, networking, telemetry, or deployment.
- No private game data or copyrighted fixtures may be committed.
- Existing exact profile/build and evidence provenance rules remain authoritative.
- Existing catalog documents remain readable without migration.
- The feature is editor-only and host-tool-only.

## Acceptance criteria

- The existing Item and Recipe Editor exposes a usable read-only recipe station and learnability evidence view.
- Every association is built from exact canonical IDs or an explicit unresolved subject reference.
- Association source and evidence source remain visible rather than being silently inferred.
- Missing, mismatched, unresolved, stale, blocked, conflicted, missing-reference, and superseded inputs fail closed with actionable reasons.
- The view cannot grant permission, change validation, suppress blockers, mutate state, or trigger persistence.
- Focused validators and unit tests cover negative, deterministic, duplicate, and non-mutation cases.
- Public documentation distinguishes research evidence from runtime capability.
- Applicable repository validation, source-policy validation, unit tests, and host builds pass before merge.

## Review decision

Approval of this proposal authorises implementation of the schema-neutral read-only slice on `foa-development`. It does not authorise schema changes, adapter contracts, runtime execution, work-order generation, or permission-model changes.