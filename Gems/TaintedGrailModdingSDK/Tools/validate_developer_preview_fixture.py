#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#

"""Validate the Developer Preview 0 deterministic fixture contract."""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def require_file(path: Path) -> str:
    if not path.is_file():
        fail(f"Required Developer Preview fixture file is missing: {path}")
    return path.read_text(encoding="utf-8")


def require_fragments(path: Path, fragments: tuple[str, ...]) -> str:
    text = require_file(path)
    for fragment in fragments:
        if fragment not in text:
            fail(f"Missing required fragment {fragment!r} in {path}")
    return text


def load_fixture_module(path: Path):
    spec = importlib.util.spec_from_file_location("tg_developer_preview_fixture_contract", path)
    if not spec or not spec.loader:
        fail(f"Unable to load Developer Preview fixture module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    gem_root = repo_root / "Gems/TaintedGrailModdingSDK"
    tools_root = gem_root / "Tools"
    fixture_root = gem_root / "Preview"
    script_path = tools_root / "developer_preview_fixture.py"
    tests_path = tools_root / "tests/test_developer_preview_fixture.py"
    fixture_readme_path = fixture_root / "README.md"
    guide_path = repo_root / "docs/tainted-grail-sdk/DEVELOPER_PREVIEW_0.md"
    workflow_path = repo_root / ".github/workflows/tainted-grail-sdk-foundation.yml"

    temporary_root: Path | None = None
    try:
        script = require_fragments(
            script_path,
            (
                'FIXTURE_ID = "preview.developer-preview-0"',
                'MANIFEST_NAME = "preview-fixture.manifest.json"',
                'PACK_ID = "preview.developer-preview-0"',
                'SUBJECT_UNRESOLVED = "subject:preview:learn-source:unresolved"',
                "def canonical_json_bytes",
                "def sha256_bytes",
                "def normalize_relative_path",
                "def ensure_no_symlinks",
                "def atomic_write",
                "def assert_public_synthetic_content",
                "def template_documents",
                "def build_manifest",
                "def generate_fixture",
                "def verify_fixture",
                "Source fingerprint does not match source input",
                "Catalog workspace binding mismatch",
                "Synthetic record claims a native identity",
                "Relationship requires exactly one target",
                "Unresolved relationship must preserve its missing reference",
                "RuntimeActionsEnabled",
                "allowed_record_ids",
                "forbidden_record_ids",
                "blocked_record_ids",
                "stale_record_ids",
                "unresolved_relationship_ids",
                "--replace",
                "Replace only an existing fixture that first passes full verification",
            ),
        )
        for forbidden in (
            "requests.",
            "urllib.request",
            "subprocess.",
            "shell=True",
            "os.system(",
            "FoA.exe",
            "BepInEx/",
            "HarmonyLib",
            "WriteProcessMemory",
        ):
            if forbidden in script:
                fail(f"Fixture generator contains prohibited dependency or runtime behavior: {forbidden}")

        require_fragments(
            tests_path,
            (
                "test_generation_is_byte_for_byte_deterministic",
                "test_generated_fixture_passes_full_verification",
                "test_manifest_entries_are_sorted_and_hash_every_payload",
                "test_generation_refuses_unrelated_non_empty_directory",
                "test_replace_requires_existing_fixture_to_verify_first",
                "test_verification_rejects_payload_tampering",
                "test_verification_rejects_unexpected_files",
                "test_manifest_rejects_path_traversal",
                "test_verification_rejects_absolute_or_private_paths",
                "test_source_fingerprint_must_match_source_input",
                "test_catalog_binding_must_match_workspace_profile",
                "test_unresolved_relationship_preserves_subject_and_missing_ref",
                "test_fixture_contains_allowed_forbidden_blocked_stale_and_unresolved_states",
                "test_all_identities_use_reserved_preview_namespace",
            ),
        )

        require_fragments(
            fixture_readme_path,
            (
                "project-owned synthetic data",
                "preview.*",
                "preview-fixture.manifest.json",
                "SHA-256",
                "does not contain proprietary game data",
                "developer_preview_fixture.py generate",
                "developer_preview_fixture.py verify",
                "--output",
                "refuses to overwrite",
            ),
        )

        require_fragments(
            guide_path,
            (
                "Generate the deterministic synthetic fixture",
                "developer_preview_fixture.py generate",
                "developer_preview_fixture.py verify",
                "preview-fixture.manifest.json",
                "byte-for-byte deterministic",
                "project-owned synthetic data",
                "does not prove Editor load/save/reopen behavior",
            ),
        )

        require_fragments(
            workflow_path,
            (
                "Test Developer Preview 0 fixture",
                "Validate Developer Preview 0 fixture contract",
                "Generate Developer Preview 0 fixture",
                "Verify Developer Preview 0 fixture",
                "test_developer_preview_fixture.py",
                "validate_developer_preview_fixture.py",
                "developer_preview_fixture.py generate",
                "developer_preview_fixture.py verify",
            ),
        )

        module = load_fixture_module(script_path)
        temporary_root = Path(tempfile.mkdtemp(prefix="tg-preview-fixture-contract-"))
        output = temporary_root / "fixture"
        manifest = module.generate_fixture(output)
        verified = module.verify_fixture(output)
        if manifest != verified:
            fail("Generated and verified fixture manifests differ")
        if len(manifest.get("files", [])) != 6:
            fail("Developer Preview fixture manifest must hash exactly six payload files")
    except (OSError, RuntimeError) as exc:
        print(f"Developer Preview 0 fixture contract validation failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if temporary_root:
            shutil.rmtree(temporary_root, ignore_errors=True)

    print("Developer Preview 0 deterministic fixture, manifest, and verification contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
