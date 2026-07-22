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
- rejects blocked, timed-out, nonzero and elevation-pending lifecycle results;
- writes only inside an absolute, existing, non-symlink SDK state root;
- uses the expected previous-state hash to prevent stale overwrite;
- writes canonical JSON bytes to a deterministic same-directory temporary file;
- fsyncs the file and atomically replaces the target state file;
- emits a publication receipt bound to the exact state record and lifecycle result.

## Boundary

This gate does not copy payloads, launch processes, request elevation, execute runtime adapters, mutate saves, sign artifacts, publish releases, mutate catalogues, promote evidence, or touch product/game directories.

The state record and publication receipt both explicitly preserve those forbidden side-effect flags as false.

## Security hardening

Installation-state publication requires its explicit session capability and a completed authenticated lifecycle result. Grants are one-shot; records and receipts are authenticated; initial creation is no-replace and replacement requires the exact previous-state hash.
