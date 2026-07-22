# Rejection Record — Template ExamplePatch

```yaml
rejection_id: tg.rejection.hooks.template-example-patch-no-target
status: rejected
reason_code: not-a-hook
source_repository: theb0yys/Tainted-Grail-The-Fall-of-Avalon-mods
source_commit: d7e740e7f167b73152b53409e483dab07d80d048
source_path: templates/mod-template/src/Patches/ExamplePatch.cs
source_blob: 4ea2d9fcb2885f9beee694d83d60f3d87b30468e
licence: NOASSERTION at repository root
```

## Decision

This file is explicitly rejected from the hook catalogue because it does not register, resolve, declare, subscribe to, or invoke any game hook.

Its `Apply` method accepts a Harmony instance and logger, then logs that no Harmony patches are registered. There is no target type, member, signature, event, service, reflection lookup, patch method, ordering rule, or cleanup requirement to catalogue.

## Retained value

The source remains useful only as a **no-gameplay-patch starter pattern**:

- a first mod can load and log without targeting the game;
- Harmony can be passed into a future registration lane without inventing a placeholder target;
- the starter does not normalize unsafe copy-paste patching.

That value belongs to the first-mod tutorial and future project-owned starter implementation, not the hook catalogue.

## Prohibited interpretation

This rejection must not be converted into:

- a candidate hook with `unknown` target fields;
- proof that Harmony initialized successfully;
- proof that the owning template loads in any game profile;
- permission to add an arbitrary demonstration patch;
- a supported example of runtime mutation.

A future starter patch enters the catalogue only when it names a separately reviewed target and satisfies the normal candidate record contract.