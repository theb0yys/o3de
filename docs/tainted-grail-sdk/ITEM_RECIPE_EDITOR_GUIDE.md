# Item and Recipe Editor Guide

## Purpose

The Item and Recipe Editor is the first specialised domain authoring tool built on the shared TG SDK foundation.

Open it from:

**Tools → Tainted Grail SDK → Tainted Grail Item and Recipe Editor**

The tool authors typed economy data for canonical catalog records. It does not create game identities, call FoA APIs, register runtime templates, grant inventory items, learn recipes, append recipes, mutate vendors or loot, deploy files, or modify saves.

## Core separation

**An item record is not a recipe record.**

The editor keeps these concepts independent:

- an **item record** identifies a game-owned or pack-owned item;
- a **recipe record** identifies a game-owned, runtime-appended, or pack-owned recipe definition;
- an **ingredient join** describes one required input for a recipe;
- an **output join** describes one output or by-product from a recipe;
- a **station record** identifies a crafting or interaction context;
- an **acquisition relationship** describes where an item or recipe may be sold, dropped, found, rewarded, learned, granted, or crafted;
- a **permission decision** authorises one named downstream usage lane after validation.

A display name never joins these records. Every profile and join uses stable canonical record IDs or an explicit unresolved subject reference.

## Prerequisites

Before authoring economy data:

1. configure and save a workspace;
2. configure the exact active FoA game profile;
3. create or load the owning pack for synthetic records;
4. import source artifacts;
5. promote evidence into canonical catalog records;
6. create canonical records with domain `economy` and the applicable record kind;
7. review the record in the Catalog Browser and Catalog Governance tools.

The Item and Recipe Editor only lists existing canonical records. Missing identities must be researched and promoted through the catalog workflow rather than invented inside the domain tool.

## Supported canonical record kinds

### Items

Typed item profiles require:

```text
Domain: economy
RecordKind: item
```

### Recipes

Typed recipe profiles require:

```text
Domain: economy
RecordKind: recipe
```

### Stations

Recipe station IDs may reference canonical economy records using one of these kinds:

```text
station
crafting_station
interaction_target
```

Other economy records—such as vendors, loot sources, locations, quests, contracts, or rewards—may be targets of acquisition relationships when their canonical identities already exist.

## Existing-content and custom-content lanes

Native and synthetic identities remain separate.

### Existing native item

A native item record:

- preserves its exact native reference;
- has no custom pack owner;
- may eventually receive reviewed permissions such as `existing_item_grant` or `existing_item_consume`;
- cannot use `custom_item_registration`.

### Custom item

A synthetic item record:

- is owned by an existing pack ID;
- does not borrow a native exact reference;
- may eventually receive `custom_item_registration` after adapter proof exists;
- cannot use native-only grant or consume lanes before registration and identity resolution.

### Existing native recipe

A native recipe record:

- preserves its exact native reference;
- may use `native_template` persistence description;
- may eventually receive `existing_recipe_learn` after station visibility and learnability proof;
- cannot use `custom_recipe_registration`.

### Runtime-appended recipe

A reviewed recipe may use the descriptive persistence mode `runtime_append` when research shows that an adapter can safely append a recipe definition. This label does not grant permission. The separate `runtime_recipe_append` lane must still pass governance and adapter validation.

### Custom recipe

A synthetic recipe:

- is pack-owned;
- may use `custom_template` persistence description;
- may eventually receive `custom_recipe_registration`;
- cannot claim the existing native recipe-learn lane.

## Item profile

Select a canonical item record, then enter only values supported by evidence.

Fields include:

- category and subtype;
- stack limit, where `0` means unknown rather than unlimited;
- weight and base value;
- rarity and quality;
- durability, where `0` may represent unknown when the underlying item does not expose a durability value;
- quest/story-sensitive flag;
- unique flag;
- hidden flag;
- localisation name and description references;
- icon and asset references;
- tags;
- evidence IDs.

Negative weight, value, or durability is rejected.

### Quest and unique items

Marking an item as quest-sensitive or unique does not automatically forbid every use, but the blocker service treats broad distribution lanes as high-risk.

Quest-sensitive items are blocked from ordinary grant, consume, vendor/loot, and reward lanes until a dedicated quest-safety review exists.

Unique items are blocked from vendor/loot and reward distribution until uniqueness, persistence, cleanup, and rollback behavior are proven.

## Recipe profile

Select a canonical recipe record and provide:

- recipe type;
- recipe tab or UI grouping;
- one or more canonical station record IDs;
- unlock mode;
- unlock subject references;
- stable duplicate key;
- persistence mode;
- hidden flag;
- evidence IDs.

Supported persistence descriptions are:

- `unknown`;
- `native_template`;
- `runtime_append`;
- `custom_template`.

These values describe the researched implementation shape. They are not runtime permissions.

Native recipes cannot use `custom_template`. Synthetic recipes cannot claim `native_template`.

A recipe without a station or typed output is persisted only as incomplete research and remains blocked from recipe action lanes.

## Ingredient joins

Ingredients are typed join records rather than strings embedded in a recipe.

