# Getting Started

This lane will provide the shortest safe path from no local setup to a validated, removable first mod.

## Planned read order

1. Choose an exact game branch and runtime profile.
2. Install and verify the matching loader without committing its binaries.
3. Obtain FOA-SDK and its pinned external O3DE dependency when SDK authoring is needed.
4. Create a project-owned mod workspace.
5. Configure local assembly references through a private path property.
6. Set plugin identity, version, dependencies, logging, and configuration.
7. Build without copying proprietary dependencies into output.
8. Produce a deterministic test package.
9. Deploy to a controlled local target through the applicable reviewed route.
10. Verify loader discovery and plugin startup in logs.
11. Exercise one bounded behavior.
12. Remove the mod and confirm cleanup.

## Pages to produce

- supported profiles and prerequisites;
- Mono first-mod tutorial;
- IL2CPP first-mod tutorial after an executable route is actually qualified;
- local reference configuration;
- project identity and dependency conventions;
- build and package layout;
- controlled test deployment and removal;
- first validation receipt;
- first troubleshooting checklist.

## Publication gate

No first-mod tutorial may be marked reviewed until it has been completed from a clean workspace against the exact documented game, branch, runtime, loader, framework, and SDK profile. A contract-only or inert adapter route is described as such and does not receive an executable tutorial.