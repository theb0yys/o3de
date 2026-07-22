# Runtime Routes

FOA-SDK treats Mono and IL2CPP as separate runtime routes with separate loaders, frameworks, binaries, evidence, packaging and compatibility. A result from one route is never inherited by the other.

## Start here

Read [Verified Runtime and Loader Profiles](VERIFIED_PROFILES.md) for the exact currently pinned game, Unity, runtime, loader, framework and evidence observations.

The optional route packages are the [FOA Mono Runtime Adapter](../../tainted-grail-sdk/MONO_RUNTIME_ADAPTER.md) and the [FOA IL2CPP Runtime Adapter](../../tainted-grail-sdk/IL2CPP_RUNTIME_ADAPTER.md). Both contain project-owned source and non-executable planning/review contracts; neither includes a process executor or deployment authority.

## Route record requirements

Every runtime profile binds exact game/branch/runtime, loader and framework versions, target framework and compiler assumptions, dependencies, source/build/package identities, installation and rollback scope, startup evidence, capabilities, prohibitions, and staleness state.

## Current pinned route state

- Mono: FoA `1.23.401`, Unity `6000.0.64f1`, BepInEx `5.4.23.3`, Tainted Framework `0.1.33`, evidence state `HostLiveLoadValidated`.
- IL2CPP: FoA `1.23.401`, Unity `6000.0.64f1`, BepInEx `6.0.0-be.735`, Tainted Framework `0.1.36`, evidence state `PackageInstallValidated`.

Those observations qualify only their exact profiles. Installation selection, deployment, game launch, runtime mutation and save access remain separately governed.

## Implementation state

Completed independently for both routes: project-owned source package, exact manifest and compatibility, deterministic non-executable build plan, external-executor review gate with execution authorization disabled, typed external runtime-result evidence, and adversarial repository validation.

IL2CPP additionally requires exact generated-interop manifests for `Assembly-CSharp.dll` and `TG.Main.dll`; these inputs are never projected onto Mono.

Still required separately for each route: external source build against a lawful exact local profile, executor and controlled deployment/removal tooling, project-owned binary live-load evidence, hook-target verification, collision/load-order reports, and profile migration/staleness tooling.

## Safety rule

No page may describe a contract-only or inert route as executable. Tutorials, commands and package layouts are published only after exact-profile validation and must state the target and rollback boundary.
