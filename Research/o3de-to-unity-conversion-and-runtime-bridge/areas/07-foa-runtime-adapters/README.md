# FoA Runtime Adapters

## Separation from authoring interchange

A FoA runtime adapter is not a Unity Editor interchange provider. It has its own stable adapter identity,
runtime-target compatibility, capabilities, permissions, build inputs, package, deployment work order,
execution result, cleanup, rollback, and evidence-return contracts.

The supplied report's hybrid runtime core, generated registration modules, Mono-first path, BepInEx build, and
no-op plugin are research candidates only. They are not accepted architecture and do not belong in the first
authoring slice.

## Runtime re-entry sequence

Runtime work may be considered only after the authoring gates and a separate FoA mapping/runtime-payload review:

```text
exact target-profile evidence
→ target-specific adapter design
→ synthetic or mock-host build proof
→ reviewed build manifest and package
→ deployment preview
→ explicit confirmation and exact work order
→ separately approved executor with backup and rollback
→ no-op load evidence
→ independent verification
→ candidate evidence intake
→ separately reviewed bounded capability
```

Save or persistence mutation remains an independent later gate.

## Ownership constraints

- The Unity Editor package does not contain or build the runtime adapter.
- `ExternalToolchain` may supervise a generic approved builder later; it does not own game API behavior.
- Runtime adapters own BepInEx/Harmony/Unity/FoA calls and capability-specific cleanup.
- A successful compile, process exit, deployment copy, or plugin load does not establish gameplay compatibility
  or grant another capability.
- Manual deployment is not an authoring acceptance criterion.

No research in this area authorises BepInEx/Harmony execution, deployment, game launch, runtime mutation, or
save access.
