# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import ast
import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOST_SOURCE = REPO_ROOT / "Installer" / "SuiteWizard" / "Host" / "Source"
RECEIPT_SOURCE = REPO_ROOT / "Installer" / "SuiteWizard" / "Receipt" / "Source"
sys.path.insert(0, str(HOST_SOURCE))
sys.path.insert(0, str(RECEIPT_SOURCE))

from confirmation_receipt import (  # noqa: E402
    ReceiptError,
    build_receipt,
    canonical_receipt_bytes,
    load_receipt,
    publish_receipt,
    validate_receipt,
    verify_published_receipt,
)
from wizard_confirmation_controller import WizardConfirmationController  # noqa: E402
from wizard_view_model import WizardContractError  # noqa: E402

INSTALLER_ROOT = REPO_ROOT / "Installer"
CONFIRMED_BY = "FOA-SDK receipt tests"
CONFIRMED_AT = "2026-07-22T00:00:00Z"


class SuiteWizardReceiptTests(unittest.TestCase):
    def accepted_chain(self) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        controller = WizardConfirmationController(INSTALLER_ROOT)
        review = controller.resolve_review()
        for row in controller.acknowledgement_choices():
            controller.set_acknowledgement(str(row["acknowledgement_id"]), True)
        controller.create_review_confirmation(
            expected_plan_sha256=str(review["plan_sha256"]),
            expected_view_model_sha256=str(review["view_model_sha256"]),
            confirmed_by=CONFIRMED_BY,
            confirmed_at_utc=CONFIRMED_AT,
        )
        result = controller.review_result
        confirmation = controller.confirmation_result
        self.assertIsInstance(result, dict)
        self.assertIsInstance(confirmation, dict)
        assert isinstance(result, dict)
        assert isinstance(confirmation, dict)
        return dict(result["plan"]), dict(result["view_model"]), dict(confirmation)

    def test_receipt_is_deterministic_self_contained_and_non_executable(self) -> None:
        plan, view_model, confirmation = self.accepted_chain()
        first = build_receipt(plan, view_model, confirmation)
        second = build_receipt(plan, view_model, confirmation)
        self.assertEqual(first, second)
        self.assertEqual(canonical_receipt_bytes(first), canonical_receipt_bytes(second))
        self.assertEqual(first["plan_sha256"], plan["plan_sha256"])
        self.assertEqual(first["view_model_sha256"], view_model["view_model_sha256"])
        self.assertEqual(first["confirmation_sha256"], confirmation["confirmation_sha256"])
        self.assertEqual(len(first["receipt_sha256"]), 64)
        self.assertTrue(all(value is False for value in first["authority"].values()))
        self.assertEqual(validate_receipt(first), first)

    def test_publication_is_atomic_canonical_verified_and_idempotent(self) -> None:
        plan, view_model, confirmation = self.accepted_chain()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "accepted.foa-receipt.json"
            published = publish_receipt(destination, plan, view_model, confirmation)
            self.assertEqual(published["status"], "published")
            receipt = load_receipt(destination)
            self.assertEqual(destination.read_bytes(), canonical_receipt_bytes(receipt))
            self.assertEqual(
                verify_published_receipt(destination, plan, view_model, confirmation),
                receipt,
            )
            repeated = publish_receipt(destination, plan, view_model, confirmation)
            self.assertEqual(repeated["status"], "already-current")
            self.assertEqual(repeated["receipt_sha256"], receipt["receipt_sha256"])
            leftovers = list(Path(temporary).glob(".*.tmp"))
            self.assertEqual(leftovers, [])

    def test_existing_different_destination_is_never_overwritten(self) -> None:
        plan, view_model, confirmation = self.accepted_chain()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "accepted.foa-receipt.json"
            original = b"do-not-replace\n"
            destination.write_bytes(original)
            with self.assertRaisesRegex(ReceiptError, "different bytes"):
                publish_receipt(destination, plan, view_model, confirmation)
            self.assertEqual(destination.read_bytes(), original)

    def test_tampered_confirmation_fails_before_publication(self) -> None:
        plan, view_model, confirmation = self.accepted_chain()
        tampered = copy.deepcopy(confirmation)
        tampered["confirmed_by"] = "altered after confirmation"
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "rejected.foa-receipt.json"
            with self.assertRaises(WizardContractError):
                publish_receipt(destination, plan, view_model, tampered)
            self.assertFalse(destination.exists())

    def test_noncanonical_file_and_receipt_tampering_fail_closed(self) -> None:
        plan, view_model, confirmation = self.accepted_chain()
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "accepted.foa-receipt.json"
            publish_receipt(destination, plan, view_model, confirmation)
            document = json.loads(destination.read_text(encoding="utf-8"))
            destination.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ReceiptError, "not canonical JSON"):
                load_receipt(destination)

        receipt = build_receipt(plan, view_model, confirmation)
        altered = copy.deepcopy(receipt)
        altered["statement"] = "altered"
        with self.assertRaisesRegex(ReceiptError, "statement was altered"):
            validate_receipt(altered)

    def test_filename_and_symlink_boundaries_fail_closed(self) -> None:
        plan, view_model, confirmation = self.accepted_chain()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ReceiptError, "must end"):
                publish_receipt(root / "receipt.json", plan, view_model, confirmation)

            real = root / "real"
            real.mkdir()
            linked = root / "linked"
            try:
                linked.symlink_to(real, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symbolic links are unavailable on this platform.")
            with self.assertRaisesRegex(ReceiptError, "symbolic link"):
                publish_receipt(
                    linked / "accepted.foa-receipt.json",
                    plan,
                    view_model,
                    confirmation,
                )

    def test_receipt_source_has_no_network_or_execution_surface(self) -> None:
        source_path = RECEIPT_SOURCE / "confirmation_receipt.py"
        source = source_path.read_text(encoding="utf-8")
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
        self.assertTrue(
            {"subprocess", "socket", "urllib", "requests", "ftplib"}.isdisjoint(imported_roots)
        )
        for required in ("os.O_EXCL", "os.fsync", "os.link", "verify_confirmation"):
            self.assertIn(required, source)
        for forbidden in (
            "os.replace",
            "Popen(",
            "urlopen",
            "InstallerEngine",
            "game_launch(",
            "runtime_execute(",
            "upload(",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
