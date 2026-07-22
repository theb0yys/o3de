# Runtime Routes

FOA-SDK treats Mono and IL2CPP as separate runtime routes with separate loaders, frameworks, binaries, evidence, packaging, and compatibility. A result from one route is never inherited by the other.

## Route record requirements

Every runtime profile must bind:

- exact game version and branch;
- runtime kind;
- loader name and exact version;
- framework/adapter name and exact version;
- target framework and compiler assumptions;
- required dependencies;
- source/build/package identities;
- installation and rollback scope;
- loader discovery and startup evidence;
- supported capabilities and explicit prohibitions;
- staleness and supersession state.

## Current known route state

The existing system-port track records exact pinned observations for:

- a Mono route using Tainted Framework `0.1.33` with host live-load evidence on its recorded profile;
- an IL2CPP route using Tainted Framework `0.1.36` with package install/load evidence on its recorded profile.

Those observations qualify only their exact profiles. Current active installation selection, executable SDK adapter packages, deployment, game launch, runtime mutation, and save access remain separately governed.

## Planned documentation

- runtime and loader concepts;
- choosing a profile;
- Mono environment and first-mod path;
- IL2CPP environment and first-mod path after executable qualification;
- local development references;
- dependency and framework compatibility;
- package layout and controlled deployment;
- log locations and startup diagnosis;
- adapter plan/build/staging/deployment lifecycle;
- rollback and removal;
- patch collision and load-order analysis;
- profile migration and staleness.

## Safety rule

No page may describe a contract-only or inert route as executable. Tutorials, commands, and package layouts are published only after exact-profile validation and must state the target and rollback boundary.