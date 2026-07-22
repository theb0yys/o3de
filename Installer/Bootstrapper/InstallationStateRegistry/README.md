# Installation state registry

`InstallationStateRegistry/` is the read-only installer state discovery and lifecycle eligibility gate.

It reads SDK-owned installation-state records produced by `InstallationStatePublisher/`, validates the canonical state-file bytes, and emits deterministic registry snapshots plus lifecycle eligibility decisions for:

```text
install
repair
upgrade
rollback
uninstall
```

## Capability

```text
package-engine.query-installation-state
```

This capability is represented by read-only snapshot and eligibility documents. It grants no package copy, process launch, elevation, lifecycle execution, installation-state publication, runtime execution, save mutation, signing, network publication, catalogue mutation, product/game directory mutation, or evidence promotion authority.

## Registry behavior

The registry reader:

- accepts only an absolute existing non-symlink SDK state root;
- scans direct canonical `*.json` state files;
- rejects symbolic links, invalid JSON, non-canonical JSON, filename/reference mismatch, duplicate state references and duplicate state-file fingerprints;
- validates every record through the installation-state publisher contract;
- emits sorted deterministic snapshots;
- derives read-only lifecycle eligibility for all five lifecycle operations.

## Eligibility model

- No current state: `install` is eligible; maintenance operations are blocked.
- Active current state: `repair`, `upgrade` and `uninstall` are eligible; duplicate `install` is blocked.
- Rollback requires a current state with an explicit prior installation reference.
- Removed state allows reinstall and blocks maintenance operations.

Eligibility decisions are recommendations only. They do not create lifecycle handoffs or grant later authority.
