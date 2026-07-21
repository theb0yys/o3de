#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
"""Committed templates, manifest, workspace, and pack checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from population_preview_fixture_common import (
    BRANCH,
    EXPECTED_FILE_PATHS,
    EXPECTED_STATE,
    FIXTURE_ID,
    FIXTURE_SCHEMA_VERSION,
    GAME_VERSION,
    MANIFEST_NAME,
    PACK_ID,
    PRIVATE_PATH_PATTERN,
    PROFILE_ID,
    RUNTIME_TARGET,
    STABLE_ID_PATTERN,
    WORKSPACE_ID,
    assert_public_synthetic_content,
    canonical_json_bytes,
    ensure_no_symlinks,
    load_json,
    normalize_relative_path,
    require,
    require_list,
    require_string,
    sha256_bytes,
    template_root_from_script,
)

def template_documents(
    template_root: Path | None = None,
) -> dict[str, dict[str, Any]]:
    root = (template_root or template_root_from_script()).resolve(strict=False)
    require(root.is_dir(), f"Population fixture template does not exist: {root}")
    ensure_no_symlinks(root)
    actual = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    )
    require(
        actual == sorted(EXPECTED_FILE_PATHS),
        "Population fixture template file set is incomplete or unexpected",
    )
    documents: dict[str, dict[str, Any]] = {}
    for relative_path in EXPECTED_FILE_PATHS:
        path = root / relative_path
        document = load_json(path)
        require(
            path.read_bytes() == canonical_json_bytes(document),
            f"Population template is not canonical JSON: {relative_path}",
        )
        assert_public_synthetic_content(
            document,
            label=f"population-template:{relative_path}",
        )
        documents[relative_path] = document
    return documents


def build_manifest(
    documents: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    files = []
    for relative_path in sorted(documents):
        payload = canonical_json_bytes(documents[relative_path])
        files.append(
            {
                "path": relative_path,
                "sha256": sha256_bytes(payload),
                "size_bytes": len(payload),
            }
        )
    return {
        "expected": EXPECTED_STATE,
        "fixture_id": FIXTURE_ID,
        "files": files,
        "generator": (
            "Gems/TaintedGrailModdingSDK/Tools/"
            "population_preview_fixture.py"
        ),
        "schema_version": FIXTURE_SCHEMA_VERSION,
    }


def manifest_paths(manifest: dict[str, Any]) -> list[str]:
    require(
        manifest.get("schema_version") == FIXTURE_SCHEMA_VERSION,
        "Unsupported population fixture manifest schema",
    )
    require(manifest.get("fixture_id") == FIXTURE_ID, "Unexpected fixture ID")
    require(
        manifest.get("expected") == EXPECTED_STATE,
        "Population fixture expected-state contract mismatch",
    )
    paths = []
    for entry in require_list(manifest.get("files"), "manifest.files"):
        require(
            isinstance(entry, dict),
            "Each manifest file entry must be an object",
        )
        paths.append(normalize_relative_path(entry.get("path")))
    require(paths == sorted(paths), "Manifest files must be sorted")
    require(len(paths) == len(set(paths)), "Manifest paths must be unique")
    require(
        paths == sorted(EXPECTED_FILE_PATHS),
        "Manifest population file set is incomplete or unexpected",
    )
    return paths


def validate_workspace(workspace: dict[str, Any]) -> dict[str, Any]:
    require(workspace.get("SchemaVersion") == 1, "Unsupported workspace schema")
    require(workspace.get("WorkspaceId") == WORKSPACE_ID, "Workspace ID mismatch")
    require(workspace.get("RootPath") == ".", "Workspace root must remain relative")
    require(
        workspace.get("ActiveGameProfileId") == PROFILE_ID,
        "Active profile mismatch",
    )
    profiles = require_list(
        workspace.get("GameProfiles"),
        "workspace.GameProfiles",
    )
    require(len(profiles) == 1, "Fixture must contain exactly one game profile")
    profile = profiles[0]
    require(isinstance(profile, dict), "Workspace profile must be an object")
    require(profile.get("ProfileId") == PROFILE_ID, "Profile ID mismatch")
    require(profile.get("GameVersion") == GAME_VERSION, "Profile version mismatch")
    require(profile.get("Branch") == BRANCH, "Profile branch mismatch")
    require(
        profile.get("RuntimeTarget") == RUNTIME_TARGET,
        "Profile runtime target mismatch",
    )
    for field in (
        "InstallPath",
        "ManagedAssembliesPath",
        "PluginPath",
        "DiagnosticsPath",
        "ExtractedDataPath",
    ):
        value = require_string(profile.get(field), f"profile.{field}")
        require(
            not PRIVATE_PATH_PATTERN.search(value),
            f"profile.{field} must be portable",
        )
    return profile


def validate_pack(pack: dict[str, Any]) -> None:
    require(pack.get("SchemaVersion") == 1, "Unsupported pack schema")
    require(pack.get("PackId") == PACK_ID, "Pack ID mismatch")
    require(pack.get("OwnerId") == "preview.population", "Pack owner mismatch")
    require(pack.get("TargetGameVersion") == GAME_VERSION, "Pack version mismatch")
    require(pack.get("TargetBranch") == BRANCH, "Pack branch mismatch")
    require(
        pack.get("RuntimeActionsEnabled") is False,
        "Population preview pack runtime actions must remain disabled",
    )
    require(
        STABLE_ID_PATTERN.fullmatch(PACK_ID) is not None,
        "Invalid pack identity",
    )