Each ingredient requires:

- stable link ID;
- recipe record ID;
- exactly one resolved item record ID or unresolved item subject reference;
- positive quantity;
- optional alternative group;
- consumed flag;
- optional conditions;
- evidence IDs.

Use an unresolved subject reference when the source proves an ingredient subject but canonical identity reconciliation is incomplete. Unresolved ingredients remain blocked for runtime recipe append and custom registration.

Alternative groups may represent substitutions or “one of” ingredient requirements. The group semantics must be documented in conditions and evidence; the editor does not infer them.

## Output and by-product joins

Each output requires:

- stable link ID;
- recipe record ID;
- exactly one resolved item record ID or unresolved item subject reference;
- positive quantity;
- probability greater than `0` and no greater than `1`;
- by-product flag;
- optional conditions;
- evidence IDs.

A recipe requires at least one typed output before recipe action lanes can be considered.

Unresolved outputs are more restrictive than unresolved ingredients because the resulting identity cannot be safely granted, registered, displayed, or persisted.

## Acquisition relationships

The shared relationship form creates first-class catalog relationships. Supported relationship kinds are:

- `sold_by`;
- `dropped_by`;
- `found_at`;
- `rewarded_by`;
- `learned_from`;
- `granted_by`;
- `crafted_at`.

Each relationship requires:

- stable relationship ID;
- source item or recipe record;
- exactly one target record ID or unresolved target subject reference;
- relationship kind;
- evidence IDs;
- optional attributes.

New relationships begin with:

```text
ResearchStage: S2
Confidence: inferred
OperationalRisk: unknown
ValidationState: unvalidated
StalenessState: unknown
ForbiddenUsages: no_unvalidated_runtime_use
```

The relationship must be reviewed in Catalog Governance before it can support planning or adapter work.

## Action-lane matrix

The Item and Recipe Editor displays action lanes as read-only status. It never changes them.

Possible status values are:

- `allowed` — a reviewed governance decision currently permits the lane;
- `forbidden` — the lane is explicitly prohibited;
- `unset` — no permission decision exists.

### Item lanes

- `existing_item_grant`;
- `existing_item_consume`;
- `custom_item_registration`;
- `asset_localisation_injection`;
- `vendor_or_loot_injection`;
- `quest_or_contract_reward_injection`.

### Recipe lanes

- `existing_recipe_learn`;
- `runtime_recipe_append`;
- `custom_recipe_registration`;
- `asset_localisation_injection`;
- `quest_or_contract_reward_injection`.

Use Catalog Governance to review validation and permissions. A green or `allowed` lane remains an editor-side decision only; a runtime adapter must independently confirm capability, compatibility, persistence, cleanup, and rollback before execution.

## Evidence rules

Item and recipe profile evidence must exist in the active evidence registry and match the canonical record’s subject reference.

Ingredient and output evidence may belong to:

- the recipe subject;
- the resolved item subject;
- the explicit unresolved item subject.

Missing or unrelated evidence is rejected before persistence.

Acquisition relationships require evidence IDs and receive blockers when referenced evidence is missing or belongs outside the active source set.

## Durable storage

Typed economy data is stored in the same canonical document as identities, relationships, validation, and governance history:

```text
Catalog/catalog.tgcatalog.json
```

The document uses optional schema-1 fields for backward compatibility:

- `EconomyItems`;
- `EconomyRecipes`;
- `RecipeIngredients`;
- `RecipeOutputs`.

The complete candidate catalog is saved before the in-memory catalog is published. A failed validation or write leaves the current catalog unchanged.

## Blockers

Economy blockers include:

- canonical item or recipe without a typed profile;
- profile evidence missing or bound to another subject;
- recipe without a station;
- recipe without an output;
- unresolved ingredient or output identity;
- missing join evidence;
- identity-incompatible action lane;
- quest-sensitive item approved for ordinary distribution;
- unique item approved for vendor, loot, or reward distribution;
- native recipe configured as custom template;
- synthetic recipe configured as native template.

Resolve the underlying identity, evidence, profile, join, governance, or adapter proof. Do not remove a blocker merely to make coverage appear complete.

## What this tool does not do

The Item and Recipe Editor does not:

- scan the game installation;
- fabricate missing item or recipe identities;
- parse opaque runtime data;
- grant or remove inventory items;
- learn or forget recipes;
- append recipes to station lists;
- register custom item or recipe templates;
- load Unity assets;
- inject localisation;
- mutate vendors, loot, rewards, quests, contracts, or saves;
- launch FoA;
- execute rollback.

Those actions belong to separately implemented and validated adapter, build, deployment, and test layers.

## Recommended review sequence

1. Verify the canonical identity and exact native reference or pack owner.
2. Verify profile evidence against the exact active game build.
3. Complete item or recipe profile fields without guessing.
4. Resolve stations, ingredients, outputs, and acquisition relationships.
5. Review economy blockers in Foundation Status.
6. Record maturity, confidence, risk, validation, and staleness in Catalog Governance.
7. Grant only the narrow usage lane supported by proof.
8. Keep runtime adapter execution outside the editor.
