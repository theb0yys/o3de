#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = TOOLS_ROOT / "population_preview_fixture.py"
SPEC = importlib.util.spec_from_file_location(
    "population_preview_fixture",
    MODULE_PATH,
)
assert SPEC and SPEC.loader
fixture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fixture)


class PopulationPreviewFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(
            tempfile.mkdtemp(prefix="tg-population-fixture-tests-")
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def generate(self, name: str = "fixture") -> Path:
        output = self.temp_root / name
        fixture.generate_fixture(output)
        return output

    def test_generation_is_byte_for_byte_deterministic(self) -> None:
        left = self.generate("left")
        right = self.generate("right")
        left_files = sorted(
            path.relative_to(left)
            for path in left.rglob("*")
            if path.is_file()
        )
        right_files = sorted(
            path.relative_to(right)
            for path in right.rglob("*")
            if path.is_file()
        )
        self.assertEqual(left_files, right_files)
        for relative_path in left_files:
            self.assertEqual(
                (left / relative_path).read_bytes(),
                (right / relative_path).read_bytes(),
            )

    def test_generated_fixture_passes_full_verification(self) -> None:
        output = self.generate()
        manifest = fixture.verify_fixture(output)
        self.assertEqual(manifest["fixture_id"], fixture.FIXTURE_ID)
        self.assertEqual(len(manifest["files"]), 6)

    def test_manifest_entries_are_sorted_and_hash_every_payload(self) -> None:
        output = self.generate()
        manifest = json.loads(
            (output / fixture.MANIFEST_NAME).read_text(encoding="utf-8")
        )
        paths = [entry["path"] for entry in manifest["files"]]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(paths, sorted(fixture.EXPECTED_FILE_PATHS))
        for entry in manifest["files"]:
            payload = (output / entry["path"]).read_bytes()
            self.assertEqual(entry["sha256"], fixture.sha256_bytes(payload))
            self.assertEqual(entry["size_bytes"], len(payload))

    def test_generation_refuses_unrelated_non_empty_directory(self) -> None:
        output = self.temp_root / "fixture"
        output.mkdir()
        (output / "unrelated.txt").write_text(
            "do not overwrite",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            fixture.PopulationFixtureError,
            "not empty",
        ):
            fixture.generate_fixture(output)

    def test_replace_requires_existing_fixture_to_verify_first(self) -> None:
        output = self.generate()
        (output / fixture.CATALOG_PATH).write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(
            fixture.PopulationFixtureError,
            "SHA-256 mismatch",
        ):
            fixture.generate_fixture(output, replace=True)

    def test_verification_rejects_unexpected_files(self) -> None:
        output = self.generate()
        (output / "unexpected.txt").write_text("extra", encoding="utf-8")
        with self.assertRaisesRegex(
            fixture.PopulationFixtureError,
            "missing or unexpected",
        ):
            fixture.verify_fixture(output)

    def test_manifest_rejects_path_traversal(self) -> None:
        output = self.generate()
        manifest_path = output / fixture.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"][0]["path"] = "../escape.json"
        manifest_path.write_bytes(fixture.canonical_json_bytes(manifest))
        with self.assertRaisesRegex(
            fixture.PopulationFixtureError,
            "traversal",
        ):
            fixture.verify_fixture(output)

    def test_verification_rejects_absolute_or_private_paths(self) -> None:
        output = self.generate()
        workspace_path = output / fixture.WORKSPACE_PATH
        workspace = json.loads(workspace_path.read_text(encoding="utf-8"))
        workspace["GameProfiles"][0]["InstallPath"] = (
            "C:\\Users\\Example\\Game"
        )
        workspace_path.write_bytes(fixture.canonical_json_bytes(workspace))
        self._rehash(output, fixture.WORKSPACE_PATH)
        with self.assertRaisesRegex(
            fixture.PopulationFixtureError,
            "absolute or private path",
        ):
            fixture.verify_fixture(output)

    def test_source_fingerprint_must_match_source_input(self) -> None:
        output = self.generate()
        source_input_path = output / fixture.SOURCE_INPUT_PATH
        source_input = json.loads(
            source_input_path.read_text(encoding="utf-8")
        )
        source_input["evidence"][0]["claim"] = "changed"
        source_input_path.write_bytes(
            fixture.canonical_json_bytes(source_input)
        )
        self._rehash(output, fixture.SOURCE_INPUT_PATH)
        with self.assertRaisesRegex(
            fixture.PopulationFixtureError,
            "Source fingerprint",
        ):
            fixture.verify_fixture(output)

    def test_catalog_requires_schema_two(self) -> None:
        output = self.generate()
        catalog_path = output / fixture.CATALOG_PATH
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog["SchemaVersion"] = 1
        catalog_path.write_bytes(fixture.canonical_json_bytes(catalog))
        self._rehash(output, fixture.CATALOG_PATH)
        with self.assertRaisesRegex(
            fixture.PopulationFixtureError,
            "requires schema 2",
        ):
            fixture.verify_fixture(output)

    def test_fixture_contains_typed_actor_troop_and_member_rows(self) -> None:
        output = self.generate()
        catalog = json.loads(
            (output / fixture.CATALOG_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual(len(catalog["ActorProfiles"]), 2)
        self.assertEqual(len(catalog["TroopProfiles"]), 1)
        self.assertEqual(len(catalog["TroopMembers"]), 2)
        self.assertEqual(
            [value["RecordId"] for value in catalog["ActorProfiles"]],
            sorted(value["RecordId"] for value in catalog["ActorProfiles"]),
        )
        self.assertEqual(
            [value["LinkId"] for value in catalog["TroopMembers"]],
            sorted(value["LinkId"] for value in catalog["TroopMembers"]),
        )

    def test_resolved_and_unresolved_template_bindings_are_preserved(self) -> None:
        output = self.generate()
        catalog = json.loads(
            (output / fixture.CATALOG_PATH).read_text(encoding="utf-8")
        )
        profiles = {
            value["RecordId"]: value
            for value in catalog["ActorProfiles"]
        }
        leader = profiles[fixture.ACTOR_LEADER_ID]
        scout = profiles[fixture.ACTOR_SCOUT_ID]
        self.assertEqual(
            leader["TemplateRecordId"],
            fixture.TEMPLATE_GUARD_ID,
        )
        self.assertTrue(leader["TemplateSubjectRef"])
        self.assertEqual(scout["TemplateRecordId"], "")
        self.assertEqual(
            scout["TemplateSubjectRef"],
            fixture.UNRESOLVED_TEMPLATE_SUBJECT,
        )

    def test_duplicate_member_actor_subject_is_rejected(self) -> None:
        output = self.generate()
        catalog_path = output / fixture.CATALOG_PATH
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        leader = catalog["TroopMembers"][0]
        scout = catalog["TroopMembers"][1]
        scout["ActorRecordId"] = leader["ActorRecordId"]
        scout["ActorSubjectRef"] = leader["ActorSubjectRef"]
        catalog_path.write_bytes(fixture.canonical_json_bytes(catalog))
        self._rehash(output, fixture.CATALOG_PATH)
        with self.assertRaisesRegex(
            fixture.PopulationFixtureError,
            "Duplicate exact actor subject",
        ):
            fixture.verify_fixture(output)

    def test_troop_leader_row_must_match_profile(self) -> None:
        output = self.generate()
        catalog_path = output / fixture.CATALOG_PATH
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        for member in catalog["TroopMembers"]:
            if member["Role"] == "leader":
                member["Role"] = "melee"
        catalog_path.write_bytes(fixture.canonical_json_bytes(catalog))
        self._rehash(output, fixture.CATALOG_PATH)
        with self.assertRaisesRegex(
            fixture.PopulationFixtureError,
            "exactly one typed leader row",
        ):
            fixture.verify_fixture(output)

    def test_member_ranges_must_overlap_troop_size(self) -> None:
        output = self.generate()
        catalog_path = output / fixture.CATALOG_PATH
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog["TroopProfiles"][0]["MinimumSize"] = 10
        catalog["TroopProfiles"][0]["MaximumSize"] = 10
        catalog_path.write_bytes(fixture.canonical_json_bytes(catalog))
        self._rehash(output, fixture.CATALOG_PATH)
        with self.assertRaisesRegex(
            fixture.PopulationFixtureError,
            "do not overlap",
        ):
            fixture.verify_fixture(output)

    def test_population_governance_has_allowed_and_forbidden_candidates(
        self,
    ) -> None:
        output = self.generate()
        catalog = json.loads(
            (output / fixture.CATALOG_PATH).read_text(encoding="utf-8")
        )
        records = {
            record["RecordId"]: record
            for record in catalog["Records"]
        }
        self.assertIn(
            "spawn_candidate",
            records[fixture.ACTOR_LEADER_ID]["AllowedUsages"],
        )
        self.assertIn(
            "spawn_candidate",
            records[fixture.ACTOR_SCOUT_ID]["ForbiddenUsages"],
        )
        self.assertIn(
            "spawn_candidate",
            records[fixture.TROOP_PATROL_ID]["AllowedUsages"],
        )

    def test_all_identities_use_reserved_population_preview_namespace(
        self,
    ) -> None:
        documents = fixture.template_documents()
        catalog = documents[fixture.CATALOG_PATH]
        for record in catalog["Records"]:
            self.assertTrue(record["RecordId"].startswith("preview.population."))
            self.assertTrue(
                record["SubjectRef"].startswith(
                    "subject:preview:population:"
                )
            )
            self.assertEqual(record["NativeRefExact"], "")
        evidence = documents[fixture.EVIDENCE_DOCUMENT_PATH]["Evidence"]
        self.assertTrue(
            all(
                value["EvidenceId"].startswith(
                    "preview.population.evidence."
                )
                for value in evidence
            )
        )
        self.assertTrue(
            all(
                fixture.is_reserved_population_subject(
                    value["SubjectRef"]
                )
                for value in evidence
            )
        )

    def test_cli_returns_success_for_generate_and_verify(self) -> None:
        output = self.temp_root / "cli"
        self.assertEqual(
            fixture.main(["generate", "--output", str(output)]),
            0,
        )
        self.assertEqual(
            fixture.main(["verify", "--output", str(output)]),
            0,
        )

    def test_cli_returns_failure_for_invalid_fixture(self) -> None:
        output = self.temp_root / "missing"
        self.assertEqual(
            fixture.main(["verify", "--output", str(output)]),
            1,
        )

    def _rehash(self, output: Path, relative_path: str) -> None:
        manifest_path = output / fixture.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload = (output / relative_path).read_bytes()
        for entry in manifest["files"]:
            if entry["path"] == relative_path:
                entry["sha256"] = fixture.sha256_bytes(payload)
                entry["size_bytes"] = len(payload)
                break
        manifest_path.write_bytes(fixture.canonical_json_bytes(manifest))


if __name__ == "__main__":
    unittest.main()
