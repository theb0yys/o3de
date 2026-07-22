# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import ast
import importlib.util
import tempfile
import unittest
from pathlib import Path

SOURCE = (
    Path(__file__).resolve().parents[2]
    / "Bootstrapper"
    / "Acquisition"
    / "Source"
    / "bootstrapper_acquisition.py"
)
SPEC = importlib.util.spec_from_file_location("foa_bootstrapper_acquisition", SOURCE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load bootstrapper acquisition module: {SOURCE}")
acquisition = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acquisition)


def package(
    package_id: str = "foa.knowledge",
    *,
    capabilities: list[str] | None = None,
) -> dict[str, object]:
    return {
        "package_id": package_id,
        "display_name": package_id,
        "version": "1.0.0",
        "kind": "integration",
        "status": "supported",
        "selection_reasons": ["suite:required"],
        "dependency_ids": [],
        "capabilities": capabilities if capabilities is not None else [
            "acquisition.approved.tainted-framework-knowledge"
        ],
        "manifest_sha256": "1" * 64,
        "source": {
            "kind": "product",
            "repository": "https://github.com/theb0yys/FOA-SDK",
            "commit": "a" * 40,
            "path": "Installer/Packages/Knowledge",
        },
        "lifecycle": {
            "install_scope": "per-user",
            "elevation_required": False,
            "repair_supported": True,
            "upgrade_supported": True,
            "uninstall_supported": True,
            "rollback_required": False,
            "preserve_external_workspaces": True,
        },
        "legal": {
            "license_expression": "Apache-2.0 OR MIT",
            "redistribution_review": "approved",
            "notice_files": [],
        },
        "payload": [],
    }


