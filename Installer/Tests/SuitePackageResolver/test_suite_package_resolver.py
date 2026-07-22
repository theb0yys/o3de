# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3] / "Installer" / "SuiteWizard" / "Resolver" / "Source"
sys.path.insert(0, str(SOURCE))

from suite_package_resolver import (  # noqa: E402
    ResolutionContext,
    ResolverError,
    SemVer,
    VersionRange,
    canonical_json_bytes,
    resolve_suite,
)

COMMIT = "a" * 40
SHA0 = "0" * 64
SHA1 = "1" * 64


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def package(
    package_id: str,
    *,
    version: str = "1.0.0",
    dependencies: list[dict[str, object]] | None = None,
    conflicts: list[str] | None = None,
    status: str = "supported",
    review: str = "approved",
    elevation: bool = False,
    game_versions: list[str] | None = None,
    runtime_targets: list[str] | None = None,
    destination: str | None = None,
) -> dict[str, object]:
    return {
        "$schema": "../../package.schema.json",
        "schema_version": 1,
        "package_id": package_id,
        "display_name": package_id,
        "version": version,
        "kind": "plugin",
        "status": status,
        "source": {
            "kind": "product",
            "repository": "https://github.com/theb0yys/FOA-SDK",
            "commit": COMMIT,
            "path": f"Plugins/{package_id}",
            "fingerprint_sha256": SHA1,
        },
        "compatibility": {
            "platforms": ["windows"],
            "architectures": ["x86_64"],
            "game_versions": game_versions or [],
            "branches": [],
            "runtime_targets": runtime_targets or ["editor-only"],
        },
        "dependencies": dependencies or [],
        "conflicts": conflicts or [],
        "capabilities": ["authoring.read"],
        "payload": [{
            "source": f"payload/{package_id}.bin",
            "destination": destination or f"components/{package_id}/payload.bin",
            "sha256": SHA0,
            "size_bytes": 10,
            "redistribution": "project-owned",
        }],
        "lifecycle": {
            "install_scope": "per-user",
            "elevation_required": elevation,
            "repair_supported": True,
            "upgrade_supported": True,
            "uninstall_supported": True,
            "rollback_required": True,
            "preserve_external_workspaces": True,
        },
        "legal": {
            "license_expression": "Apache-2.0 OR MIT",
            "redistribution_review": review,
            "notice_files": [],
        },
        "authority": {
            "game_launch": False,
            "runtime_execution": False,
            "deployment": False,
            "save_mutation": False,
            "signing": False,
            "publication": False,
            "catalog_mutation": False,
            "evidence_promotion": False,
        },
    }


def suite(
    entries: list[tuple[str, str, int]],
    *,
    features: list[dict[str, object]] | None = None,
    elevation: bool = False,
) -> dict[str, object]:
    return {
        "$schema": "../../suite.schema.json",
        "schema_version": 1,
        "suite_id": "foa.developer",
        "display_name": "FOA Developer Suite",
        "version": "1.0.0",
        "channel": "development",
        "packages": [
            {"package_id": pid, "selection": selection, "order": order, "feature_ids": []}
            for pid, selection, order in entries
        ],
        "features": features or [],
        "compatibility": {"platforms": ["windows"], "architectures": ["x86_64"]},
        "policies": {
            "network_allowed": False,
            "elevation_allowed": elevation,
            "unreviewed_packages_allowed": False,
            "silent_install_allowed": False,
        },
        "provenance": {
            "source_repository": "https://github.com/theb0yys/FOA-SDK",
            "source_commit": COMMIT,
            "reviewed_by": "maintainer",
            "reviewed_at_utc": "2026-07-21T00:00:00Z",
        },
    }


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root / "Installer"
        (self.root / "Packages").mkdir(parents=True)
        (self.root / "Suites").mkdir()
        (self.root / "Packages" / "README.md").write_text("# Packages\n")
        (self.root / "Suites" / "README.md").write_text("# Suites\n")

    def add(self, directory: str, document: dict[str, object]) -> None:
        write(self.root / "Packages" / directory / "package.json", document)

    def set_suite(self, document: dict[str, object]) -> None:
        write(self.root / "Suites" / "Developer" / "suite.json", document)

    def resolve(self, **kwargs: object) -> dict[str, object]:
        return resolve_suite(
            self.root,
            "Developer",
            ResolutionContext("windows", "x86_64", "editor-only"),
            **kwargs,
        )


