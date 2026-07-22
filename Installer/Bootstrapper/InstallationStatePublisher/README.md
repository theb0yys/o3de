# Installation state publisher

`InstallationStatePublisher/` is the installer state-ledger publication gate.

It consumes one exact verified package-engine session and one completed lifecycle coordinator result, then publishes a canonical SDK-owned state record under a caller-supplied state root.

## Capability

```text
package-engine.publish-installation-state
```

This capability is represented by a short-lived publication grant. The grant binds:

- the exact package-engine session;
- the exact completed lifecycle result;
- the installation state reference;
- the expected previous state-file SHA-256, or `null` for first publication;
- issuer, nonce and bounded UTC validity window.

## Publication behavior

The publisher:

- accepts only lifecycle results with `status = completed` and `lifecycle_completed = true`;
- accepts non-elevated completed lifecycle results as before;
- accepts elevated completed lifecycle results only when `elevation_request_confirmed = true`, `elevated_completion_observed = true`, and `elevated_completion_observation_sha256` is present;
- rejects raw elevation-pending lifecycle results that are still `elevation-requested-pending-completion-receipt`;
- rejects blocked, timed-out, nonzero and output-limit lifecycle results;
- records elevated lifecycle provenance on the state record without giving that record new authority;
- writes only inside an absolute, existing, non-symlink SDK state root;
- uses the expected previous-state hash to prevent stale overwrite;
- writes canonical JSON bytes to a deterministic same-directory temporary file;
- fsyncs the file and atomically replaces the target state file;
- emits a publication receipt bound to the exact state record and lifecycle result.

## Elevated lifecycle policy

Raw `ElevationHelper/` results prove only that the operating system accepted the prompt. They remain non-publishable until `LifecycleCoordinator/` consumes an authenticated `ElevatedCompletionReceipt/` observation and produces a completed lifecycle result.

Completed elevated lifecycle results are publishable only after that observation is present. Blocked elevated lifecycle results remain non-publishable.

## Boundary

This gate does not copy payloads, launch processes, request elevation, execute runtime adapters, mutate saves, sign artifacts, publish releases, mutate catalogues, promote evidence, or touch product/game directories.

The state record and publication receipt both explicitly preserve those forbidden side-effect flags as false.

## Security hardening

Installation-state publication requires its explicit session capability and a completed authenticated lifecycle result. Grants are one-shot; records and receipts are authenticated; initial creation is no-replace and replacement requires the exact previous-state hash.
