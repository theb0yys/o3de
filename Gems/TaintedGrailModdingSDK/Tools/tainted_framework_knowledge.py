#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#

"""Generate and verify the canonical Tainted Framework knowledge pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


class TaintedFrameworkKnowledgeGenerationError(RuntimeError):
    pass


UPSTREAM_REPOSITORY = "theb0yys/Tainted-Grail-The-Fall-of-Avalon-mods"
UPSTREAM_COMMIT = "d7e740e7f167b73152b53409e483dab07d80d048"
UPSTREAM_BRANCH = "main"
FRAMEWORK_VERSION = "0.1.33"
CAPTURED_AT_UTC = "2026-07-21T16:58:00Z"


SOURCE_BINDINGS = (
    (
        "mods/tainted-framework/README.md",
        "de3763a50023f467a82370f3c8bcb56f48a7ce65",
    ),
    (
        "mods/tainted-framework/docs/api-surfaces.md",
        "d08eaa8245de2931bc1f68ecc865a6dc8a70f90f",
    ),
    (
        "mods/tainted-framework/docs/compatibility.md",
        "b6cbd59b46cca19a4b085fea66bd9e416e19d279",
    ),
    (
        "mods/tainted-framework/release/manifest.md",
        "55ad7e964c83c5ac17d582bf11d6e50e6adb2a8b",
    ),
    (
        "mods/tainted-framework/src/Tainted.Core/Plugins/"
        "TaintedScaffoldPluginCatalogFactory.cs",
        "8170dbd1f99727db44e89ea36b9b1df278df010d",
    ),
    (
        "mods/tainted-framework/src/Tainted.Host.IL2CPP/Plugin.cs",
        "b34239da98387261bdda56cc02c590c710fc4b22",
    ),
    (
        "mods/tainted-framework/src/Tainted.Host.Mono/Plugin.cs",
        "f73491e1f6766ff5d328f686ea339c24f1548151",
    ),
)


COMPONENTS = (
    ("tainted.abstractions", "portable_authoring_contract", "mods/tainted-framework/src/Tainted.Abstractions"),
    ("tainted.contracts", "portable_authoring_contract", "mods/tainted-framework/src/Tainted.Contracts"),
    ("tainted.core", "editor_utility_candidate", "mods/tainted-framework/src/Tainted.Core"),
    ("tainted.plugin-catalog", "portable_fixture", "mods/tainted-framework/src/Tainted.Core/Plugins"),
    ("tainted.configuration", "portable_authoring_contract", "mods/tainted-framework/src/Tainted.Abstractions/Configuration"),
    ("tainted.diagnostics", "portable_fixture", "mods/tainted-framework/src/Tainted.Abstractions/Reporting"),
    ("tainted.host.mono", "mono_runtime_only", "mods/tainted-framework/src/Tainted.Host.Mono"),
    ("tainted.host.il2cpp", "il2cpp_runtime_only", "mods/tainted-framework/src/Tainted.Host.IL2CPP"),
    ("tainted.runtime-consumer", "game_linked", "mods/Tainted-Diagnostic Tool"),
    ("tainted.gates", "documentation_evidence", "mods/tainted-framework/docs/gates"),
    ("tainted.release", "documentation_evidence", "mods/tainted-framework/release"),
    ("tainted.runtime-bootstrap", "prohibited_in_editor", "mods/tainted-framework/src/Tainted.Host.*"),
    ("tainted.editor-services", "deferred", "mods/tainted-framework/src/Tainted.Core"),
)


API_SURFACES = (
    ("runtime-report", "candidate", "mods/Tainted-Diagnostic Tool", True),
    ("runtime-fingerprint", "candidate", "disabled", False),
    ("runtime-readiness", "candidate", "disabled", False),
    ("runtime-compatibility", "candidate", "disabled", False),
    ("host-safety", "candidate", "disabled", False),
    ("contract-manifest", "candidate", "disabled", False),
    ("plugin-registration", "candidate", "disabled", False),
    ("service-registry", "candidate", "disabled", False),
    ("service-activation", "candidate", "disabled", False),
    ("report-bundle", "candidate", "disabled", False),
    ("report-export", "blocked", "disabled", False),
)


CONFIGURATION_KEYS = (
    "General.Enabled",
    "Safety.DryRunOnly",
    "Safety.ReportOnlyMode",
)

DIAGNOSTIC_VOCABULARY = (
    "contract-manifest",
    "host-safety",
    "plugin-registration",
    "runtime-compatibility",
    "runtime-fingerprint",
    "runtime-readiness",
    "runtime-report",
    "service-activation",
    "service-registry",
)

CAPABILITIES = (
    "read_active_profile",
    "query_catalog",
    "submit_candidate_evidence",
)


EXPECTED_FILES = {
    "component-inventory.json",
    "golden/fixtures.json",
    "knowledge.json",
    "manifest.json",
    "upstream-intake.json",
}


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def build_documents() -> dict[str, bytes]:
    intake = {
        "schema_version": 1,
        "repository": UPSTREAM_REPOSITORY,
        "commit": UPSTREAM_COMMIT,
        "branch": UPSTREAM_BRANCH,
        "framework_id": "framework.tainted",
        "framework_version": FRAMEWORK_VERSION,
        "plugin_guid": "kane.tgfoa.tainted-framework",
        "captured_at_utc": CAPTURED_AT_UTC,
        "license_expression": "NOASSERTION",
        "license_status": "unverified_no_repository_license_file_found",
        "sources": [
            {
                "path": path,
                "fingerprint_kind": "git_blob_sha1",
                "fingerprint": fingerprint,
            }
            for path, fingerprint in SOURCE_BINDINGS
        ],
    }
    inventory = {
        "schema_version": 1,
        "components": [
            {"id": identity, "classification": classification, "path": path}
            for identity, classification, path in COMPONENTS
        ],
    }
    knowledge = {
        "schema_version": 1,
        "framework": {
            "id": "framework.tainted",
            "version": FRAMEWORK_VERSION,
            "plugin_guid": "kane.tgfoa.tainted-framework",
        },
        "compatibility": [
            {
                "version": FRAMEWORK_VERSION,
                "game_version": "1.23.401",
                "branch": "Mono",
                "runtime": "Mono",
                "bepinex": "5.4.23.3",
                "status": "live_load_validated",
                "evidence": "mods/tainted-framework/release/manifest.md",
            },
            {
                "version": FRAMEWORK_VERSION,
                "game_version": "unknown",
                "branch": "IL2CPP",
                "runtime": "IL2CPP",
                "bepinex": "6",
                "status": "blocked",
                "evidence": "mods/tainted-framework/release/manifest.md",
            },
            {
                "version": FRAMEWORK_VERSION,
                "game_version": "n/a",
                "branch": "Shared",
                "runtime": "none",
                "bepinex": "none",
                "status": "contracts_only",
                "evidence": "mods/tainted-framework/README.md",
            },
        ],
        "api_surfaces": [
            {
                "id": identity,
                "status": status,
                "consumer": consumer,
                "consumer_ready": consumer_ready,
            }
            for identity, status, consumer, consumer_ready in API_SURFACES
        ],
        "capabilities": list(CAPABILITIES),
        "service_identities": ["extension.tainted-framework", "framework.tainted"],
        "plugin_identities": ["kane.tgfoa.tainted-framework"],
        "configuration_keys": list(CONFIGURATION_KEYS),
        "diagnostic_vocabulary": list(DIAGNOSTIC_VOCABULARY),
        "known_limitations": [
            "IL2CPP host support is blocked in the pinned upstream release.",
            "Only runtime-report diagnostics is consumer-ready, and only for the named Mono consumer.",
            "No public release archive is asserted by the pinned upstream manifest.",
            "Upstream licence remains NOASSERTION pending provenance review.",
            "Runtime host code is prohibited from the O3DE Editor build graph.",
        ],
    }
    fixtures = {
        "schema_version": 1,
        "plugin_catalog": [
            {
                "plugin_id": "kane.tgfoa.tainted-framework",
                "version": FRAMEWORK_VERSION,
                "order": 0,
            }
        ],
        "duplicate_registration": {
            "plugin_id": "kane.tgfoa.tainted-framework",
            "expected": "rejected",
        },
        "capabilities": {
            "known": list(CAPABILITIES),
            "unknown": "rejected",
        },
        "branch_compatibility": {
            "Mono": "supported_exact_1.23.401",
            "IL2CPP": "blocked",
            "cross_branch_binary": "disabled",
        },
        "configuration": [
            ["General.Enabled", "true"],
            ["Safety.DryRunOnly", "true"],
            ["Safety.ReportOnlyMode", "true"],
        ],
        "diagnostics": list(DIAGNOSTIC_VOCABULARY),
        "future_schema": {"schema_version": 2, "expected": "rejected"},
    }

    documents = {
        "upstream-intake.json": canonical_bytes(intake),
        "component-inventory.json": canonical_bytes(inventory),
        "knowledge.json": canonical_bytes(knowledge),
        "golden/fixtures.json": canonical_bytes(fixtures),
    }
    manifest = {
        "schema_version": 1,
        "files": [
            {
                "path": path,
                "sha256": hashlib.sha256(content).hexdigest(),
                "bytes": len(content),
            }
            for path, content in sorted(documents.items())
        ],
    }
    documents["manifest.json"] = canonical_bytes(manifest)
    return documents


def verify(output: Path) -> None:
    documents = build_documents()
    actual_files = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file()
    }
    if actual_files != EXPECTED_FILES:
        raise TaintedFrameworkKnowledgeGenerationError(
            f"Knowledge file set mismatch: expected {sorted(EXPECTED_FILES)}, "
            f"found {sorted(actual_files)}"
        )
    for relative, expected in documents.items():
        path = output / relative
        actual = path.read_bytes()
        if actual != expected:
            raise TaintedFrameworkKnowledgeGenerationError(
                f"Knowledge bytes drifted for {relative}"
            )


def generate(output: Path, replace: bool) -> None:
    if output.exists():
        if not replace:
            raise TaintedFrameworkKnowledgeGenerationError(
                f"Output already exists: {output}"
            )
        verify(output)
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for relative, content in build_documents().items():
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    verify(output)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("generate", "verify"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--output", type=Path, required=True)
        if command == "generate":
            subparser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.command == "generate":
            generate(arguments.output.resolve(), arguments.replace)
        else:
            verify(arguments.output.resolve())
    except (OSError, TaintedFrameworkKnowledgeGenerationError) as exc:
        print(f"Tainted Framework knowledge {arguments.command} failed: {exc}", file=sys.stderr)
        return 1
    print(f"Tainted Framework knowledge {arguments.command} passed: {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
