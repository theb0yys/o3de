# Recipe Station Visibility and Learnability Evidence View

## Purpose

The Item and Recipe Editor includes a read-only evidence view for reviewing where a canonical recipe is associated with a crafting or interaction station and what research exists for recipe learnability.

The view consolidates facts that already exist in the shared catalog. It does not add a second persistence format and does not execute or authorise runtime behavior.

Open:

**Tools → Tainted Grail SDK → Tainted Grail Item and Recipe Editor → Recipes**

Select a canonical recipe and review **Station Visibility and Learnability Evidence — Read-only Research**.

## Authoritative inputs

Rows are derived from:

- the selected canonical `economy/recipe` record;
- its typed recipe profile and canonical station record IDs;
- matching `crafted_at` relationships;
- unlock mode and exact unlock subject references;
- matching `learned_from` relationships;
- source/evidence registry records;
- record and relationship validation, staleness, missing-reference, conflict, and supersession state;
- current economy and governance blockers;
- read-only action-lane decisions.

Exact record IDs and subject references are preserved. Display names are labels only and are never used to join identities.

## One row per station association

A row represents one exact station association or one explicit unresolved station subject.

The **Association sources** column distinguishes:

- `recipe profile` — the station ID is declared by the typed recipe profile;
- `crafted_at:<relationship-id>` — a first-class catalog relationship associates the recipe with the station;
- both sources — profile and relationship research agree on the same canonical station.

Duplicate profile and relationship references are collapsed into one row without losing their source details.

## Learnability research

Each row also displays the recipe's:

- unlock mode;
- exact unlock subject references;
- matching `learned_from` relationship IDs;
- evidence attached to the recipe and relevant relationships.

These fields report research coverage only. An unlock mode or `learned_from` relationship does not prove that FoA can safely learn, forget, register, append, persist, clean up, or roll back a recipe.

## Research statuses

The view uses neutral research statuses:

- **supported evidence** — the exact station is represented by both profile and relationship sources, usable evidence exists, and applicable governance checks are current;
- **partial evidence** — usable evidence exists but only one association source is represented;
- **missing evidence** — no usable evidence supports the represented association;
- **unresolved** — the station identity has not been reconciled to a canonical record;
- **blocked** — evidence, governance, identity, relationship, or blocker state prevents the research from supporting downstream planning.

These statuses are not validation decisions, permission decisions, adapter capabilities, runtime test results, or deployment readiness.

## Fail-closed behavior

A row is not presented as supported when an applicable input is:

- unknown or missing;
- associated with an unrelated subject;
- inconsistent with its source fingerprint, profile, game version, or branch;
- unresolved;
- unvalidated, failed, stale, potentially stale, or blocked;
- conflicted or missing references;
- superseded;
- covered by an open blocker.

The **Blockers and reasons** column gives the relevant blocker IDs and actionable explanations.

## Read-only boundary

The evidence view cannot:

- create or change identities;
- add or edit station, `crafted_at`, or `learned_from` relationships;
- change evidence;
- validate records or relationships;
- grant or remove permission;
- suppress blockers;
- save or publish a catalog candidate;
- append or learn recipes;
- call FoA, BepInEx, Harmony, or Avalon Core runtime APIs;
- deploy files or mutate saves or game state.

Use the existing source intake, catalog, economy authoring, and Catalog Governance workflows to correct the authoritative inputs. Runtime behavior remains the responsibility of separately designed and validated adapter contracts.

## Review sequence

1. Select the exact canonical recipe.
2. Confirm the recipe profile station IDs and evidence.
3. Review matching `crafted_at` relationships.
4. Review unlock subjects and `learned_from` relationships.
5. Inspect evidence IDs, research status, governance state, and blocker reasons per row.
6. Resolve missing identity, evidence, validation, staleness, conflict, or supersession issues in their owning tools.
7. Treat any allowed action lane as an editor-side governance decision only, never as proof of runtime capability.
