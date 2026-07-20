# O3DE to Unity Conversion and Runtime Bridge Research

Status: research intake and reconciliation

Repository baseline: `92aa29960bab92d646c464ae48b8cf09d881a436`

Observation date: 20 July 2026

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

## Research lanes

| Area | Purpose |
| --- | --- |
| `01-architecture-and-repository-state` | Exact repository baseline, existing ownership, and contradictions |
| `02-authoring-interchange-and-assets` | Package contracts, identities, transforms, materials, animation, losses, and Asset Processor handoff |
| `03-external-toolchain-host` | Generic provider discovery and separately gated process supervision |
| `04-blender-provider` | Blender discovery, native extension candidates, compatibility, and round trips |
| `05-unity-editor-interchange` | Synthetic or user-owned Unity Editor project interchange only |
| `06-runtime-target-profile` | Unknown FoA version, branch, Unity player, scripting backend, loader, and content-loading evidence |
| `07-foa-runtime-adapters` | Separately reviewed runtime build, deployment, execution, cleanup, rollback, and evidence-return research |
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
after the authoring interchange gates. The report also omits the mandatory Blender-first ordering and the
existing canonical identity, transformation, loss, and round-trip requirements.

See [`gates/IMPLEMENTATION_GATE_MAPPING.md`](gates/IMPLEMENTATION_GATE_MAPPING.md) for the controlling order.
