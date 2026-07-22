# O3DE to Unity Conversion and Runtime Bridge Research

Status: research intake and reconciliation

Original intake baseline: `92aa29960bab92d646c464ae48b8cf09d881a436`

Current reconciliation baseline: `8fb3f0a729e4be4e513ba896ba52708a73d03eae`

Observation dates: 20 July 2026 at intake; 22 July 2026 at current reconciliation

## Authority boundary

This topic records evidence and unresolved design questions. It grants no implementation authority. The
normative design independently authorises one narrow Gate 0 contract-only precursor: inert Core value objects,
canonical serialization, pure validation, focused tests, and repository boundary validation. Research does not
create or expand that authority. In particular, it does not approve a service, persistence, filesystem access,
process launch, a Unity or Blender version, a native extension, game-install inspection, BepInEx or Harmony
execution, deployment, game launch, runtime mutation, save access, live IPC, or publication.

The normative authority remains
`docs/tainted-grail-sdk/EDITOR_TOOLCHAIN_UNITY_INTERCHANGE_DESIGN.md` and
`docs/tainted-grail-sdk/EXTERNAL_TOOL_INTERCHANGE_GATE_0.md`. Gate 0 may proceed before Phase 9 only within its
Core-only boundary. The Phase 9 prerequisite continues to control Gates 1 and later.

## Preserved input

The supplied report is preserved unchanged at
`inputs/FOA_SDK_O3DE_TO_UNITY_CONVERSION_AND_RUNTIME_BRIDGE_RESEARCH_REPORT.md`.

SHA-256 at intake:

```text
b17850a12efe97dbd92a8bdf9cfcd155204105c49e230c51cf9b10aceba9c048
```

The report contains opaque citations such as `turn5view4` and `turn34search0`. Those identifiers are local to
the conversation that produced the report. They are not durable, resolvable repository citations and cannot
support implementation, compatibility, licensing, or runtime decisions. Durable sources are recorded in
[`SOURCE_REGISTER.md`](SOURCE_REGISTER.md); unresolved report claims remain marked unsupported or unverified
in [`CLAIM_REGISTER.md`](CLAIM_REGISTER.md).

## Current reconciled synthesis

[`FOA_SDK_PORTING_METHODS_RESEARCH.md`](FOA_SDK_PORTING_METHODS_RESEARCH.md) records the current source-backed
porting-method conclusion. It reconciles repository drift through current `main`, corrects the distinction
between exact pinned Mono/IL2CPP route observations and an unselected active operator target, and selects a
canonical file-backed interchange package with separate shared domain documents and format-specific payloads
as the research direction.

The synthesis is a research conclusion only. It does not select a schema version, tool version, runtime route,
or operational capability.

## Research lanes

| Area | Purpose |
| --- | --- |
| `01-architecture-and-repository-state` | Exact repository baseline, existing ownership, and contradictions |
| `02-authoring-interchange-and-assets` | Package contracts, identities, transforms, materials, animation, losses, and Asset Processor handoff |
| `03-external-toolchain-host` | Generic provider discovery and separately gated process supervision |
| `04-blender-provider` | Blender discovery, native extension candidates, compatibility, and round trips |
| `05-unity-editor-interchange` | Synthetic or user-owned Unity Editor project interchange only |
| `06-runtime-target-profile` | Pinned route observations versus unselected active operator target, loading evidence, and diagnostic boundaries |
| `07-foa-runtime-adapters` | Separate Mono/IL2CPP route, build, deployment, execution, cleanup, rollback, and evidence-return research |
| `08-security-privacy-legal-and-licensing` | Trust, provenance, content, path, log, dependency, licence, and redistribution boundaries |
| `09-qualification-and-experiments` | Synthetic fixtures, compatibility matrices, deterministic comparisons, and negative tests |

## Claim states

- `unverified` — no durable supporting source has been registered;
- `source-supported` — a durable source supports the scoped statement;
- `repository-observed` — the exact repository baseline supports the statement;
- `fixture-verified` — an accepted, reproducible fixture supports the statement;
- `contradicted` — an accepted source or invariant conflicts with the statement;
- `superseded` — a later accepted record replaces the statement.

`source-supported` and `repository-observed` are evidence states, not qualification or permission states.

## Reconciliation summary

The report's four proposed handoff/result envelopes informed the independently approved Gate 0 contract-only
precursor. At Gate 0 they remain disabled, `NotAttempted` Core documents consumed by no service. The report's
file-backed Unity batch execution, exact tool locks, candidate-evidence intake, and host-owned supervision stay
later research candidates. Its proposed BepInEx compilation, game deployment, plugin-load evidence, and
rollback slice remains incompatible with current authority and belongs to the separately reviewed runtime lane
after the authoring interchange gates.

The current reconciliation preserves mandatory Blender-first ordering, canonical identity, transformation,
loss, and round-trip requirements. Exact pinned Mono and IL2CPP route observations now exist, but they do not
select an active target or authorise build, deployment, execution, game API access, runtime mutation, or save
access.

## Active next question

The research process now advances to:

[`areas/02-authoring-interchange-and-assets/CANONICAL_INTERCHANGE_SCHEMA_RESEARCH_QUESTION.md`](areas/02-authoring-interchange-and-assets/CANONICAL_INTERCHANGE_SCHEMA_RESEARCH_QUESTION.md)

That question covers the minimum schema 1 field inventory, identity and binding state machine, coordinate and
matrix basis, payload model, transformation and loss taxonomy, provenance/legal state, determinism classes,
validation rules, schema evolution, and qualification fixtures.

See [`gates/IMPLEMENTATION_GATE_MAPPING.md`](gates/IMPLEMENTATION_GATE_MAPPING.md) for the controlling order.
