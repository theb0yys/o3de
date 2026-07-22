# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import ast
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPO_ROOT / "Installer" / "SuiteWizard" / "Host" / "Source"
sys.path.insert(0, str(SOURCE))

from wizard_host_controller import WizardHostController, WizardHostError  # noqa: E402
from wizard_catalog import CatalogInterfaceError  # noqa: E402

INSTALLER_ROOT = REPO_ROOT / "Installer"
EXPECTED_ORDER = [
    "foa.foundation-descriptor",
    "foa.editor-descriptor",
    "foa.installer-documentation",
]


class SuiteWizardHostTests(unittest.TestCase):
    def controller(self, installer_root: Path = INSTALLER_ROOT) -> WizardHostController:
        return WizardHostController(installer_root)

    def test_initial_state_renders_reviewed_suite_package_and_feature_choices(self) -> None:
        controller = self.controller()
        snapshot = controller.host_snapshot()
        self.assertEqual(snapshot["selected_suite_id"], "foa.developer-preview")
        self.assertEqual(len(snapshot["catalog_sha256"]), 64)
        self.assertEqual(snapshot["context"], {
            "platform": "windows",
            "architecture": "x86_64",
            "runtime_target": "editor-only",
            "game_version": "",
            "branch": "",
        })
        packages = {row["package_id"]: row for row in snapshot["packages"]}
        self.assertEqual([row["package_id"] for row in snapshot["packages"]], EXPECTED_ORDER)
        self.assertTrue(packages["foa.foundation-descriptor"]["included"])
        self.assertTrue(packages["foa.foundation-descriptor"]["locked"])
        self.assertTrue(packages["foa.editor-descriptor"]["included"])
        self.assertFalse(packages["foa.editor-descriptor"]["locked"])
        self.assertFalse(packages["foa.installer-documentation"]["included"])
        self.assertEqual(
            [row["feature_id"] for row in snapshot["features"]],
            ["foa.feature.documentation", "foa.feature.editor"],
        )
        self.assertTrue(all(value is False for value in snapshot["authority"].values()))

    def test_graphical_choices_delegate_final_package_order_to_resolver(self) -> None:
        controller = self.controller()
        controller.set_package_included("foa.editor-descriptor", False)
        controller.set_feature_selected("foa.feature.documentation", True)
        review = controller.resolve_review()
        self.assertEqual(
            [row["package_id"] for row in review["packages"]],
            ["foa.foundation-descriptor", "foa.installer-documentation"],
        )
        self.assertEqual(
            [row["package_id"] for row in review["payload"]],
            ["foa.foundation-descriptor", "foa.installer-documentation"],
        )
        self.assertEqual(review["summary"], {
            "package_count": 2,
            "payload_file_count": 2,
            "payload_size_bytes": 1260,
        })
        self.assertTrue(all(value is False for value in review["authority"].values()))
        for field in (
            "catalog_sha256",
            "selection_sha256",
            "plan_sha256",
            "view_model_sha256",
            "result_sha256",
        ):
            self.assertEqual(len(review[field]), 64)

    def test_required_package_cannot_be_excluded(self) -> None:
        controller = self.controller()
        with self.assertRaisesRegex(WizardHostError, "Required package"):
            controller.set_package_included("foa.foundation-descriptor", False)
        self.assertTrue(
            next(
                row["included"]
                for row in controller.package_choices()
                if row["package_id"] == "foa.foundation-descriptor"
            )
        )

    def test_refresh_resets_transient_choices_and_invalidates_review(self) -> None:
        controller = self.controller()
        controller.set_package_included("foa.editor-descriptor", False)
        controller.set_feature_selected("foa.feature.documentation", True)
        controller.resolve_review()
        self.assertTrue(controller.host_snapshot()["review_available"])
        refreshed = controller.refresh_catalog()
        self.assertFalse(refreshed["review_available"])
        packages = {row["package_id"]: row for row in refreshed["packages"]}
        self.assertTrue(packages["foa.editor-descriptor"]["included"])
        self.assertFalse(packages["foa.installer-documentation"]["included"])
        self.assertTrue(all(not row["selected"] for row in refreshed["features"]))

    def test_manifest_drift_after_display_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied_installer = Path(temporary) / "Installer"
            shutil.copytree(INSTALLER_ROOT, copied_installer)
            controller = self.controller(copied_installer)
            suite_path = copied_installer / "Suites" / "DeveloperPreview" / "suite.json"
            document = json.loads(suite_path.read_text(encoding="utf-8"))
            document["display_name"] = "Changed after graphical review"
            suite_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(CatalogInterfaceError, "catalogue changed"):
                controller.resolve_review()

    def test_graphical_host_uses_native_widgets_and_exposes_no_executor_surface(self) -> None:
        host_path = SOURCE / "suite_wizard_host.py"
        source = host_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_roots.update(
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        self.assertIn("tkinter", source)
        self.assertIn("ttk.Notebook", source)
        self.assertIn("ttk.Treeview", source)
        self.assertIn("ttk.Checkbutton", source)
        self.assertIn("resolve_review", source)
        self.assertTrue({"subprocess", "socket", "urllib", "requests"}.isdisjoint(imported_roots))
        for forbidden in (
            "os.system",
            "Popen(",
            "write_bytes",
            "write_text",
            "shutil.copy",
            "urlopen",
            "InstallerEngine",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
