# FoA Adapter Work-Order Plans

## Status

Implemented as Correction Slice 9, the second Phase 7 capability slice. The slice produces deterministic, canonical plans only from reviewed catalog state and the typed adapter contracts introduced in Slice 8.

Execution remains prohibited.

## Purpose

A work-order plan is a read-only description of what an adapter would have to receive later. It is not an adapter invocation, code generator, deployment package, loader instruction, runtime approval, or proof that FoA behavior works.

A candidate is evaluated for one exact combination of:

- pack ID and pack version;
- adapter ID, declared adapter version, and pack-required adapter version;
- active profile ID, game version, branch, and runtime target.

## Whole-plan gate

A canonical plan requires exactly one compatibility row for each of the eleven typed capabilities from Slice 8:

- `item_grant`;
- `recipe_learn`;
- `recipe_append`;
- `custom_item_registration`;
- `custom_recipe_registration`;
- `vendor_mutation`;
- `loot_mutation`;
- `reward_mutation`;
- `persistence`;
- `cleanup`;
- `rollback`.

All eleven compatibility rows must be `supported`. Any `unsupported`, `version_mismatch`, `permission_missing`, or `proof_missing` row refuses the entire candidate. The planner never cherry-picks a partial subset from an incompatible adapter declaration.

## Exact reviewed subjects

Compatibility is an aggregate readiness finding, so the planner independently rebuilds the eligible subject set before generating steps. Every record step requires:

- the exact pack owner;
- the identity lane required by the capability;
- current, validated, reference-complete, conflict-free, non-superseded catalog state;
- the exact allowed usage mapped by the adapter contract;
- a same-subject permission event;
- valid same-subject validation proof;
- exact active-profile source and input evidence;
- no applicable open blocker.

This second pass prevents a supported aggregate row from leaking an unreviewed catalog subject into a plan.

## Typed payloads

Record steps carry sorted key/value arguments derived from canonical catalog and typed economy state.

Custom item registration requires a typed item profile with exact input evidence. Recipe append and custom recipe registration require a typed recipe profile, typed output joins, and exact evidence for the record, profile, ingredients, and outputs. Missing or unrelated payload evidence refuses the whole candidate.

The plan records input evidence, adapter declaration evidence, permission event IDs, permission evidence, and validation proof IDs separately.

## Resolved relationship targets

Vendor, loot, and reward steps are relationship steps. They require:

- a current validated relationship of the exact supported kind;
- a resolved target record ID rather than an unresolved subject-only target;
- a current validated target record;
- exact evidence for the source, relationship, and target;
- relationship validation proof bound to the exact active profile;
- no applicable open blocker on the source or resolved target.

The step records the source record, relationship ID, target record, and target subject explicitly.

## Stable plan identity

The stable plan identity contains the exact pack, pack version, adapter, adapter version, profile, game version, branch, and runtime target. Step identity contains the plan identity, capability, subject kind, and exact subject ID.

No wall-clock timestamp, random UUID, filesystem path, host name, or process result contributes to plan identity.

## Canonical JSON

Generated plans include canonical JSON with:

- fixed property order;
- deterministic capability and subject ordering;
- stable one-based step sequence numbers;
- sorted and deduplicated evidence/proof arrays;
- sorted and deduplicated typed arguments;
- JSON string escaping;
- locale-independent numeric formatting;
- 17-digit floating-point formatting;
- `ExecutionAllowed: false` on the plan and every step.

Equivalent reviewed inputs produce byte-identical canonical JSON.

## Refusals

A refusal contains the stable candidate plan ID, exact pack/adapter/profile identity, failed capabilities, compatibility statuses, affected subjects, and deterministic reasons. A refusal creates no partial plan and no executable step.

## Transient presentation

Plans and refusals are transient derived state. The Editor pane recomputes them from the current workspace, packs, transient adapter registry, source/evidence registry, catalog, and blockers.

The **Tainted Grail Adapter Work-Order Plans** pane is non-editable. It displays generated steps, canonical JSON, or refusal reasons. It has no save, export, dispatch, execute, deploy, launch, or adapter-registration control.

No work-order document schema is added in this slice.

## No runtime execution

This slice adds no FoA process access, BepInEx or Harmony execution, loader registration, generated adapter code, filesystem output, deployment, game launch, telemetry, save mutation, or actual adapter implementation.

`ExecutionAllowed` is always false. A generated plan is planning evidence only and does not grant permission.

## Tests and enforcement

Production-linked tests cover:

- whole-plan refusal when any compatibility row is not supported;
- generation from a fully supported reviewed catalog;
- prevention of aggregate-subject leakage;
- resolved relationship targets and relationship proof;
- refusal when relationship proof is missing;
- refusal when typed payload evidence is invalid;
- deterministic canonical serialization;
- complete input non-mutation.

The focused validator rejects runtime/process code, persistence or export paths, mutable UI controls, weakened all-capability gating, missing canonical sorting, incomplete tests, and missing documentation.

## Slice 10 runtime-result evidence

Slice 10 implements the typed runtime-result evidence contract described by the earlier next ordered slice. It binds externally supplied attempted-plan and attempted-step identities back to this exact canonical plan, validates typed outcomes, failures, cleanup, rollback, safe log references, and fingerprints, and returns candidate source/evidence documents.

The runtime-result evidence contract has no execution path. It does not save or dispatch a plan, call an adapter, read a log, import evidence automatically, or promote validation or permission.

See [FoA Adapter Runtime Result Evidence Contract](FOA_ADAPTER_RUNTIME_RESULT_EVIDENCE.md).

## Rollback

Revert the implementing pull request. No durable workspace, pack, catalog, source/evidence, or adapter schema requires migration because Slice 9 adds transient derived plans only.
