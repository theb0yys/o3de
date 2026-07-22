# Installer tests

Installer-specific tests belong here when they are not production-linked tests owned by the SDK foundation.

Required coverage includes deterministic suite/package resolution, schema rejection, dependency and conflict handling, exact inventories, path safety, case collisions, symlink/reparse-point refusal, clean install, repair, upgrade, rollback, uninstall, workspace preservation, and negative authority checks.

Generated payloads, MSI files, ZIP archives, logs, receipts, registry captures, and screenshots belong beneath the external build/evidence root.

## Execution-security regression lane

`Security/` and the operational bootstrapper suites prove wrong-key rejection, exact resolver and helper binding, capability denial, one-shot nonce consumption, bounded output, process-tree timeout handling, controlled elevation bootstrapper requests, no-replace staging publication, and authenticated installation-state publication.