class ResolverTests(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Fixture]:
        temporary = tempfile.TemporaryDirectory()
        return temporary, Fixture(Path(temporary.name))

    def test_semver_and_range(self) -> None:
        self.assertLess(SemVer.parse("1.0.0-alpha"), SemVer.parse("1.0.0"))
        self.assertEqual(SemVer.parse("1.0.0+one"), SemVer.parse("1.0.0+two"))
        constraint = VersionRange.parse(">=1.2.0 <2.0.0", "range")
        self.assertTrue(constraint.matches(SemVer.parse("1.9.0")))
        self.assertFalse(constraint.matches(SemVer.parse("2.0.0")))
        with self.assertRaisesRegex(ResolverError, "unsupported version-range"):
            VersionRange.parse("^1.2.3", "range")

    def test_selection_modes(self) -> None:
        temporary, f = self.fixture()
        with temporary:
            for pid in ("foa.core", "foa.default", "foa.optional"):
                f.add(pid, package(pid))
            f.set_suite(suite([
                ("foa.core", "required", 0),
                ("foa.default", "default", 1),
                ("foa.optional", "optional", 2),
            ]))
            plan = f.resolve(selected_package_ids=["foa.optional"])
            self.assertEqual(plan["package_order"], ["foa.core", "foa.default", "foa.optional"])
            self.assertEqual(
                f.resolve(excluded_package_ids=["foa.default"])["package_order"],
                ["foa.core"],
            )
            with self.assertRaisesRegex(ResolverError, "cannot be excluded"):
                f.resolve(excluded_package_ids=["foa.core"])

    def test_dependency_closure_and_order(self) -> None:
        temporary, f = self.fixture()
        with temporary:
            f.add("Base", package("foa.base"))
            f.add("Feature", package("foa.feature", dependencies=[{
                "package_id": "foa.base",
                "version_range": ">=1.0.0 <2.0.0",
                "required": True,
            }]))
            f.set_suite(suite([("foa.feature", "required", 0)]))
            plan = f.resolve()
            self.assertEqual(plan["package_order"], ["foa.base", "foa.feature"])
            rows = {row["package_id"]: row for row in plan["packages"]}
            self.assertIn("dependency:foa.feature", rows["foa.base"]["selection_reasons"])

    def test_missing_and_wrong_version_dependency(self) -> None:
        temporary, f = self.fixture()
        with temporary:
            f.add("Feature", package("foa.feature", dependencies=[{
                "package_id": "foa.missing", "version_range": "*", "required": True,
            }]))
            f.set_suite(suite([("foa.feature", "required", 0)]))
            with self.assertRaisesRegex(ResolverError, "requires missing package"):
                f.resolve()
        temporary, f = self.fixture()
        with temporary:
            f.add("Base", package("foa.base", version="2.0.0"))
            f.add("Feature", package("foa.feature", dependencies=[{
                "package_id": "foa.base", "version_range": "<2.0.0", "required": True,
            }]))
            f.set_suite(suite([("foa.feature", "required", 0)]))
            with self.assertRaisesRegex(ResolverError, "selected version is 2.0.0"):
                f.resolve()

    def test_conflict_and_cycle(self) -> None:
        temporary, f = self.fixture()
        with temporary:
            f.add("Mono", package("foa.mono", conflicts=["foa.il2cpp"]))
            f.add("Il2cpp", package("foa.il2cpp"))
            f.set_suite(suite([("foa.mono", "required", 0), ("foa.il2cpp", "required", 1)]))
            with self.assertRaisesRegex(ResolverError, "foa.il2cpp <-> foa.mono"):
                f.resolve()
        temporary, f = self.fixture()
        with temporary:
            f.add("A", package("foa.a", dependencies=[{
                "package_id": "foa.b", "version_range": "*", "required": True,
            }]))
            f.add("B", package("foa.b", dependencies=[{
                "package_id": "foa.a", "version_range": "*", "required": True,
            }]))
            f.set_suite(suite([("foa.a", "required", 0)]))
            with self.assertRaisesRegex(ResolverError, r"foa\.a -> foa\.b -> foa\.a"):
                f.resolve()

    def test_feature_selection(self) -> None:
        temporary, f = self.fixture()
        with temporary:
            f.add("Core", package("foa.core"))
            f.add("UI", package("foa.ui"))
            f.set_suite(suite(
                [("foa.core", "required", 0), ("foa.ui", "optional", 1)],
                features=[{
                    "feature_id": "foa.feature.ui",
                    "display_name": "UI",
                    "package_ids": ["foa.ui"],
                }],
            ))
            self.assertEqual(
                f.resolve(selected_feature_ids=["foa.feature.ui"])["package_order"],
                ["foa.core", "foa.ui"],
            )

    def test_compatibility_review_authority_and_elevation(self) -> None:
        temporary, f = self.fixture()
        with temporary:
            f.add("Runtime", package(
                "foa.runtime", game_versions=["1.2.3"], runtime_targets=["mono"]
            ))
            f.set_suite(suite([("foa.runtime", "required", 0)]))
            with self.assertRaisesRegex(ResolverError, "explicit game version context"):
                f.resolve()
        temporary, f = self.fixture()
        with temporary:
            f.add("Unreviewed", package("foa.unreviewed", review="required"))
            f.set_suite(suite([("foa.unreviewed", "required", 0)]))
            with self.assertRaisesRegex(ResolverError, "approved redistribution"):
                f.resolve()
        temporary, f = self.fixture()
        with temporary:
            unsafe = package("foa.unsafe")
            unsafe["authority"]["deployment"] = True
            f.add("Unsafe", unsafe)
            f.set_suite(suite([("foa.unsafe", "required", 0)]))
            with self.assertRaisesRegex(ResolverError, "illegally grants authority"):
                f.resolve()
        temporary, f = self.fixture()
        with temporary:
            f.add("Admin", package("foa.admin", elevation=True))
            f.set_suite(suite([("foa.admin", "required", 0)]))
            with self.assertRaisesRegex(ResolverError, "suite forbids elevation"):
                f.resolve()

    def test_duplicate_identity_json_and_destination(self) -> None:
        temporary, f = self.fixture()
        with temporary:
            f.add("One", package("foa.same"))
            f.add("Two", package("foa.same"))
            f.set_suite(suite([("foa.same", "required", 0)]))
            with self.assertRaisesRegex(ResolverError, "Duplicate package_id"):
                f.resolve()
        temporary, f = self.fixture()
        with temporary:
            path = f.root / "Packages" / "Bad" / "package.json"
            path.parent.mkdir()
            path.write_text('{"schema_version":1,"schema_version":1}\n')
            f.set_suite(suite([("foa.bad", "required", 0)]))
            with self.assertRaisesRegex(ResolverError, "Duplicate JSON key"):
                f.resolve()
        temporary, f = self.fixture()
        with temporary:
            f.add("One", package("foa.one", destination="Bin/Tool.dll"))
            f.add("Two", package("foa.two", destination="bin/tool.dll"))
            f.set_suite(suite([("foa.one", "required", 0), ("foa.two", "required", 1)]))
            with self.assertRaisesRegex(ResolverError, "destination collision"):
                f.resolve()

    def test_canonical_plan_fingerprint(self) -> None:
        temporary, f = self.fixture()
        with temporary:
            for pid in ("foa.a", "foa.b", "foa.c"):
                f.add(pid, package(pid))
            f.set_suite(suite([
                ("foa.a", "required", 0),
                ("foa.b", "optional", 1),
                ("foa.c", "optional", 2),
            ]))
            first = f.resolve(selected_package_ids=["foa.c", "foa.b"])
            second = f.resolve(selected_package_ids=["foa.b", "foa.c"])
            self.assertEqual(canonical_json_bytes(first), canonical_json_bytes(second))
            base = {key: value for key, value in first.items() if key != "plan_sha256"}
            self.assertEqual(first["plan_sha256"], hashlib.sha256(canonical_json_bytes(base)).hexdigest())


if __name__ == "__main__":
    unittest.main()
