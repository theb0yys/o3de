# Graphical Suite Wizard host

`Installer/SuiteWizard/Host/` owns the native graphical review, confirmation, and receipt-export host for the FOA-SDK installer catalogue.

The host imports the engine-neutral `Catalog/`, `ViewModel/`, and `Receipt/` contracts directly. It does not parse suite/package manifests independently and does not reproduce dependency, compatibility, conflict, legal, ordering, payload-collision, acknowledgement, confirmation, receipt, or fingerprint logic.

## Launch

From the FOA-SDK checkout:

```powershell
python Installer/SuiteWizard/Host/Source/suite_wizard_receipt_host.py `
  --installer-root Installer
```

The host uses Python's standard-library `tkinter` and themed `ttk` widgets. If native Tk support or a graphical display is unavailable, startup fails closed with a diagnostic and performs no fallback mutation.

`suite_wizard_host.py` remains the confirmation-stage entry point used by its focused tests. `suite_wizard_receipt_host.py` is the complete current graphical entry point.

## User flow

The **Choose** page displays:

- the exact reviewed `catalog_sha256`;
- reviewed suite identity, version, channel, and description;
- compatibility context fields;
- required, default, and optional package rows;
- exact package versions, status, payload totals, and licence expressions;
- reviewed feature groups and their package references.

Required packages are visible and locked. Default packages begin included and may be explicitly excluded. Optional packages begin excluded and may be explicitly selected. Feature choices are submitted as feature IDs; the host does not calculate their dependency effect.

The **Resolve review** action creates the exact review-only selection through `Catalog/`, then asks the existing resolver and view-model layers for the current result. The **Review** page displays:

- `catalog_sha256`;
- `selection_sha256`;
- `plan_sha256`;
- `view_model_sha256`;
- `result_sha256`;
- resolver-owned package order;
- planned destination paths, sizes, and payload hashes;
- warnings;
- required acknowledgement text.

The **Confirm** page renders every required acknowledgement as an explicit checkbox and collects caller-supplied confirming identity plus an ISO-8601 UTC timestamp. The host compares the displayed `plan_sha256` and `view_model_sha256` with the exact current in-memory review before delegating confirmation creation and verification to `ViewModel.create_confirmation()` and `ViewModel.verify_confirmation()`.

A successful confirmation displays:

- the exact bound `plan_sha256`;
- the exact bound `view_model_sha256`;
- `confirmation_sha256`;
- the exact acknowledged ID set;
- caller-supplied identity and UTC time;
- the immutable review-only statement;
- an all-false authority record.

The **Receipt** page is enabled only for the exact current confirmation. It can:

- export a caller-selected `.foa-receipt.json` file through `Receipt.publish_receipt()`;
- verify an existing canonical receipt against the exact current plan, view-model, acknowledgement set, and confirmation;
- display `plan_sha256`, `view_model_sha256`, `confirmation_sha256`, and `receipt_sha256`;
- display the selected path, canonical byte count, immutable statement, and all-false authority result.

The graphical host never serializes or writes receipt bytes itself. It delegates to the reviewed create-once receipt publisher, which rejects symbolic-link paths, noncanonical bytes, stale fingerprints, and replacement of a different existing file.

Refreshing the catalogue or changing any suite, package, feature, compatibility context, acknowledgement, confirmer identity, or timestamp invalidates the applicable displayed review, confirmation, and receipt state. Manifest drift after discovery is rejected by the existing stale-catalogue gate.

## Validation

The complete native smoke resolves the production catalogue, accepts every required acknowledgement, creates the exact confirmation, exports a canonical receipt to a temporary external evidence directory, verifies it against the current chain, renders the Receipt page, and exits. This smoke exercises no installer or runtime capability.

The authoritative PR static workflow invokes this complete smoke under Xvfb after all mandatory-discovery Python tests and validators pass. The workflow preserves the combined static and graphical log as exact-run evidence.

## Authority boundary

This host is review and evidence-export only. It has no downloader, network client, package copier, installer engine, elevation helper, launcher, runtime executor, deployment service, save mutator, signer, network publisher, catalogue mutator, or evidence promoter.

There is no install or execution button. A receipt grants no operational authority. Any later acquisition or execution unit must be separately reviewed and must reverify the complete plan, view-model, acknowledgement, confirmation, and receipt chain before receiving capability.
