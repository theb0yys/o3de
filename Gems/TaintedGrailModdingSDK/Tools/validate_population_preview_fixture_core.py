#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
"""Focused contract validator for the deterministic Actor/Troop fixture."""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path


class PopulationFixtureContractError(RuntimeError):
    """Raised when the fixture or local-gate integration is incomplete."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PopulationFixtureContractError(message)


def read(path: Path) -> str:
    require(path.is_file(), f"Required population fixture file is missing: {path}")
    return path.read_text(encoding="utf-8")


def require_fragments(text: str, fragments: tuple[str, ...], label: str) -> None:
    missing = [fragment for fragment in fragments if fragment not in text]
    require(not missing, f"{label} is missing required fragments: {missing}")


def reject_fragments(text: str, fragments: tuple[str, ...], label: str) -> None:
    found = [fragment for fragment in fragments if fragment in text]
    require(not found, f"{label} contains forbidden fragments: {found}")


def load_fixture_module(path: Path):
    spec = importlib.util.spec_from_file_location(
        "tg_population_preview_fixture_contract",
        path,
    )
    require(bool(spec and spec.loader), f"Unable to load fixture module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_population_preview_fixture(repo_root: Path) -> None:
    gem_root = repo_root / "Gems/TaintedGrailModdingSDK"
    tools_root = gem_root / "Tools"
    template_root = gem_root / "Preview/PopulationTemplate"
    script_path = tools_root / "population_preview_fixture.py"
    runner_path = tools_root / "run_local_validation.py"
    tests_path = tools_root / "tests/test_population_preview_fixture.py"

    module_names = {
        "population_preview_fixture.py",
        "population_preview_fixture_catalog.py",
        "population_preview_fixture_catalog_history.py",
        "population_preview_fixture_catalog_records.py",
        "population_preview_fixture_catalog_troops.py",
        "population_preview_fixture_common.py",
        "population_preview_fixture_contract.py",
        "population_preview_fixture_evidence.py",
        "population_preview_fixture_templates.py",
    }
    module_paths = sorted(tools_root.glob("population_preview_fixture*.py"))
    require(
        {path.name for path in module_paths} == module_names,
        "Population fixture source module set is incomplete or unexpected.",
    )
    sources = "\n".join(read(path) for path in module_paths)
    require_fragments(
        sources,
        (
            'FIXTURE_ID = "preview.population-authoring-0"',
            'PACK_ID = "preview.population.pack"',
            'ACTOR_LEADER_ID = "preview.population.actor.leader"',
            'ACTOR_SCOUT_ID = "preview.population.actor.scout"',
            'TROOP_PATROL_ID = "preview.population.troop.patrol"',
            "def generate_fixture",
            "def verify_fixture",
            "def validate_catalog",
            "Population catalog requires schema 2",
            "Duplicate exact actor subject in troop",
            "Troop requires exactly one typed leader row",
            "Troop member ranges do not overlap profile size",
            "allowed_spawn_candidate_record_ids",
            "forbidden_spawn_candidate_record_ids",
        ),
        "Population fixture implementation",
    )
    reject_fragments(
        sources,
        (
            "requests.",
            "urllib.request",
            "subprocess.",
            "shell=True",
            "os.system(",
            "FoA.exe",
            "WriteProcessMemory",
        ),
        "Population fixture implementation",
    )

    tests = read(tests_path)
    require_fragments(
        tests,
        (
            "test_generation_is_byte_for_byte_deterministic",
            "test_generated_fixture_passes_full_verification",
            "test_generation_refuses_unrelated_non_empty_directory",
            "test_manifest_rejects_path_traversal",
            "test_verification_rejects_absolute_or_private_paths",
            "test_source_fingerprint_must_match_source_input",
            "test_catalog_requires_schema_two",
            "test_fixture_contains_typed_actor_troop_and_member_rows",
            "test_resolved_and_unresolved_template_bindings_are_preserved",
            "test_duplicate_member_actor_subject_is_rejected",
            "test_troop_leader_row_must_match_profile",
            "test_member_ranges_must_overlap_troop_size",
            "test_population_governance_has_allowed_and_forbidden_candidates",
        ),
        "Population fixture tests",
    )

    expected_templates = {
        "Catalog/catalog.tgcatalog.json",
        "Input/preview-population-source.json",
        "Packs/preview.population.tgpack.json",
        "Sources/preview.population.source/evidence.tgevidence.json",
        "Sources/preview.population.source/source.tgsource.json",
        "preview-population.tgworkspace.json",
    }
    actual_templates = {
        path.relative_to(template_root).as_posix()
        for path in template_root.rglob("*")
        if path.is_file()
    }
    require(
        actual_templates == expected_templates,
        "Population fixture template set is incomplete or unexpected.",
    )

    runner = read(runner_path)
    require_fragments(
        runner,
        (
            '"validate_population_preview_fixture.py"',
            'population_fixture = temporary_root / "population-preview-fixture"',
            '"Generate Actor/Troop population fixture"',
            '"Verify Actor/Troop population fixture"',
            'str(TOOLS_ROOT / "population_preview_fixture.py")',
        ),
        "Authoritative local validation runner",
    )

    module = load_fixture_module(script_path)
    temporary_root: Path | None = None
    try:
        temporary_root = Path(
            tempfile.mkdtemp(prefix="tg-population-fixture-contract-")
        )
        output = temporary_root / "fixture"
        manifest = module.generate_fixture(output)
        require(manifest == module.verify_fixture(output), "Manifest verification mismatch")
        require(len(manifest.get("files", [])) == 6, "Manifest must hash six files")
        require(
            manifest.get("expected") == module.EXPECTED_STATE,
            "Fixture expected-state contract mismatch",
        )
    finally:
        if temporary_root:
            shutil.rmtree(temporary_root, ignore_errors=True)


def main() -> int:
    try:
        validate_population_preview_fixture(Path(__file__).resolve().parents[3])
    except (OSError, PopulationFixtureContractError) as exc:
        print(f"Actor/Troop population fixture validation failed: {exc}", file=sys.stderr)
        return 1
    print("Actor/Troop deterministic population fixture and local-gate integration passed.")
    return 0
