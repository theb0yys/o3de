# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPO_ROOT / "Installer" / "SuiteWizard" / "Host" / "Source"

import sys

sys.path.insert(0, str(SOURCE))

from wizard_receipt_controller import (  # noqa: E402
    ReceiptError,
    WizardHostError,
    WizardReceiptController,
)

INSTALLER_ROOT = REPO_ROOT / "Installer"
CONFIRMED_AT = "2026-07-22T00:00:00Z"


class SuiteWizardReceiptHostTests(unittest.TestCase):
    def controller(self) -> WizardReceiptController:
        return WizardReceiptController(INSTALLER_ROOT)

    @staticmethod
    def confirm(
        controller: WizardReceiptController,
        *,
        confirmed_by: str = "FOA-SDK graphical receipt tests",
    ) -> dict[str, object]:
        review = controller.resolve_review()
        for row in controller.acknowledgement_choices():
            controller.set_acknowledgement(str(row["acknowledgement_id"]), True)
        return controller.create_review_confirmation(
            expected_plan_sha256=str(review["plan_sha256"]),
            expected_view_model_sha256=str(review["view_model_sha256"]),
            confirmed_by=confirmed_by,
            confirmed_at_utc=CONFIRMED_AT,
        )

    def test_export_and_verify_bind_the_exact_current_chain(self) -> None:
        controller = self.controller()
        confirmation = self.confirm(controller)
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "current.foa-receipt.json"
            exported = controller.export_current_receipt(
                destination,
                expected_plan_sha256=str(confirmation["plan_sha256"]),
                expected_view_model_sha256=str(confirmation["view_model_sha256"]),
                expected_confirmation_sha256=str(confirmation["confirmation_sha256"]),
            )
            self.assertEqual(exported["status"], "published")
            self.assertEqual(exported["path"], str(destination))
            self.assertEqual(exported["plan_sha256"], confirmation["plan_sha256"])
            self.assertEqual(
                exported["view_model_sha256"], confirmation["view_model_sha256"]
            )
            self.assertEqual(
                exported["confirmation_sha256"], confirmation["confirmation_sha256"]
            )
            self.assertEqual(len(exported["receipt_sha256"]), 64)
            self.assertTrue(exported["current"])
            self.assertTrue(all(value is False for value in exported["authority"].values()))

            verified = controller.verify_current_receipt(
                destination,
                expected_plan_sha256=str(confirmation["plan_sha256"]),
                expected_view_model_sha256=str(confirmation["view_model_sha256"]),
                expected_confirmation_sha256=str(confirmation["confirmation_sha256"]),
            )
            self.assertEqual(verified["status"], "verified")
            self.assertEqual(verified["receipt_sha256"], exported["receipt_sha256"])
            self.assertTrue(controller.host_snapshot()["receipt_available"])

    def test_stale_displayed_hashes_fail_before_destination_creation(self) -> None:
        controller = self.controller()
        confirmation = self.confirm(controller)
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "stale.foa-receipt.json"
            with self.assertRaisesRegex(WizardHostError, "confirmation fingerprint is stale"):
                controller.export_current_receipt(
                    destination,
                    expected_plan_sha256=str(confirmation["plan_sha256"]),
                    expected_view_model_sha256=str(confirmation["view_model_sha256"]),
                    expected_confirmation_sha256="0" * 64,
                )
            self.assertFalse(destination.exists())

    def test_acknowledgement_and_context_changes_invalidate_receipt_state(self) -> None:
        controller = self.controller()
        confirmation = self.confirm(controller)
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "accepted.foa-receipt.json"
            controller.export_current_receipt(
                destination,
                expected_plan_sha256=str(confirmation["plan_sha256"]),
                expected_view_model_sha256=str(confirmation["view_model_sha256"]),
                expected_confirmation_sha256=str(confirmation["confirmation_sha256"]),
            )
            first_ack = str(controller.acknowledgement_choices()[0]["acknowledgement_id"])
            controller.set_acknowledgement(first_ack, False)
            self.assertFalse(controller.host_snapshot()["receipt_available"])
            with self.assertRaisesRegex(WizardHostError, "Export or verify"):
                controller.receipt_snapshot()

            confirmation = self.confirm(controller, confirmed_by="replacement confirmer")
            controller.export_current_receipt(
                Path(temporary) / "replacement.foa-receipt.json",
                expected_plan_sha256=str(confirmation["plan_sha256"]),
                expected_view_model_sha256=str(confirmation["view_model_sha256"]),
                expected_confirmation_sha256=str(confirmation["confirmation_sha256"]),
            )
            controller.set_context(
                platform="windows",
                architecture="x86_64",
                runtime_target="editor-only",
                branch="changed-after-receipt",
            )
            self.assertFalse(controller.host_snapshot()["review_available"])
            self.assertFalse(controller.host_snapshot()["confirmation_available"])
            self.assertFalse(controller.host_snapshot()["receipt_available"])

    def test_existing_different_file_is_not_replaced(self) -> None:
        controller = self.controller()
        confirmation = self.confirm(controller)
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "occupied.foa-receipt.json"
            original = b"preserve-this-file\n"
            destination.write_bytes(original)
            with self.assertRaisesRegex(ReceiptError, "different bytes"):
                controller.export_current_receipt(
                    destination,
                    expected_plan_sha256=str(confirmation["plan_sha256"]),
                    expected_view_model_sha256=str(confirmation["view_model_sha256"]),
                    expected_confirmation_sha256=str(confirmation["confirmation_sha256"]),
                )
            self.assertEqual(destination.read_bytes(), original)
            self.assertFalse(controller.host_snapshot()["receipt_available"])

    def test_receipt_from_previous_confirmation_does_not_match_new_confirmation(self) -> None:
        controller = self.controller()
        first = self.confirm(controller, confirmed_by="first confirmer")
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "first.foa-receipt.json"
            controller.export_current_receipt(
                destination,
                expected_plan_sha256=str(first["plan_sha256"]),
                expected_view_model_sha256=str(first["view_model_sha256"]),
                expected_confirmation_sha256=str(first["confirmation_sha256"]),
            )

            controller.invalidate_confirmation()
            second = controller.create_review_confirmation(
                expected_plan_sha256=str(first["plan_sha256"]),
                expected_view_model_sha256=str(first["view_model_sha256"]),
                confirmed_by="second confirmer",
                confirmed_at_utc=CONFIRMED_AT,
            )
            with self.assertRaisesRegex(ReceiptError, "does not match"):
                controller.verify_current_receipt(
                    destination,
                    expected_plan_sha256=str(second["plan_sha256"]),
                    expected_view_model_sha256=str(second["view_model_sha256"]),
                    expected_confirmation_sha256=str(second["confirmation_sha256"]),
                )
            self.assertFalse(controller.host_snapshot()["receipt_available"])

    def test_graphical_receipt_surface_has_no_installer_or_network_authority(self) -> None:
        paths = [
            SOURCE / "suite_wizard_receipt_host.py",
            SOURCE / "wizard_receipt_controller.py",
        ]
        sources = [path.read_text(encoding="utf-8") for path in paths]
        combined = "\n".join(sources)
        imported_roots: set[str] = set()
        for source in sources:
            tree = ast.parse(source)
            imported_roots.update(
                alias.name.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            )
            imported_roots.update(
                node.module.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module
            )

        self.assertIn('text="4. Receipt"', combined)
        self.assertIn("Export receipt…", combined)
        self.assertIn("Verify receipt…", combined)
        self.assertIn("publish_receipt", combined)
        self.assertIn("verify_published_receipt", combined)
        self.assertTrue(
            {"subprocess", "socket", "urllib", "requests", "ftplib"}.isdisjoint(
                imported_roots
            )
        )
        for forbidden in (
            "InstallerEngine",
            "install_button",
            "Start-Process",
            "Popen(",
            "urlopen",
            "upload(",
            "game_launch(",
            "runtime_execute(",
            "deploy(",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
