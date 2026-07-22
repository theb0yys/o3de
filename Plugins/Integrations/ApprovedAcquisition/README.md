# Approved local and pinned-GitHub acquisition

`ApprovedAcquisition` is an optional editor-only integration package for acquiring only the exact framework knowledge and project-owned fallback assets listed in `approved-sources.json`.

## Approved packages

- `tainted-framework-knowledge` — the canonical Tainted Framework `0.1.33` knowledge, inventory, golden fixtures and provenance records already reviewed in FOA-SDK.
- `tainted-interface-fallback-assets` — three small FOA-SDK-owned SVG fallback classes used by the semantic UI catalog.

The source set is pinned to repository `theb0yys/FOA-SDK` at exact commit `b6975dde94a04c948bb05705fe2d36b3f38cd82e`. The branch name in the manifest is descriptive only and is never used as retrieval authority.

## Inspect and plan

```powershell
python Plugins/Integrations/ApprovedAcquisition/Tools/approved_acquisition.py list
python Plugins/Integrations/ApprovedAcquisition/Tools/approved_acquisition.py plan `
  --provider pinned-github
```

Plans are canonical JSON and receive a deterministic SHA-256 `plan_id`. A package can be selected by repeating `--package <id>`.

## Local route

The local provider reads an already available source checkout. It refuses symlinked roots and symlinked path components, checks containment, and verifies the exact approved byte count and SHA-256 before publishing a bundle.

```powershell
python Plugins/Integrations/ApprovedAcquisition/Tools/approved_acquisition.py acquire `
  --provider local `
  --source-root C:\src\FOA-SDK `
  --output C:\foa-build\acquired\framework
```

## Pinned-GitHub route

The pinned-GitHub provider requests only `raw.githubusercontent.com` URLs containing the exact forty-character commit. It refuses redirects, branch and tag resolution, credentials, and unlisted paths.

```powershell
python Plugins/Integrations/ApprovedAcquisition/Tools/approved_acquisition.py acquire `
  --provider pinned-github `
  --output C:\foa-build\acquired\framework
```

Network retrieval is intentionally not part of the default repository validation gate. The deterministic plan and injected-byte provider tests cover the URL and verification contract without making CI or local validation dependent on GitHub availability.

## Verify

```powershell
python Plugins/Integrations/ApprovedAcquisition/Tools/approved_acquisition.py verify `
  --bundle C:\foa-build\acquired\framework
```

The bundle contains `ACQUISITION_PLAN.json`, `ACQUISITION_RECEIPT.json`, and only the selected reviewed files. Verification recomputes the plan and receipt, rejects missing or extra paths and symlinks, and rehashes every payload.

## Boundaries

- Output must be outside the FOA-SDK checkout and must not already exist.
- Publication is atomic through a sibling temporary directory; overwrite is prohibited.
- No local source path is retained in the receipt.
- Acquisition does not create or promote candidate evidence.
- It grants no catalog mutation, runtime execution, deployment, signing, upload, publication, game launch, or save authority.
- No upstream Tainted Interface PNG payload is approved or acquired.
- Merlin's Workshop is a later optional provider package.
- Mono and IL2CPP remain separate later runtime-adapter packages.
