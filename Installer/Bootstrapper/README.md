# Installer bootstrapper

This directory owns bounded prerequisite detection, reviewed package acquisition, hash and policy verification, and the transition into the suite wizard or package engine.

The bootstrapper must fail closed for unsupported hosts, missing prerequisites, source or hash drift, unsafe paths, dependency cycles, unreviewed redistribution, partial acquisition, unexpected elevation, and stale suite definitions.

Network access, process execution, and elevation are explicit reviewed capabilities. They are never inferred from package presence. The bootstrapper grants no FoA launch, deployment, runtime, save, signing, publication, catalog-mutation, or evidence-promotion authority.

## Approved-acquisition handoff

`Acquisition/` implements the first capability-gated handoff from an exact Suite Wizard plan and review-only confirmation into the existing approved local or pinned-GitHub provider.

The handoff:

- reverifies the resolver plan, view-model, confirmation, and provider plan;
- requires explicit `acquisition.approved.<provider-package-id>` package capabilities;
- requires exact provider-package coverage with no implicit name matching;
- requires the reviewed suite network policy before pinned-GitHub use;
- creates a named, time-bounded acquisition-only request;
- permits only acquisition, required external filesystem writes, and route-specific network access;
- invokes only `Plugins/Integrations/ApprovedAcquisition`;
- verifies the provider bundle again before producing a result;
- records no private output path and retains no authority after completion.

It does not install, repair, upgrade, roll back, uninstall, elevate, launch, deploy, mutate saves, sign, publish, mutate the catalog, or promote evidence. Those remain later separately reviewed package-engine and release units.
