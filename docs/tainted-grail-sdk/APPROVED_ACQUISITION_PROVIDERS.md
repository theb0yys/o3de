# Approved local and pinned-GitHub acquisition providers

## Status

Implemented as the optional `Plugins/Integrations/ApprovedAcquisition` package. This is an editor-side acquisition boundary, not a runtime adapter or deployment system.

## Purpose

The package creates deterministic, independently verifiable bundles containing only reviewed Tainted Framework knowledge and FOA-SDK-owned Tainted Interface fallback assets. It provides two routes:

- **local** — read exact approved files from an existing checkout after canonical containment and symlink checks;
- **pinned-GitHub** — fetch exact approved files from `raw.githubusercontent.com` at one immutable forty-character commit.

The current source authority is:

```text
repository: theb0yys/FOA-SDK
commit: b6975dde94a04c948bb05705fe2d36b3f38cd82e
```

The descriptive branch name is not retrieval authority. No branch, tag, release, latest-version lookup, redirect, or GitHub API response can replace the exact commit.

## Approved content

### Tainted Framework knowledge

The reviewed `0.1.33` canonical knowledge pack:

- upstream intake and exact source bindings;
- component inventory and classifications;
- compatibility and API-surface knowledge;
- deterministic golden fixtures;
- knowledge manifest.

### Tainted Interface fallback assets

Three small FOA-SDK-owned SVG fallback classes:

- frame/content;
- action/confirmation;
- input device.

These assets are generic project-owned fallbacks and do not claim upstream visual parity.

**NO upstream PNG is approved by this provider.** The upstream `Assets/User Interface` payload remains excluded because its licence and redistribution authority are not established. Unlisted binaries, Unity metadata, raw source packs, credentials, runtime hosts and proprietary game files are also excluded.

## Deterministic plan

`plan` produces canonical JSON containing:

- provider and route identity;
- exact repository and commit;
- sorted package IDs;
- sorted approved source and bundle paths;
- media types, byte counts, licences and SHA-256 values;
- aggregate counts and bytes;
- permanently false authority fields;
- a deterministic SHA-256 `plan_id`.

The committed `pinned-github-all.plan.json` is the golden all-package plan. Any manifest, ordering, fingerprint or source drift invalidates it.

## Local provider

The local provider requires an explicit source root. It:

- refuses a symlinked root;
- checks every approved path component with `lstat`;
- refuses symlinks, missing files and non-regular files;
- resolves the final path beneath the canonical source root;
- reads no more than the expected byte count plus one byte;
- requires exact byte count and SHA-256.

The local source path is transient and is not written into the receipt.

## Pinned-GitHub provider

The pinned-GitHub provider:

- constructs only HTTPS `raw.githubusercontent.com` URLs;
- includes the exact commit in every URL;
- refuses redirects;
- validates the final scheme and host;
- does not support credentials or tokens;
- reads only an approved path;
- enforces exact content length when supplied;
- enforces the same byte-count and SHA-256 checks as the local route.

The default repository gate does not require live network access. It verifies the deterministic URL contract and payload validation through injected-byte tests. A real network acquisition remains an explicit operator action.

## Atomic external output

Acquisition output must be **outside the FOA-SDK checkout**. Existing output is never overwritten.

Files are written exclusively into a sibling temporary directory, flushed and synchronized, then the completed directory is published with one atomic rename. Any failure removes the temporary directory and leaves no candidate bundle at the requested output path.

Each bundle contains:

```text
ACQUISITION_PLAN.json
ACQUISITION_RECEIPT.json
<approved payload paths>
```

`verify` recomputes plan and receipt fingerprints, checks the exact path set, refuses symlinks and rehashes every file.

## Governance and authority

Acquisition does not create, promote or approve **candidate evidence**. A later caller may separately submit evidence only through the governed ExtensionAPI lane and its exact capability, profile, source and chronology checks.

The provider permanently grants no:

- mutable catalog or source-registry access;
- evidence promotion;
- runtime execution;
- deployment or game installation;
- signing, upload or publication;
- game launch or save mutation.

## Deferred providers and adapters

- **Merlin** acquisition remains a separate optional integration package with its own official-tool provenance and process boundary.
- **Mono** remains a separate runtime-adapter package.
- **IL2CPP** remains a separate runtime-adapter package.

Neither runtime adapter is imported, built, selected, deployed or executed by this acquisition unit.

## Validation

Repository validation includes:

- provider unit tests for both routes without mandatory network access;
- local atomic acquisition and full bundle verification;
- symlink, tamper, overwrite, unknown-package and repository-output refusal;
- exact production source and seed fingerprints;
- a deterministic golden plan;
- mutation tests for authority escalation, source tampering, unapproved PNG inclusion, loss of atomic publication, stale plans and gate removal;
- the non-network local acquisition fixture in `run_local_validation.py`.

O3DE compilation, CTest and Windows UI evidence are separate host gates and are not implied by successful acquisition-provider tests.
