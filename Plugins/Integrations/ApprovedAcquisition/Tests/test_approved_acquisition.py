from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "Tools/approved_acquisition.py"
SPEC = importlib.util.spec_from_file_location("approved_acquisition", MODULE_PATH)
assert SPEC and SPEC.loader
acquisition = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = acquisition
SPEC.loader.exec_module(acquisition)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class ApprovedAcquisitionTests(unittest.TestCase):
    def make_contract(self, root: Path) -> tuple[Path, Path, dict[str, bytes]]:
        payloads = {
            "Sources/knowledge.json": b'{"schema_version":1}\n',
            "Sources/frame.svg": b'<svg xmlns="http://www.w3.org/2000/svg"/>',
        }
        source_root = root / "source"
        for relative, payload in payloads.items():
            path = source_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        packages = [
            {
                "files": [
                    {
                        "bundle_path": "Knowledge/knowledge.json",
                        "bytes": len(payloads["Sources/knowledge.json"]),
                        "media_type": "application/json",
                        "sha256": hashlib.sha256(payloads["Sources/knowledge.json"]).hexdigest(),
                        "source_path": "Sources/knowledge.json",
                    }
                ],
                "id": "knowledge",
                "license": "Apache-2.0 OR MIT",
                "redistribution_reviewed": True,
                "version": "1.0.0",
            },
            {
                "files": [
                    {
                        "bundle_path": "Assets/frame.svg",
                        "bytes": len(payloads["Sources/frame.svg"]),
                        "media_type": "image/svg+xml",
                        "sha256": hashlib.sha256(payloads["Sources/frame.svg"]).hexdigest(),
                        "source_path": "Sources/frame.svg",
                    }
                ],
                "id": "ui-assets",
                "license": "Apache-2.0 OR MIT",
                "redistribution_reviewed": True,
                "version": "1.0.0",
            },
        ]
        manifest = {
            "authority": {name: False for name in acquisition.AUTHORITY_FIELDS},
            "blocked_sources": [
                {"pattern": "Merlin/**", "reason": "optional_merlin_provider_is_separate_later_unit"},
                {"pattern": "Runtime/**", "reason": "runtime_adapters_are_separate_later_units"},
            ],
            "limits": {
                "maximum_file_bytes": 1024,
                "maximum_files": 4,
                "maximum_total_bytes": 4096,
            },
            "packages": packages,
            "provider_id": acquisition.PROVIDER_ID,
            "schema_version": 1,
            "source": {
                "commit": "a" * 40,
                "display_branch": "test",
                "repository": acquisition.GITHUB_REPOSITORY,
            },
        }
        manifest_path = root / "approved-sources.json"
        manifest_path.write_bytes(canonical(manifest))
        return manifest_path, source_root, payloads

    def test_plan_is_deterministic_and_pinned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            manifest_path, _, _ = self.make_contract(Path(temporary))
            manifest = acquisition.load_manifest(manifest_path)
            first = acquisition.build_plan(manifest, provider="pinned-github")
            second = acquisition.build_plan(manifest, provider="pinned-github")
            self.assertEqual(first, second)
            self.assertEqual(first["source"]["commit"], "a" * 40)
            self.assertEqual(first["packages"], ["knowledge", "ui-assets"])
            self.assertTrue(str(first["plan_id"]).startswith("sha256:"))

    def test_local_acquisition_is_atomic_and_verifiable(self) -> None:
        with tempfile.TemporaryDirectory() as contract_temp, tempfile.TemporaryDirectory() as output_temp:
            manifest_path, source_root, _ = self.make_contract(Path(contract_temp))
            manifest = acquisition.load_manifest(manifest_path)
            output = Path(output_temp) / "bundle"
            receipt = acquisition.acquire(
                manifest,
                provider="local",
                output=output,
                source_root=source_root,
                captured_at_utc="2026-07-22T10:00:00Z",
            )
            self.assertEqual(receipt["route"], "local")
            self.assertFalse(receipt["candidate_evidence_created"])
            self.assertNotIn(str(source_root), (output / acquisition.RECEIPT_NAME).read_text())
            verified = acquisition.verify_bundle(output, manifest)
            self.assertEqual(verified["receipt_id"], receipt["receipt_id"])

    def test_pinned_github_route_uses_injected_verified_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as contract_temp, tempfile.TemporaryDirectory() as output_temp:
            manifest_path, _, payloads = self.make_contract(Path(contract_temp))
            manifest = acquisition.load_manifest(manifest_path)
            calls: list[str] = []

            def fake_reader(current_manifest, approved):
                self.assertIs(current_manifest, manifest)
                calls.append(acquisition.pinned_github_url(manifest, approved))
                return payloads[approved.source_path]

            output = Path(output_temp) / "bundle"
            acquisition.acquire(
                manifest,
                provider="pinned-github",
                output=output,
                captured_at_utc="2026-07-22T10:00:00Z",
                github_reader=fake_reader,
            )
            self.assertEqual(len(calls), 2)
            self.assertTrue(all("/" + "a" * 40 + "/" in url for url in calls))
            self.assertTrue(all("/main/" not in url for url in calls))
            acquisition.verify_bundle(output, manifest)

    def test_tampered_bundle_fails(self) -> None:
        with tempfile.TemporaryDirectory() as contract_temp, tempfile.TemporaryDirectory() as output_temp:
            manifest_path, source_root, _ = self.make_contract(Path(contract_temp))
            manifest = acquisition.load_manifest(manifest_path)
            output = Path(output_temp) / "bundle"
            acquisition.acquire(
                manifest,
                provider="local",
                output=output,
                source_root=source_root,
                captured_at_utc="2026-07-22T10:00:00Z",
            )
            (output / "Assets/frame.svg").write_text("tampered", encoding="utf-8")
            with self.assertRaisesRegex(acquisition.AcquisitionError, "Byte count differs|SHA-256 differs"):
                acquisition.verify_bundle(output, manifest)

    def test_unknown_package_and_existing_output_fail(self) -> None:
        with tempfile.TemporaryDirectory() as contract_temp, tempfile.TemporaryDirectory() as output_temp:
            manifest_path, source_root, _ = self.make_contract(Path(contract_temp))
            manifest = acquisition.load_manifest(manifest_path)
            with self.assertRaisesRegex(acquisition.AcquisitionError, "Unknown approved package"):
                acquisition.build_plan(manifest, provider="local", package_ids=["unknown"])
            output = Path(output_temp) / "bundle"
            output.mkdir()
            with self.assertRaisesRegex(acquisition.AcquisitionError, "already exists"):
                acquisition.acquire(
                    manifest,
                    provider="local",
                    output=output,
                    source_root=source_root,
                )

    @unittest.skipIf(os.name == "nt", "Windows symlink creation requires privileges")
    def test_local_symlink_source_fails(self) -> None:
        with tempfile.TemporaryDirectory() as contract_temp, tempfile.TemporaryDirectory() as output_temp:
            manifest_path, source_root, _ = self.make_contract(Path(contract_temp))
            target = source_root / "Sources/frame.svg"
            original = source_root / "Sources/original.svg"
            target.rename(original)
            target.symlink_to(original)
            manifest = acquisition.load_manifest(manifest_path)
            with self.assertRaisesRegex(acquisition.AcquisitionError, "symlink"):
                acquisition.acquire(
                    manifest,
                    provider="local",
                    output=Path(output_temp) / "bundle",
                    source_root=source_root,
                )

    def test_production_manifest_matches_golden_plan_and_seed_hashes(self) -> None:
        manifest = acquisition.load_manifest(acquisition.DEFAULT_MANIFEST)
        actual = acquisition.canonical_json_bytes(
            acquisition.build_plan(manifest, provider="pinned-github")
        )
        fixture = (
            Path(__file__).resolve().parent
            / "Fixtures/pinned-github-all.plan.json"
        ).read_bytes()
        self.assertEqual(actual, fixture)
        for approved in manifest.files:
            if not approved.source_path.startswith(
                "Plugins/Integrations/ApprovedAcquisition/Seeds/Assets/"
            ):
                continue
            payload = (acquisition.REPO_ROOT / approved.source_path).read_bytes()
            acquisition.validate_payload(payload, approved)

    def test_output_inside_repository_fails(self) -> None:
        candidate = acquisition.REPO_ROOT / "build/acquired"
        with self.assertRaisesRegex(acquisition.AcquisitionError, "outside"):
            acquisition.validate_external_output_path(candidate)


if __name__ == "__main__":
    unittest.main()
