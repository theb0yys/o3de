# Deterministic installer suite/package resolver

`Installer/SuiteWizard/Resolver/` owns the engine-neutral decision layer beneath the future suite wizard UI.

The resolver consumes one reviewed `suite.json`, the reviewed package catalog under `Installer/Packages/`, and an explicit compatibility context. It produces one canonical, dry-run installation plan conforming to `plan.schema.json`.

The wizard may collect user choices and display the resulting plan. It must not reproduce dependency, compatibility, conflict, path, legal, or ordering logic in UI code.

## Resolution contract

The resolver:

- always includes `required` suite entries;
- includes `default` entries unless explicitly excluded;
- includes `optional` entries only when selected directly or through a selected feature;
- expands required package dependencies to a fixed point;
- validates exact package identity and semantic-version constraints;
- rejects missing dependencies, unsupported version-range syntax, dependency cycles, package conflicts, and duplicate package IDs;
- validates platform, architecture, game version, branch, and runtime-target compatibility;
- rejects schema-version drift, malformed reviewed provenance, invalid install scopes, incomplete host compatibility, `planned`, `blocked`, unreviewed, authority-granting, or redistribution-blocked packages;
- rejects Windows path traversal, device names, case aliases, unsafe characters, in-package duplicate destinations, and cross-package destination collisions;
- orders dependencies before dependants using a lexical tie-breaker;
- emits canonical JSON with no timestamps or environment-dependent values;
- binds the plan to exact suite and package manifest SHA-256 values;
- calculates `plan_sha256` over the canonical plan with that field omitted.

The supported dependency range grammar is deliberately small and fail-closed:

```text
*
1.2.3
==1.2.3
>=1.0.0 <2.0.0
>=1.0.0, <2.0.0
```

Caret, tilde, disjunction, implicit floating versions, and implementation-specific package-manager syntax are rejected.

## Source

```text
Installer/SuiteWizard/Resolver/
├── README.md
├── plan.schema.json
└── Source/
    ├── suite_package_resolver.py   public manifest boundary and CLI
    └── _resolver_core.py           internal deterministic graph/plan engine
```

The implementation uses only the Python standard library. It does not acquire files, install packages, modify the game, elevate privileges, launch FoA, sign artifacts, publish releases, mutate saves, alter the catalog, or promote evidence.

## Command line

```powershell
python Installer/SuiteWizard/Resolver/Source/suite_package_resolver.py `
  --installer-root Installer `
  --suite Developer `
  --platform windows `
  --architecture x86_64 `
  --runtime-target editor-only `
  --select foa.ui-framework `
  --feature foa.feature.authoring `
  --output ..\foa-build\installer-plans\developer.plan.json
```

`--select`, `--exclude`, and `--feature` may be repeated. When `--output` is omitted, canonical JSON is written to standard output.

## Wizard boundary

The future wizard must:

1. load available suites and package presentation metadata;
2. submit explicit choices and compatibility context to the resolver;
3. display resolver diagnostics without weakening them;
4. display the exact resolved package order, payload inventory, disk usage, elevation state, legal state, warnings, and plan fingerprint;
5. require a later explicit confirmation against that exact plan fingerprint;
6. hand the accepted plan to a separately reviewed execution layer.

A valid plan is not permission to install. Installation, acquisition, elevation, repair, upgrade, rollback, uninstall, signing, and publication remain separate capability-gated units.

## Tests

Focused tests live in:

```text
Installer/Tests/SuitePackageResolver/
├── test_suite_package_resolver.py
└── test_manifest_contract.py
```

They cover:

- SemVer precedence and supported ranges;
- required/default/optional selection;
- explicit exclusion and feature selection;
- required dependency closure and dependency-first order;
- missing dependencies, version mismatches, conflicts, and cycles;
- compatibility and elevation policy;
- redistribution review and authority prohibition;
- schema-version, provenance, lifecycle and host-compatibility validation;
- duplicate JSON keys and duplicate package identity;
- Windows destination collisions;
- canonical output and stable plan fingerprints.
