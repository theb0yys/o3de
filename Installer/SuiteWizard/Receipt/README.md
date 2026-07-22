# Suite Wizard confirmation receipts

`Installer/SuiteWizard/Receipt/` owns deterministic local persistence for the exact review-only confirmation produced by the Suite Wizard.

A receipt is a self-contained canonical JSON bundle containing:

- the exact validated resolver plan and `plan_sha256`;
- the exact validated view-model and `view_model_sha256`;
- the exact verified confirmation and `confirmation_sha256`;
- the immutable receipt statement;
- an all-false authority record;
- `receipt_sha256`, calculated over every preceding receipt field.

Receipt creation re-verifies the complete accepted chain before producing any bytes. A receipt does not grant acquisition, installation, elevation, game launch, runtime execution, deployment, save mutation, signing, network publication, catalogue mutation, or evidence promotion authority.

## Export

Use existing canonical plan, view-model, and confirmation JSON files:

```powershell
python Installer/SuiteWizard/Receipt/Source/confirmation_receipt.py export `
  --plan foa-build/evidence/plan.json `
  --view-model foa-build/evidence/view-model.json `
  --confirmation foa-build/evidence/confirmation.json `
  --output foa-build/evidence/review.foa-receipt.json
```

The destination parent must already exist and must contain no symbolic-link component. Receipt names must end in `.foa-receipt.json`.

Publication is create-once and non-overwriting. The publisher writes canonical bytes to a deterministic exclusive temporary file, flushes them, validates them again, then creates the destination atomically by hard-linking the verified file. An existing byte-identical canonical receipt is accepted as `already-current`; an existing different file fails closed.

## Verify

```powershell
python Installer/SuiteWizard/Receipt/Source/confirmation_receipt.py verify `
  --receipt foa-build/evidence/review.foa-receipt.json
```

Verification rejects altered embedded artifacts, stale fingerprints, alternate acknowledgement sets, noncanonical JSON formatting, invalid UTF-8, symbolic links, and any non-false authority value.

## Output boundary

Receipts are generated evidence and belong beneath the external build/evidence root. They must not be committed under `Installer/`, copied into an installation target, treated as a signature, uploaded, or used as execution authority by this layer.
