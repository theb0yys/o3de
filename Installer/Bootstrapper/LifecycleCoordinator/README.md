# Lifecycle execution coordinator

`LifecycleCoordinator/` is the installer operation-level coordination gate for:

```text
install
repair
upgrade
rollback
uninstall
```

It consumes one exact verified package-engine session and issues one short-lived lifecycle grant for the matching `package-engine.execute.<operation>` capability.

## Evidence model

The coordinator does not copy payloads, launch processes, request elevation, run runtime adapters, mutate saves, sign artifacts, publish releases, mutate catalogues, or promote evidence.

Instead, it consumes already-verified lower-level evidence:

- package payload copy receipt from `PackageCopier/`;
- process-launch result from `ProcessLauncher/`;
- elevation result from `ElevationHelper/` when the lifecycle grant explicitly allows it.

Install, repair, and upgrade require a verified copy receipt because those operations depend on staged payload evidence. Rollback and uninstall do not require a copy receipt, but every operation requires either process-launch or elevation evidence.

## Elevated operations

An elevation result proves only that the operating system accepted an explicit elevation request. It does not prove process completion, installer success, or product state mutation. The coordinator therefore records elevated operations as:

```text
elevation-requested-pending-completion-receipt
```

A later completion/finalization receipt must close that loop.

## Result boundary

A lifecycle result may mark a non-elevated operation as `completed` only when the exact process-launch result reports `return_code = 0` and `timed_out = false`.

The result always records the following forbidden side effects as false:

- product or game directory mutation;
- runtime execution;
- save mutation;
- signing;
- publication;
- catalogue mutation;
- evidence promotion.

This gate coordinates lifecycle evidence. Installation-state publication remains a later isolated gate.

## Security hardening

Lifecycle grants and results are authenticated, one-shot records and every consumed copy, launch, elevation, or bootstrapper-completion receipt is reverified against the same session trust anchor.
