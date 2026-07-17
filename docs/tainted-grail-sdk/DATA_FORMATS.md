# Data Formats

## General rules

TG SDK durable documents are UTF-8 JSON produced through O3DE serialization.

Rules:

- top-level durable documents use an explicit schema version;
- field names are case-sensitive;
- stable IDs and exact native references are not display labels;
- unknown schema versions are rejected unless a migration exists;
- secrets and credentials are prohibited;
- private absolute paths should not be distributed publicly;
- runtime permission is never implied by the existence of a document;
- examples must not include copyrighted game content.

The examples below are illustrative. O3DE serialization may omit fields that equal default values.

## Workspace document

Suffix:

```text
*.tgworkspace.json
```

Purpose: editor-owned workspace and exact game-profile configuration.

Logical structure:

```json
{
  "WorkspaceId": "owner.workspace",
  "DisplayName": "My TG Workspace",
  "RootPath": "/authoring/MyWorkspace",
  "OutputPath": "/authoring/MyWorkspace/Build",
  "StagingPath": "/authoring/MyWorkspace/Staging",
  "DeploymentPath": "/authoring/MyWorkspace/Deployment",
  "ActiveGameProfileId": "foa.mono.current",
  "GameProfiles": [
    {
      "ProfileId": "foa.mono.current",
      "DisplayName": "FoA Mono Current",
      "InstallPath": "/games/FoA",
      "GameVersion": "exact-version",
      "Branch": "mono",
      "RuntimeTarget": "Mono",
      "UnityVersion": "exact-unity-version",
      "BepInExVersion": "exact-bepinex-version",
      "ManagedAssembliesPath": "/games/FoA/Tainted Grail_Data/Managed",
      "PluginPath": "/games/FoA/BepInEx/plugins",
      "DiagnosticsPath": "/authoring/MyWorkspace/Diagnostics",
      "ExtractedDataPath": "/authoring/MyWorkspace/Extracted",
      "DlcScopes": ["base-game"]
    }
  ]
}
```

### Required configured profile fields

- `ProfileId`
- `InstallPath`
- `GameVersion`
- `Branch`
- `RuntimeTarget`
- `ManagedAssembliesPath`

`RuntimeTarget` must be `Mono` or `IL2CPP`. Mono profiles also require BepInEx version and plugin path for build/deployment planning.

## Pack manifest

Suffix:

```text
*.tgpack.json
```

Required location: inside the active workspace root.

Logical structure:

```json
{
  "SchemaVersion": 1,
  "PackId": "owner.pack-name",
  "DisplayName": "Pack Name",
  "OwnerId": "owner",
  "Version": "0.1.0",
  "TargetGameVersion": "exact-version",
  "TargetBranch": "mono",
  "CompatibleGameVersions": [],
  "RequiredCoreVersion": "0.1.0",
  "RequiredAdapterVersion": "0.1.0",
  "SaveImpact": "unknown",
  "DlcScopes": ["base-game"],
  "Dependencies": [],
  "RequiredMods": [],
  "Incompatibilities": [],
  "ContentDefinitionPaths": ["Content/items.json"],
  "AssetPaths": [],
  "LocalisationPaths": [],
  "BuildConfiguration": "Profile",
  "ReleaseChannel": "development",
  "RuntimeActionsEnabled": false
}
```

### Identity rules

- `PackId` is lowercase and namespaced.
- `OwnerId` is explicit.
- `Version` uses semantic versioning.
- `RuntimeActionsEnabled` must be `false` in editor-owned documents.

### Save-impact values

- `none`
- `compatible`
- `migration`
- `destructive`
- `unknown`

## Source document

Path:

```text
Sources/<source-id>/source.tgsource.json
```

Purpose: immutable description of an imported artifact and its provenance.

Logical structure:

```json
{
  "SchemaVersion": 1,
  "Source": {
    "SourceId": "source.profile.fingerprint",
    "Title": "Template diagnostic export",
    "SourceKind": "template-diagnostics",
    "Locator": "/path/to/input.json",
    "Fingerprint": "sha256:...",
    "ProfileId": "foa.mono.current",
    "GameVersion": "exact-version",
    "Branch": "mono",
    "RuntimeTarget": "Mono",
    "ToolName": "Diagnostic Tool",
    "ToolVersion": "1.0.0",
    "ImporterId": "tg.structured-json",
    "ImporterVersion": "1.0.0",
    "CapturedAt": "2026-07-17T10:00:00.000Z",
    "ImportedAt": "2026-07-17T11:00:00.000Z",
    "Limitations": "Read-only capture",
    "MediaType": "application/json",
    "ByteSize": 1234,
    "ImportStatus": "imported"
  },
  "Issues": []
}
```