def resolver_plan(
    wizard,
    *,
    network_allowed: bool = False,
    packages: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    rows = packages or [package()]
    base = {
        "schema_version": 1,
        "suite": {
            "suite_id": "foa.developer",
            "display_name": "Developer",
            "version": "1.0.0",
            "channel": "development",
            "manifest_sha256": "2" * 64,
        },
        "context": {
            "platform": "windows",
            "architecture": "x86_64",
            "runtime_target": "editor-only",
            "game_version": "",
            "branch": "",
        },
        "selection": {
            "selected_package_ids": [],
            "excluded_package_ids": [],
            "selected_feature_ids": [],
        },
        "policies": {
            "network_allowed": network_allowed,
            "elevation_allowed": True,
            "unreviewed_packages_allowed": False,
            "silent_install_allowed": False,
        },
        "requires_elevation": False,
        "package_order": [row["package_id"] for row in rows],
        "packages": rows,
        "summary": {
            "package_count": len(rows),
            "payload_file_count": 0,
            "payload_size_bytes": 0,
        },
        "warnings": [],
    }
    return {**base, "plan_sha256": wizard.sha256(base)}


class BootstrapperAcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.wizard = acquisition.load_wizard_api()
        cls.provider = acquisition.load_provider_api()
        cls.manifest = cls.provider.load_manifest()

    def artifacts(
        self,
        *,
        route: str = "local",
        network_allowed: bool = False,
        packages: list[dict[str, object]] | None = None,
        provider_packages: tuple[str, ...] = ("tainted-framework-knowledge",),
    ) -> tuple[dict[str, object], ...]:
        plan = resolver_plan(
            self.wizard,
            network_allowed=network_allowed,
            packages=packages,
        )
        view = self.wizard.build_view_model(plan)
        confirmation = self.wizard.create_confirmation(
            plan,
            view,
            expected_plan_sha256=plan["plan_sha256"],
            acknowledged_ids=self.wizard.required_acknowledgement_ids(view),
            confirmed_by="Maintainer",
            confirmed_at_utc="2026-07-22T03:00:00Z",
        )
        provider_plan = self.provider.build_plan(
            self.manifest,
            provider=route,
            package_ids=provider_packages,
        )
        request = acquisition.build_request(
            plan,
            view,
            confirmation,
            provider_plan,
            expected_confirmation_sha256=confirmation["confirmation_sha256"],
            output_reference="foa.acquisition.bundle",
            authorized_by="Maintainer",
            authorized_at_utc="2026-07-22T04:00:00Z",
            wizard_api=self.wizard,
            provider_api=self.provider,
        )
        return plan, view, confirmation, provider_plan, request

    def test_request_is_deterministic_and_exact_bound(self) -> None:
        first = self.artifacts()
        second = self.artifacts()
        self.assertEqual(
            acquisition.canonical_json(first[-1]),
            acquisition.canonical_json(second[-1]),
        )
        request = first[-1]
        self.assertEqual(
            request["bindings"],
            [{
                "installer_package_id": "foa.knowledge",
                "provider_package_id": "tainted-framework-knowledge",
            }],
        )
        self.assertTrue(request["authority"]["acquisition"])
        self.assertTrue(request["authority"]["filesystem_write"])
        self.assertFalse(request["authority"]["network"])
        self.assertFalse(request["authority"]["installation"])
        self.assertFalse(request["authority"]["elevation"])

    def test_pinned_github_requires_reviewed_network_policy(self) -> None:
        with self.assertRaisesRegex(
            acquisition.BootstrapperAcquisitionError,
            "network policy",
        ):
            self.artifacts(route="pinned-github")
        request = self.artifacts(
            route="pinned-github",
            network_allowed=True,
        )[-1]
        self.assertTrue(request["authority"]["network"])

    def test_provider_packages_require_explicit_capability_bindings(self) -> None:
        with self.assertRaisesRegex(
            acquisition.BootstrapperAcquisitionError,
            "binding mismatch",
        ):
            self.artifacts(packages=[package(capabilities=[])])
        duplicate = [package("foa.first"), package("foa.second")]
        with self.assertRaisesRegex(
            acquisition.BootstrapperAcquisitionError,
            "bound more than once",
        ):
            self.artifacts(packages=duplicate)

    def test_stale_confirmation_and_request_tampering_fail(self) -> None:
        plan, view, confirmation, provider_plan, request = self.artifacts()
        changed_plan = resolver_plan(
            self.wizard,
            packages=[package(), package("foa.other", capabilities=[])],
        )
        changed_view = self.wizard.build_view_model(changed_plan)
        with self.assertRaisesRegex(
            acquisition.BootstrapperAcquisitionError,
            "Upstream plan",
        ):
            acquisition.verify_request(
                changed_plan,
                changed_view,
                confirmation,
                provider_plan,
                request,
                wizard_api=self.wizard,
                provider_api=self.provider,
            )
        request["authorized_by"] = "Changed"
        with self.assertRaisesRegex(
            acquisition.BootstrapperAcquisitionError,
            "fingerprint",
        ):
            acquisition.verify_request(
                plan,
                view,
                confirmation,
                provider_plan,
                request,
                wizard_api=self.wizard,
                provider_api=self.provider,
            )

    def test_real_local_provider_execution_and_result_verification(self) -> None:
        plan, view, confirmation, provider_plan, request = self.artifacts()
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary) / "bundle"
            result = acquisition.execute_request(
                plan,
                view,
                confirmation,
                provider_plan,
                request,
                output=bundle,
                source_root=acquisition.REPO_ROOT,
                captured_at_utc="2026-07-22T04:00:01Z",
                completed_at_utc="2026-07-22T04:00:02Z",
                wizard_api=self.wizard,
                provider_api=self.provider,
            )
            self.assertTrue(result["verification"]["bundle_verified"])
            self.assertTrue(result["effects"]["acquisition_performed"])
            self.assertFalse(result["effects"]["installation_performed"])
            self.assertTrue(
                all(value is False for value in result["remaining_authority"].values())
            )
            self.assertEqual(
                acquisition.verify_result(
                    plan,
                    view,
                    confirmation,
                    provider_plan,
                    request,
                    result,
                    bundle=bundle,
                    wizard_api=self.wizard,
                    provider_api=self.provider,
                ),
                result,
            )

    def test_invalid_chronology_refuses_before_output_creation(self) -> None:
        plan, view, confirmation, provider_plan, request = self.artifacts()
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary) / "bundle"
            with self.assertRaisesRegex(
                acquisition.BootstrapperAcquisitionError,
                "chronology",
            ):
                acquisition.execute_request(
                    plan,
                    view,
                    confirmation,
                    provider_plan,
                    request,
                    output=bundle,
                    source_root=acquisition.REPO_ROOT,
                    captured_at_utc="2026-07-22T03:59:59Z",
                    completed_at_utc="2026-07-22T04:00:02Z",
                    wizard_api=self.wizard,
                    provider_api=self.provider,
                )
            self.assertFalse(bundle.exists())

    def test_result_effect_tampering_fails(self) -> None:
        plan, view, confirmation, provider_plan, request = self.artifacts()
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary) / "bundle"
            result = acquisition.execute_request(
                plan,
                view,
                confirmation,
                provider_plan,
                request,
                output=bundle,
                source_root=acquisition.REPO_ROOT,
                captured_at_utc="2026-07-22T04:00:01Z",
                completed_at_utc="2026-07-22T04:00:02Z",
                wizard_api=self.wizard,
                provider_api=self.provider,
            )
            result["effects"]["installation_performed"] = True
            unsigned = {
                key: value for key, value in result.items() if key != "result_sha256"
            }
            result["result_sha256"] = acquisition.sha256(unsigned)
            with self.assertRaisesRegex(
                acquisition.BootstrapperAcquisitionError,
                "effects exceed",
            ):
                acquisition.verify_result(
                    plan,
                    view,
                    confirmation,
                    provider_plan,
                    request,
                    result,
                    bundle=bundle,
                    wizard_api=self.wizard,
                    provider_api=self.provider,
                )

    def test_module_has_no_installation_or_elevation_executor(self) -> None:
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        imported = set()
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                calls.add(node.func.id)
        self.assertNotIn("subprocess", imported)
        self.assertNotIn("urllib", imported)
        self.assertTrue(
            {"exec", "eval", "compile", "system", "popen"}.isdisjoint(calls)
        )
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("runas", source.casefold())
        self.assertNotIn("shell_execute", source.casefold())


if __name__ == "__main__":
    unittest.main()
