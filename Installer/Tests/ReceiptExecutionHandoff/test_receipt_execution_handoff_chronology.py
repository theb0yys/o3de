# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HANDOFF_SOURCE = (
    REPO_ROOT
    / "Installer"
    / "Bootstrapper"
    / "ExecutionHandoff"
    / "Source"
)
RECEIPT_SOURCE = REPO_ROOT / "Installer" / "SuiteWizard" / "Receipt" / "Source"
HOST_SOURCE = REPO_ROOT / "Installer" / "SuiteWizard" / "Host" / "Source"
VIEW_MODEL_SOURCE = REPO_ROOT / "Installer" / "SuiteWizard" / "ViewModel" / "Source"
for source_root in (
    HANDOFF_SOURCE,
    RECEIPT_SOURCE,
    HOST_SOURCE,
    VIEW_MODEL_SOURCE,
):
    sys.path.insert(0, str(source_root))

from confirmation_receipt import build_receipt  # noqa: E402
from receipt_execution_handoff import (  # noqa: E402
    ExecutionHandoffError,
    build_handoff,
)
from wizard_confirmation_controller import WizardConfirmationController  # noqa: E402

INSTALLER_ROOT = REPO_ROOT / "Installer"


class ReceiptExecutionHandoffChronologyTests(unittest.TestCase):
    def accepted_receipt(self) -> dict[str, object]:
        controller = WizardConfirmationController(INSTALLER_ROOT)
        review = controller.resolve_review()
        for row in controller.acknowledgement_choices():
            controller.set_acknowledgement(
                str(row["acknowledgement_id"]),
                True,
            )
        controller.create_review_confirmation(
            expected_plan_sha256=str(review["plan_sha256"]),
            expected_view_model_sha256=str(review["view_model_sha256"]),
            confirmed_by="FOA-SDK chronology confirmation",
            confirmed_at_utc="2026-07-22T12:00:00Z",
        )
        result = controller.review_result
        confirmation = controller.confirmation_result
        self.assertIsInstance(result, dict)
        self.assertIsInstance(confirmation, dict)
        assert isinstance(result, dict)
        assert isinstance(confirmation, dict)
        return build_receipt(
            dict(result["plan"]),
            dict(result["view_model"]),
            dict(confirmation),
        )

    def test_request_time_cannot_precede_embedded_confirmation(self) -> None:
        receipt = self.accepted_receipt()
        with self.assertRaisesRegex(
            ExecutionHandoffError,
            "must not precede the embedded confirmation time",
        ):
            build_handoff(
                receipt,
                operation="install",
                target_reference="installation.foa-sdk.default",
                prior_installation_reference=None,
                requested_by="FOA-SDK chronology requester",
                requested_at_utc="2026-07-22T11:59:59Z",
            )

        handoff = build_handoff(
            receipt,
            operation="install",
            target_reference="installation.foa-sdk.default",
            prior_installation_reference=None,
            requested_by="FOA-SDK chronology requester",
            requested_at_utc="2026-07-22T12:00:00Z",
        )
        self.assertEqual(handoff["requested_at_utc"], "2026-07-22T12:00:00Z")


if __name__ == "__main__":
    unittest.main()
