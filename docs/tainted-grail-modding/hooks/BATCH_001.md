# Semantic Hook Batch 001

## Identity

- source repository: `theb0yys/Tainted-Grail-The-Fall-of-Avalon-mods`
- source commit: `d7e740e7f167b73152b53409e483dab07d80d048`
- source root licence: `NOASSERTION`
- batch scope: seven selected patch, reflection, registrar, and template sources
- authority: documentation and research classification only

This batch applies the completion rule from the pinned file inventory. Every selected source has exactly one primary disposition: a complete candidate hook record, a canonical system fact, a research blocker, or an explicit rejection record.

## Results

| Selected source | Source blob | Primary result | Destination |
|---|---|---|---|
| `mods/wyrd-hunt/src/Patches/NpcDeathPatch.cs` | `7e4915918da28cdcb3b257ea46cf31ae2d427c0f` | candidate hook record | `records/ACTORS_NPC_DEATH.md` |
| `mods/wyrd-hunt/src/Patches/ReadableStealPatch.cs` | `4d58a71ebab00c050ce3907e25b9dac4085212d2` | candidate hook record | `records/CRIME_READABLE_STEAL.md` |
| `mods/smart-save-backups/src/Patches/CloudServiceEndSavePatch.cs` | `29aa7491292de7faa8e6d8df2662d51201b2296d` | four-target candidate hook family | `records/PERSISTENCE_CLOUD_END_SAVE.md` |
| `mods/foa-mod-manager/src/Patches/MenuButtonPatch.cs` | `b289d4a510bf0cb1a0f146710f3892cd7b33ffc7` | method-patch and reflection candidate family | `records/UI_MENU_INITIALIZE.md` |
| `mods/TaintedEconomy/src/Patches/PatchRegistration.cs` | `f6997889aa3468e8692602423b8ce8481648ad26` | canonical source-system fact; not a hook | `../systems/items-economy/PATCH_REGISTRATION_FACT.md` |
| `mods/avalon-mounts/src/Plugin.cs` | `896e0f4e63c57b1800eb3ac09468cefe0ca8509d` | research blocker requiring decomposition | `blockers/AVALON_MOUNTS_PLUGIN.md` |
| `templates/mod-template/src/Patches/ExamplePatch.cs` | `4ea2d9fcb2885f9beee694d83d60f3d87b30468e` | explicit `not-a-hook` rejection | `rejections/TEMPLATE_EXAMPLE_PATCH.md` |

## Batch counts

- selected source files: 7
- candidate hook records: 9
  - two direct Harmony postfix records;
  - four cloud-service `EndSave(string)` variants;
  - two UI initialization method targets;
  - one reflected UI field target.
- canonical system facts: 1
- research blockers: 1
- explicit rejection records: 1
- promoted hooks: 0

## Promotion state

Every hook in this batch remains `candidate`. The pinned source proves source intent and target spelling only. It does not prove an exact current assembly fingerprint, exact game branch, exact loader version, successful target resolution, successful patch registration, intended behavior, unload cleanup, or combined-mod compatibility for the FOA-SDK supported profiles.

No record in this batch grants permission to inspect a game installation, load proprietary assemblies, deploy a mod, execute Harmony, launch the game, mutate runtime state, read or write saves, or promote evidence.

## Shared blockers

Before any candidate can advance:

1. bind the target to an exact game version, branch, runtime, loader, and assembly fingerprint;
2. resolve the exact type, member, overload, parameter list, and return type;
3. inspect the patch callback and all downstream handlers;
4. prove registration is fail-safe when the target is absent or changed;
5. prove plugin load and deterministic unpatch/unsubscribe cleanup;
6. capture bounded behavior evidence for the intended scenario;
7. test collisions, ordering, duplicate registration, and combined-mod behavior;
8. record save, story, performance, UI, and privacy effects.

## Next batch boundary

Batch 002 should decompose the Avalon Mounts blocker and then process the first economy registrar callers. A centralized registrar helper is never treated as evidence for the caller-supplied game targets.