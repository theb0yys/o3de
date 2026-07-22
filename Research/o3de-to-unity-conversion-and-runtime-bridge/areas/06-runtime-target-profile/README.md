# Runtime Target Profile

## Current evidence state

Runtime evidence must be separated into two scopes.

### Pinned upstream route observations

The repository contains exact route observations for two separate adapter families:

| Route | Evidence state | Framework | Game | Branch | Runtime | Unity | BepInEx | Licence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `adapter.foa.mono` | `HostLiveLoadValidated` | `0.1.33` | `1.23.401` | `mono` | `Mono` | `6000.0.64f1` | `5.4.23.3` | `NOASSERTION` |
| `adapter.foa.il2cpp` | `PackageInstallValidated` | `0.1.36` | `1.23.401` | `il2cpp` | `IL2CPP` | `6000.0.64f1` | `6.0.0-be.735` | `NOASSERTION` |

Source:

https://github.com/theb0yys/FOA-SDK/blob/8fb3f0a729e4be4e513ba896ba52708a73d03eae/Gems/TaintedGrailModdingSDK/Code/Source/FoARuntimeAdapterRoutes.cpp#L99-L183

These observations are bound to the pinned upstream system-port evidence. They are not active-target selection, dependency-redistribution approval, or executable adapter authority.

### Active operator profile

The following remain unselected for an operator-provided lawful installation and a requested future capability:

- exact installation and build identity;
- selected distribution branch;
- selected Mono or IL2CPP route;
- verified managed/native assembly layout;
- verified Addressables, AssetBundle, `Resources`, or custom loading behavior;
- exact runtime APIs and log locations required by the requested capability;
- reviewed dependency acquisition, licensing, and redistribution state.

No route is selected automatically from community reports, filenames, prior installations, or the existence of a route descriptor.

## Capability boundary

The current Mono route blocks:

- `adapter.build`;
- `adapter.deploy`;
- `adapter.execute`;
- `game-api-access`;
- `runtime-mutation`;
- `save-access`.

The current IL2CPP route blocks the same capabilities and also blocks `feature-tested-gameplay`.

Route evidence therefore cannot be interpreted as permission to build, deploy, execute, mutate, or access saves.

## Future evidence boundary

Exact active-profile capture is not part of provider discovery or Unity Editor interchange. It requires a separately reviewed, bounded, read-only diagnostic plan after the FoA mapping/runtime-extension gate.

That plan must name:

- the exact operator-provided installation scope;
- the requested capability and why each observation is necessary;
- permitted files, metadata, APIs, and log locations;
- path and privacy treatment;
- output schema and canonical fingerprints;
- redaction and retention;
- legal basis and dependency licensing;
- failure behavior;
- candidate-evidence review and promotion boundaries.

It must not automatically discover installations, recursively scan disks, extract assets, copy assemblies, inspect saves, or commit proprietary/private material. Lawful possession is necessary but does not itself grant the SDK authority to inspect or persist data.

## Output state

A future capture returns source observations or candidate evidence. It does not automatically select Mono or IL2CPP, approve a loader, promote catalog facts, authorize compilation, deployment, game launch, runtime mutation, or save access.
