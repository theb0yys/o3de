# Editor installation readiness

`EditorInstallationReadiness/` is the read-only bridge from the installer state ledger to editor tooling.

It consumes one validated `InstallationStateRegistry/` snapshot and emits a deterministic editor readiness document that tells the editor whether a published SDK installation is available to use.

## Capability

```text
tg-editor.consume-installation-state
```

This capability appears only on the readiness document. It does not copy packages, launch processes, request elevation, coordinate lifecycle execution, publish installation state, mutate products, run runtime adapters, mutate saves, sign artifacts, publish to the network, mutate catalogues, or promote evidence.

## Readiness model

The bridge reports:

- `ready` when exactly one active SDK installation state matches the editor request;
- `blocked-no-active-installation` when the registry is empty, removed, rolled back, or has no active matching target;
- `blocked-ambiguous-active-installation` when multiple active states match and the editor did not provide a narrowing target.

When ready, the document carries only read-only identity and evidence fields:

```text
state_reference
state_file_sha256
state_record_sha256
lifecycle_result_sha256
package_order
summary
```

If the published state came from an elevated installation, the readiness document also preserves the elevated completion provenance already stamped by `InstallationStatePublisher/`:

```text
elevation_request_confirmed
elevated_completion_observed
elevation_result_sha256
elevated_completion_observation_sha256
```

## Boundary

This bridge does not open editors, create panes, load plug-ins, write files, or mutate product/game directories. It exists so editor UI and action lanes can consume one canonical readiness document rather than interpreting installer receipts directly.

## Test path

The SDK discovery suite now includes the editor readiness tests, so the local test loop can verify:

```text
InstallationStatePublisher
→ InstallationStateRegistry
→ EditorInstallationReadiness
→ editor-ready or blocked status
```
