# Suite wizard

This directory owns the current engine-neutral FOA-SDK catalogue-selection interface, native graphical suite-selection/review/confirmation/receipt host, and deterministic confirmation-receipt publisher.

The wizard presents reviewed suites and packages, prerequisites, exact versions, provenance, licences, compatibility, disk use, conflicts, planned filesystem changes, elevation, rollback behavior and required acknowledgements before confirmation.

`Catalog/` is the read-only discovery and explicit-selection interface. It enumerates reviewed suite/package manifests, emits a canonical catalogue fingerprint, rejects stale selections, delegates package decisions to the resolver, and returns the existing presentation view-model. Its command-line surface remains available for deterministic inspection and automation.

`Host/` is the current native graphical surface. It imports `Catalog/`, `ViewModel/`, and `Receipt/` directly, displays reviewed suite/package/feature choices, captures explicit package and feature selections, submits compatibility context, and renders the returned resolver/view-model rows. It then collects the exact required acknowledgement set plus caller-supplied identity and UTC time, creates the exact review-only confirmation, and can export or verify the matching canonical receipt. The host does not calculate dependency effects, acknowledgement requirements, confirmation or receipt fingerprints, or alter resolver/view-model output.

`Resolver/` is the engine-neutral source of truth for package decisions. The wizard submits explicit selections, exclusions, features and compatibility context to the resolver, then displays its canonical plan and diagnostics. UI code may not recalculate dependency closure, version constraints, conflicts, compatibility, path safety, legal state, package ordering, payload collisions or plan fingerprints.

`ViewModel/` is the pure presentation and review-confirmation layer. It verifies the exact resolver plan, derives stable package/payload rows and acknowledgement requirements, and creates and verifies a review-only confirmation bound to both `plan_sha256` and `view_model_sha256`.

`Receipt/` is the deterministic local persistence layer. Before producing bytes it re-verifies the exact plan, view-model, complete acknowledgement set and confirmation. It emits a self-contained canonical JSON bundle with `receipt_sha256`, uses create-once atomic publication, rejects symlink paths and noncanonical bytes, and never replaces a different existing file.

The current flow is:

```text
reviewed manifests
    → Catalog discovery (`catalog_sha256`)
    → Host package/feature/context choices
    → explicit review-only selection (`selection_sha256`)
    → Resolver plan (`plan_sha256`)
    → ViewModel presentation (`view_model_sha256`)
    → graphical review display (`result_sha256`)
    → explicit acknowledgement set + caller identity/time
    → verified review-only confirmation (`confirmation_sha256`)
    → graphical export or verification of the canonical local receipt (`receipt_sha256`)
```

Launch the complete graphical host from the product checkout with:

```powershell
python Installer/SuiteWizard/Host/Source/suite_wizard_receipt_host.py `
  --installer-root Installer
```

The Receipt page delegates all writes and verification to `Receipt/Source/confirmation_receipt.py`; generated receipt files belong beneath the external build/evidence root and must use the `.foa-receipt.json` suffix.

Wizard code must remain a thin presentation layer over deterministic suite resolution and installer services. It may not silently acquire packages, bypass hash or redistribution review, enable runtime adapters, launch FoA, deploy files, mutate saves, sign artifacts, upload receipts, publish releases, mutate the catalog, or promote evidence.

A valid resolution plan, confirmation, and receipt remain non-executable. Any later acquisition or execution layer must be separately designed and must reverify the exact current plan, view-model, acknowledgement set, confirmation, and receipt before receiving capability.

Generated binaries, plans, confirmations, receipts and screenshots belong under the external build/evidence root, not in this directory.
