# Architecture and Repository State

## Scope

This area records the exact repository baseline, implemented services, proposed designs, and discrepancies
between research material and repository truth.

Current baseline: `92aa29960bab92d646c464ae48b8cf09d881a436`, observed on
`FOA-plug-in-development` on 20 July 2026.

## Established repository boundaries

- O3DE is the editor host; FoA remains a separate Unity runtime target.
- Core owns typed, deterministic contracts and intrinsic validation without filesystem, process, network,
  editor, Unity, Blender, or game dependencies.
- Framework owns evidence binding, persistence, contained staging, and candidate-before-publish orchestration.
- Editor panes remain thin clients.
- Runtime adapters separately own Unity/FoA API calls, BepInEx/Harmony behavior, persistence, cleanup, and
  rollback after reviewed handoff.
- `ExternalToolchain` currently owns registration, configuration, bounded local discovery, and diagnostics;
  it does not execute providers.
- The normative working-tree amendment authorises Gate 0 Core-only handoff/result envelopes, canonical helpers,
  pure validation, focused tests, and boundary validation before Phase 9. It adds no service or operational
  authority.

## Research tasks

1. Reconfirm repository observations at the exact head used by each later experiment.
2. Distinguish Gate 0 contract implementation from proposed Phase 9 Gate 1+ behavior.
3. Record contradictions in `../../CLAIM_REGISTER.md` rather than silently rewriting supplied material.
4. Keep current first-party domain ordering unchanged.

## Exclusions

This area does not approve a schema, provider, process supervisor, runtime target, game inspection, build,
deployment, or execution. Normative sources are registered as `SRC-REPO-001` through `SRC-REPO-017` in
`../../SOURCE_REGISTER.md`.
