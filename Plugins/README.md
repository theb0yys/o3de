# FOA-SDK plug-in systems

`Plugins/` is the product-owned root for optional FOA-SDK extension packages.

It is deliberately separate from `Gems/`:

- `Gems/ExternalToolchain` and `Gems/TaintedGrailModdingSDK` are foundational host components required by the product;
- packages under `Plugins/` are optional systems discovered, validated, selected, and registered through the governed ExtensionAPI;
- a plug-in manifest declares compatibility and capabilities but never grants runtime, deployment, save, signing, publication, catalog-mutation, or evidence-promotion authority.

## Layout

```text
Plugins/
├── README.md
├── plugin.schema.json
├── Authoring/
│   └── <Package>/
│       ├── plugin.json
│       ├── Code/
│       ├── Assets/
│       ├── Tools/
│       ├── Tests/
│       └── Docs/
├── Integrations/
│   └── <Package>/
│       └── plugin.json
└── RuntimeAdapters/
    └── <Package>/
        └── plugin.json
```

Only files required by a package should be present. Package directories are not valid without a root `plugin.json` conforming to `plugin.schema.json`.

## Categories

### Authoring

Optional editor-side systems that operate through read-only queries, governed authoring commands, candidate evidence, validation, and reviewed handoff contracts.

Planned destinations include:

- `Plugins/Authoring/AvalonAI/` for the custom AI authoring and validation layer;
- `Plugins/Authoring/UIFramework/` for reusable approved UI utilities and embedded assets;
- `Plugins/Authoring/RoadAtlas/` for the typed road domain and editor.

Authoring packages are editor-only unless a separately reviewed runtime adapter consumes their output.

### Integrations

Optional providers for external tools, acquisition routes, import/export bridges, and official or community workflows.

Planned destinations include:

- `Plugins/Integrations/MerlinsWorkshop/` for the optional Merlin's Workshop integration;
- additional local, pinned-GitHub, or approved acquisition providers.

External process discovery and execution must route through `Gems/ExternalToolchain`. Integration packages may not silently download, redistribute, execute, promote, or publish content.

### RuntimeAdapters

Target-specific runtime packages that consume reviewed work orders and return evidence.

Mono and IL2CPP must remain separate packages, with separate compatibility declarations, dependencies, binaries, tests, and evidence. A successful declaration or build does not itself authorize deployment or execution.

## Package contract

Every package must provide a canonical `plugin.json` containing:

- a stable namespaced extension ID and semantic version;
- one category matching its directory;
- explicit entry points;
- deterministic dependency and capability declarations;
- exact game-version, branch, and runtime compatibility;
- source provenance, licence state, and redistribution-review state.

Discovery must fail closed for malformed manifests, duplicate IDs, missing dependencies, dependency cycles, unknown capabilities, unsupported profiles, branch drift, version drift, or unsafe paths.

Registration is deterministic and occurs through `TaintedGrailModdingSDK::ExtensionAPI`. Packages receive no mutable catalog, workspace, profile, source-registry, runtime, deployment, save, signing, or publication references.

## Import rule

Existing systems are ported into this root one reviewed package at a time. Canonical knowledge, golden fixtures, provenance, licences, branch applicability, and tests must land before executable integration. Proprietary game files, unlicensed upstream assets, credentials, personal paths, generated binaries, caches, and runtime captures do not belong in the repository.
