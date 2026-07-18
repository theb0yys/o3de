# Tainted Grail Modding Infrastructure

This folder records the shared infrastructure boundaries used by the Tainted Grail Modding SDK and Editor.

## Active build modules

The first two scaffolded boundaries now have real internal build targets while source paths remain stable under `Code/Source`:

- `TaintedCore/` maps to `TaintedGrailModdingSDK.Core.Static` for shared domain primitives and pure core services;
- `TaintedFramework/` maps to `TaintedGrailModdingSDK.Framework.Static` for persistence, path policy, workspace loading, and Foundation orchestration;
- the Tool Gem `Editor` target owns Qt widgets, the Editor system component, and module composition.

`Core.Static` and `Framework.Static` are internal implementation targets. Only the existing Editor module is exposed through the Tool and Builder aliases.

## Reserved scaffold modules

These folders remain scaffolding only and have no build target or runtime behavior:

- `TaintedUI/` - future reusable Editor UI components and presentation contracts;
- `Exceptions/` - future error types, diagnostics, and failure-reporting contracts;
- `AI/` - future AI-facing contracts and integrations approved by project research.

Implementations remain evidence-gated: each new module needs a documented contract, ownership boundary, dependencies, and validation requirements before build integration.

## Dependency direction

`Core.Static` is the lowest shared layer. `Framework.Static` depends on Core, and Editor depends on Framework. Core must not depend on Framework, Editor, UI, AI, Qt, AzToolsFramework, or runtime integrations. Cross-module behavior is exposed through existing documented C++ interfaces rather than duplicate compilation or reverse implementation coupling.

Tests link `Framework.Static` and receive Core transitively. Test manifests own tests only; every production translation unit has exactly one production target owner.

## Runtime boundary

This build split remains entirely editor-side. It adds no FoA runtime adapter, game launch, deployment, injection, save mutation, or telemetry behavior.