### Fingerprint rule

`Fingerprint` uses lowercase hexadecimal SHA-256 with the prefix:

```text
sha256:<64-hex-digits>
```

A profile/fingerprint pair cannot be registered twice.

### Import status

Current values:

- `imported`
- `warning`
- `error`

Status describes import processing, not factual validity or runtime permission.

## Evidence document

Path:

```text
Sources/<source-id>/evidence.tgevidence.json
```

Purpose: evidence extracted from one source plus schema/import issues.

Logical structure:

```json
{
  "SchemaVersion": 1,
  "SourceId": "source.profile.fingerprint",
  "SourceFingerprint": "sha256:...",
  "ProfileId": "foa.mono.current",
  "GameVersion": "exact-version",
  "Branch": "mono",
  "Evidence": [
    {
      "EvidenceId": "evidence.fingerprint.1",
      "SourceId": "source.profile.fingerprint",
      "SourceFingerprint": "sha256:...",
      "ProfileId": "foa.mono.current",
      "GameVersion": "exact-version",
      "Branch": "mono",
      "SubjectRef": "subject:example",
      "Claim": "Evidence-backed statement",
      "EvidenceKind": "runtime-observation",
      "Confidence": "unrated",
      "Locator": "/path/to/input.json",
      "RecordPath": "$.evidence[0]",
      "ExtractedAt": "2026-07-17T11:00:00.000Z"
    }
  ],
  "Issues": []
}
```

The evidence document's source ID, fingerprint, profile, version, and branch must match the source document and each child evidence record.

## Import issue

Logical structure:

```json
{
  "IssueId": "issue.source-id.1",
  "Severity": "error",
  "Code": "schema.evidence-required-fields",
  "Message": "Evidence entries require subject_ref and claim.",
  "Locator": "/path/to/input.json",
  "RecordPath": "$.evidence[0]",
  "Line": 0
}
```

Severity values currently used:

- `warning`
- `error`

Issue codes are stable machine-readable identifiers. Message text may improve without a schema change.

## Structured JSON intake schema

Accepted shapes:

### Root array

```json
[
  {
    "subject_ref": "subject:example",
    "claim": "Statement"
  }
]
```

### Evidence property

```json
{
  "evidence": [
    {
      "subject_ref": "subject:example",
      "claim": "Statement"
    }
  ]
}
```

### Single evidence object

```json
{
  "subject_ref": "subject:example",
  "claim": "Statement"
}
```

Required:

- `subject_ref`
- `claim`

Optional:

- `evidence_id`
- `kind`
- `confidence`
- `locator`

## Structured CSV intake schema

Required header columns:

```text
subject_ref,claim
```

Accepted aliases:

- `subject` for `subject_ref`
- `id` for `evidence_id`
- `evidence_kind` for `kind`

Optional columns:

- `evidence_id`
- `kind`
- `confidence`
- `locator`

CSV supports quoted values and doubled quotes. It is intended for evidence registers, not arbitrary spreadsheet semantics.

## Generic artifact intake

Generic intake creates a source document and an evidence document containing a manual-extraction warning. It does not infer evidence from logs, screenshots, dumps, notes, or unknown formats.

## Catalog documents

The canonical catalog format is introduced by the catalog browser milestone. Its contract must include:

- schema version;
- stable record IDs;
- exact refs and identity kind;
- pack ownership for synthetic records;
- evidence links;
- typed relationships;
- maturity, confidence, risk, validation, permissions, and prohibitions;
- conflict, missing-reference, staleness, and supersession data.

The final fields and suffixes must be documented here before catalog persistence is merged.

## Compatibility and migration

### Backward-compatible changes

Examples:

- adding an optional field with a safe default;
- adding a new issue code;
- adding a new importer that does not reinterpret existing documents.

### Breaking changes

Examples:

- changing identity semantics;
- renaming or removing a field;
- changing a field type;
- changing fingerprint scope;
- changing required profile binding;
- merging previously distinct record kinds.

Breaking changes require:

- schema version increment;
- migration tool or explicit unsupported-version error;
- tests using old and new fixtures;
- changelog and user-guide updates;
- release notes and rollback guidance.
