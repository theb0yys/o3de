#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Bounded receipt export and verification state for the Suite Wizard host."""

from __future__ import annotations

import sys
from pathlib import Path

from wizard_confirmation_controller import (
    WizardConfirmationController,
    WizardContractError,
    WizardHostError,
)

SUITE_WIZARD_ROOT = Path(__file__).resolve().parents[2]
RECEIPT_SOURCE = SUITE_WIZARD_ROOT / "Receipt" / "Source"
if str(RECEIPT_SOURCE) not in sys.path:
    sys.path.insert(0, str(RECEIPT_SOURCE))

from confirmation_receipt import (  # noqa: E402
    ReceiptError,
    load_receipt,
    publish_receipt,
    verify_published_receipt,
)


class WizardReceiptController(WizardConfirmationController):
    """Exports and re-verifies only the exact current review confirmation chain."""

    def __init__(self, installer_root: object) -> None:
        self._receipt_path: Path | None = None
        self._receipt_status: str | None = None
        self._receipt: dict[str, object] | None = None
        super().__init__(installer_root)

    @property
    def receipt_result(self) -> dict[str, object] | None:
        return self._receipt

    def invalidate_review(self) -> dict[str, object]:
        self._clear_receipt_state()
        return super().invalidate_review()

    def invalidate_confirmation(self) -> dict[str, object]:
        self._clear_receipt_state()
        return super().invalidate_confirmation()

    def set_package_included(self, package_id: str, included: bool) -> dict[str, object]:
        self._clear_receipt_state()
        return super().set_package_included(package_id, included)

    def set_feature_selected(self, feature_id: str, selected: bool) -> dict[str, object]:
        self._clear_receipt_state()
        return super().set_feature_selected(feature_id, selected)

    def set_context(
        self,
        *,
        platform: str,
        architecture: str,
        runtime_target: str,
        game_version: str = "",
        branch: str = "",
    ) -> dict[str, object]:
        self._clear_receipt_state()
        return super().set_context(
            platform=platform,
            architecture=architecture,
            runtime_target=runtime_target,
            game_version=game_version,
            branch=branch,
        )

    def set_acknowledgement(self, acknowledgement_id: str, acknowledged: bool) -> dict[str, object]:
        self._clear_receipt_state()
        return super().set_acknowledgement(acknowledgement_id, acknowledged)

    def resolve_review(self) -> dict[str, object]:
        self._clear_receipt_state()
        return super().resolve_review()

    def create_review_confirmation(
        self,
        *,
        expected_plan_sha256: str,
        expected_view_model_sha256: str,
        confirmed_by: str,
        confirmed_at_utc: str,
    ) -> dict[str, object]:
        self._clear_receipt_state()
        return super().create_review_confirmation(
            expected_plan_sha256=expected_plan_sha256,
            expected_view_model_sha256=expected_view_model_sha256,
            confirmed_by=confirmed_by,
            confirmed_at_utc=confirmed_at_utc,
        )

    def export_current_receipt(
        self,
        destination: Path,
        *,
        expected_plan_sha256: str,
        expected_view_model_sha256: str,
        expected_confirmation_sha256: str,
    ) -> dict[str, object]:
        """Reverify the displayed chain and atomically export its canonical receipt."""
        plan, view_model, confirmation = self._current_accepted_chain(
            expected_plan_sha256=expected_plan_sha256,
            expected_view_model_sha256=expected_view_model_sha256,
            expected_confirmation_sha256=expected_confirmation_sha256,
        )
        result = publish_receipt(Path(destination), plan, view_model, confirmation)
        receipt = verify_published_receipt(Path(destination), plan, view_model, confirmation)
        self._receipt_path = Path(destination)
        self._receipt_status = str(result["status"])
        self._receipt = receipt
        return self.receipt_snapshot()

    def verify_current_receipt(
        self,
        receipt_path: Path,
        *,
        expected_plan_sha256: str,
        expected_view_model_sha256: str,
        expected_confirmation_sha256: str,
    ) -> dict[str, object]:
        """Verify a canonical receipt against the exact current accepted chain."""
        plan, view_model, confirmation = self._current_accepted_chain(
            expected_plan_sha256=expected_plan_sha256,
            expected_view_model_sha256=expected_view_model_sha256,
            expected_confirmation_sha256=expected_confirmation_sha256,
        )
        receipt = verify_published_receipt(Path(receipt_path), plan, view_model, confirmation)
        self._receipt_path = Path(receipt_path)
        self._receipt_status = "verified"
        self._receipt = receipt
        return self.receipt_snapshot()

    def receipt_snapshot(self) -> dict[str, object]:
        if self._receipt is None or self._receipt_path is None or self._receipt_status is None:
            raise WizardHostError("Export or verify the current confirmation receipt first.")
        plan, view_model, confirmation = self._current_accepted_chain(
            expected_plan_sha256=str(self._receipt["plan_sha256"]),
            expected_view_model_sha256=str(self._receipt["view_model_sha256"]),
            expected_confirmation_sha256=str(self._receipt["confirmation_sha256"]),
        )
        verified = verify_published_receipt(
            self._receipt_path,
            plan,
            view_model,
            confirmation,
        )
        if verified != self._receipt:
            raise WizardHostError("The displayed receipt changed after verification.")
        authority = self._object(verified.get("authority"), "receipt.authority")
        return {
            "status": self._receipt_status,
            "path": str(self._receipt_path),
            "plan_sha256": verified["plan_sha256"],
            "view_model_sha256": verified["view_model_sha256"],
            "confirmation_sha256": verified["confirmation_sha256"],
            "receipt_sha256": verified["receipt_sha256"],
            "statement": verified["statement"],
            "size_bytes": len(self._receipt_path.read_bytes()),
            "authority": dict(authority),
            "current": True,
        }

    def receipt_state_snapshot(self) -> dict[str, object]:
        state = self.confirmation_state_snapshot()
        state["receipt_available"] = self._receipt is not None
        if self._receipt is not None:
            state["receipt"] = self.receipt_snapshot()
        return state

    def review_snapshot(self) -> dict[str, object]:
        snapshot = super().review_snapshot()
        snapshot["receipt_available"] = self._receipt is not None
        if self._receipt is not None:
            snapshot["receipt"] = self.receipt_snapshot()
        return snapshot

    def host_snapshot(self) -> dict[str, object]:
        snapshot = super().host_snapshot()
        snapshot["receipt_available"] = self._receipt is not None
        return snapshot

    def load_receipt_for_display(self, receipt_path: Path) -> dict[str, object]:
        """Load syntax and canonical form only; it does not make the receipt current."""
        loaded = load_receipt(Path(receipt_path))
        return {
            "path": str(receipt_path),
            "plan_sha256": loaded["plan_sha256"],
            "view_model_sha256": loaded["view_model_sha256"],
            "confirmation_sha256": loaded["confirmation_sha256"],
            "receipt_sha256": loaded["receipt_sha256"],
            "statement": loaded["statement"],
            "authority": dict(self._object(loaded.get("authority"), "receipt.authority")),
        }

    def _current_accepted_chain(
        self,
        *,
        expected_plan_sha256: str,
        expected_view_model_sha256: str,
        expected_confirmation_sha256: str,
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        result = self._current_result()
        plan = self._object(result.get("plan"), "result.plan")
        view_model = self._object(result.get("view_model"), "result.view_model")
        confirmation = self.confirmation_snapshot()
        if expected_plan_sha256 != plan.get("plan_sha256"):
            raise WizardHostError("The displayed plan fingerprint is stale; resolve again.")
        if expected_view_model_sha256 != view_model.get("view_model_sha256"):
            raise WizardHostError("The displayed view-model fingerprint is stale; resolve again.")
        if expected_confirmation_sha256 != confirmation.get("confirmation_sha256"):
            raise WizardHostError("The displayed confirmation fingerprint is stale; confirm again.")
        raw_confirmation = self._confirmation
        if not isinstance(raw_confirmation, dict):
            raise WizardHostError("Create the current review confirmation first.")
        return plan, view_model, dict(raw_confirmation)

    def _clear_confirmation_state(self, *, clear_acknowledgements: bool) -> None:
        self._clear_receipt_state()
        super()._clear_confirmation_state(clear_acknowledgements=clear_acknowledgements)

    def _clear_receipt_state(self) -> None:
        self._receipt_path = None
        self._receipt_status = None
        self._receipt = None


__all__ = [
    "ReceiptError",
    "WizardContractError",
    "WizardHostError",
    "WizardReceiptController",
]
