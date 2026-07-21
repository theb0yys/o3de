#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
"""Generate and verify the project-owned Actor/Troop Editor population fixture.

The committed templates contain only synthetic preview.* identities and portable
relative paths. Generation writes canonical UTF-8 JSON and an exact SHA-256
manifest. Verification reconstructs the population identity, evidence, composition,
governance, and persistence-facing invariants required by the editor.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

MODULE_ROOT = Path(__file__).resolve().parent
if str(MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT))

from population_preview_fixture_catalog import validate_catalog
from population_preview_fixture_contract import (
    ACTOR_LEADER_ID,
    ACTOR_SCOUT_ID,
    BRANCH,
    CATALOG_PATH,
    EVIDENCE_DOCUMENT_PATH,
    EXPECTED_FILE_PATHS,
    EXPECTED_STATE,
    FIXTURE_ID,
    GAME_VERSION,
    MANIFEST_NAME,
    MEMBER_LEADER_ID,
    MEMBER_SCOUT_ID,
    PACK_ID,
    PACK_PATH,
    PROFILE_ID,
    PopulationFixtureError,
    RELATIONSHIP_LEADER_TEMPLATE_ID,
    RUNTIME_TARGET,
    SOURCE_DOCUMENT_PATH,
    SOURCE_ID,
    SOURCE_INPUT_PATH,
    TEMPLATE_GUARD_ID,
    TROOP_PATROL_ID,
    UNRESOLVED_TEMPLATE_SUBJECT,
    WORKSPACE_ID,
    WORKSPACE_PATH,
    assert_public_synthetic_content,
    atomic_write,
    build_manifest,
    canonical_json_bytes,
    ensure_no_symlinks,
    is_reserved_population_subject,
    load_json,
    manifest_paths,
    normalize_relative_path,
    require,
    require_list,
    sha256_bytes,
    template_documents,
    validate_pack,
    validate_source_and_evidence,
    validate_workspace,
)

def prepare_output_directory(output_dir: Path, *, replace: bool) -> None:
    require(
        not output_dir.is_symlink(),
        f"Population fixture output must not be a symbolic link: {output_dir}",
    )
    if output_dir.exists() and not output_dir.is_dir():
        raise PopulationFixtureError(
            f"Population fixture output is not a directory: {output_dir}"
        )
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        return
    ensure_no_symlinks(output_dir)
    if not any(path.is_file() for path in output_dir.rglob("*")):
        return
    if not replace:
        raise PopulationFixtureError(
            f"Population fixture output is not empty: {output_dir}. "
            "Use --replace only for an existing fixture that passes verification."
        )
    verify_fixture(output_dir)
    shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)


def generate_fixture(
    output_dir: Path,
    *,
    replace: bool = False,
    template_root: Path | None = None,
) -> dict[str, Any]:
    output_dir = output_dir.expanduser().resolve(strict=False)
    prepare_output_directory(output_dir, replace=replace)
    documents = template_documents(template_root)
    for relative_path in sorted(documents):
        atomic_write(
            output_dir / relative_path,
            canonical_json_bytes(documents[relative_path]),
        )
    manifest = build_manifest(documents)
    atomic_write(output_dir / MANIFEST_NAME, canonical_json_bytes(manifest))
    verify_fixture(output_dir, template_root=template_root)
    return manifest


def verify_fixture(
    output_dir: Path,
    *,
    template_root: Path | None = None,
) -> dict[str, Any]:
    root = output_dir.expanduser().resolve(strict=False)
    require(root.is_dir(), f"Population fixture directory does not exist: {root}")
    ensure_no_symlinks(root)
    manifest_path = root / MANIFEST_NAME
    manifest = load_json(manifest_path)
    require(
        manifest_path.read_bytes() == canonical_json_bytes(manifest),
        "Population fixture manifest is not canonical JSON",
    )
    paths = manifest_paths(manifest)
    actual = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    )
    require(
        actual == sorted((*EXPECTED_FILE_PATHS, MANIFEST_NAME)),
        "Population fixture file set is missing or unexpected",
    )
    entries = {
        normalize_relative_path(entry.get("path")): entry
        for entry in require_list(manifest.get("files"), "manifest.files")
    }
    loaded: dict[str, dict[str, Any]] = {}
    for relative_path in paths:
        path = root / relative_path
        payload = path.read_bytes()
        entry = entries[relative_path]
        require(
            entry.get("sha256") == sha256_bytes(payload),
            f"SHA-256 mismatch for population fixture file: {relative_path}",
        )
        require(
            entry.get("size_bytes") == len(payload),
            f"Byte-size mismatch for population fixture file: {relative_path}",
        )
        document = load_json(path)
        require(
            payload == canonical_json_bytes(document),
            f"Population fixture JSON is not canonical: {relative_path}",
        )
        assert_public_synthetic_content(
            document,
            label=f"population-fixture:{relative_path}",
        )
        loaded[relative_path] = document

    validate_workspace(loaded[WORKSPACE_PATH])
    validate_pack(loaded[PACK_PATH])
    evidence_by_id = validate_source_and_evidence(
        root,
        loaded[SOURCE_DOCUMENT_PATH],
        loaded[EVIDENCE_DOCUMENT_PATH],
    )
    validate_catalog(loaded[CATALOG_PATH], evidence_by_id)

    documents = template_documents(template_root)
    expected_manifest = build_manifest(documents)
    require(
        manifest == expected_manifest,
        "Population fixture manifest does not match the deterministic template",
    )
    for relative_path in paths:
        require(
            (root / relative_path).read_bytes()
            == canonical_json_bytes(documents[relative_path]),
            f"Population fixture differs from committed template: {relative_path}",
        )
    return manifest


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or verify the deterministic Actor/Troop population fixture."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate")
    generate.add_argument("--output", required=True, type=Path)
    generate.add_argument(
        "--replace",
        action="store_true",
        help=(
            "Replace only an existing population fixture that first passes "
            "full verification."
        ),
    )
    verify = subparsers.add_parser("verify")
    verify.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    try:
        if arguments.command == "generate":
            manifest = generate_fixture(
                arguments.output,
                replace=arguments.replace,
            )
            print(
                "Generated deterministic Actor/Troop population fixture "
                f"{manifest['fixture_id']}."
            )
        else:
            manifest = verify_fixture(arguments.output)
            print(
                "Verified deterministic Actor/Troop population fixture "
                f"{manifest['fixture_id']}."
            )
    except (OSError, PopulationFixtureError) as exc:
        print(f"Population fixture operation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
