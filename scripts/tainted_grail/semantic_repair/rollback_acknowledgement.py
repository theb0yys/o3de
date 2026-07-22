"""Acknowledgement receipts for read-only publication-intent rollback plans."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .dependency_rollback import IntentPartialRollbackPlan
from .errors import PublicationIntentError

_ZERO_HASH = "0" * 64
_DISPOSITIONS = {
    "acknowledged-for-manual-execution-review",
    "declined-for-manual-execution-review",
}


def _canonical(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


@dataclass(frozen=True)
class IntentRollbackPlanAcknowledgementReceipt:
    acknowledgement_index: int
    previous_acknowledgement_sha256: str
    acknowledgement_id: str
    plan_sha256: str
    source_graph_sha256: str
    reviewer_id: str
    disposition: str
    action_count: int
    reason: str

    def __post_init__(self) -> None:
        if (
            type(self.acknowledgement_index) is not int
            or self.acknowledgement_index <= 0
        ):
            raise PublicationIntentError(
                "rollback acknowledgement index must be positive"
            )
        for value in (
            self.previous_acknowledgement_sha256,
            self.plan_sha256,
            self.source_graph_sha256,
        ):
            if not isinstance(value, str) or len(value) != 64:
                raise PublicationIntentError(
                    "rollback acknowledgement hash is invalid"
                )
        if (
            not isinstance(self.acknowledgement_id, str)
            or not self.acknowledgement_id.strip()
        ):
            raise PublicationIntentError(
                "rollback acknowledgement_id must be non-empty"
            )
        if not isinstance(self.reviewer_id, str) or not self.reviewer_id.strip():
            raise PublicationIntentError(
                "rollback acknowledgement reviewer_id must be non-empty"
            )
        if self.disposition not in _DISPOSITIONS:
            raise PublicationIntentError(
                "rollback acknowledgement disposition is unsupported"
            )
        if type(self.action_count) is not int or self.action_count <= 0:
            raise PublicationIntentError(
                "rollback acknowledgement action count must be positive"
            )
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise PublicationIntentError(
                "rollback acknowledgement reason must be non-empty"
            )

    @property
    def effect(self) -> str:
        return (
            "rollback-plan-acknowledged-no-execution"
            if self.disposition
            == "acknowledged-for-manual-execution-review"
            else "rollback-plan-declined-no-execution"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-publication-intent-rollback-acknowledgement-only",
            "runtime_authority": "none",
            "promotion": "none",
            "execution_authority": "none",
            "effect": self.effect,
            "acknowledgement_index": self.acknowledgement_index,
            "previous_acknowledgement_sha256": (
                self.previous_acknowledgement_sha256
            ),
            "acknowledgement_id": self.acknowledgement_id,
            "plan_sha256": self.plan_sha256,
            "source_graph_sha256": self.source_graph_sha256,
            "reviewer_id": self.reviewer_id,
            "disposition": self.disposition,
            "action_count": self.action_count,
            "reason": self.reason,
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
    ) -> "IntentRollbackPlanAcknowledgementReceipt":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PublicationIntentError(
                "invalid rollback acknowledgement receipt"
            ) from exc
        expected = {
            "schema_version",
            "authority",
            "runtime_authority",
            "promotion",
            "execution_authority",
            "effect",
            "acknowledgement_index",
            "previous_acknowledgement_sha256",
            "acknowledgement_id",
            "plan_sha256",
            "source_graph_sha256",
            "reviewer_id",
            "disposition",
            "action_count",
            "reason",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise PublicationIntentError(
                "rollback acknowledgement receipt has unexpected fields"
            )
        if (
            doc["schema_version"] != 1
            or doc["authority"]
            != "synthetic-publication-intent-rollback-acknowledgement-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
            or doc["execution_authority"] != "none"
        ):
            raise PublicationIntentError(
                "rollback acknowledgement boundary is invalid"
            )
        receipt = cls(
            doc["acknowledgement_index"],
            doc["previous_acknowledgement_sha256"],
            doc["acknowledgement_id"],
            doc["plan_sha256"],
            doc["source_graph_sha256"],
            doc["reviewer_id"],
            doc["disposition"],
            doc["action_count"],
            doc["reason"],
        )
        if doc["effect"] != receipt.effect:
            raise PublicationIntentError(
                "rollback acknowledgement effect mismatch"
            )
        return receipt


def build_intent_rollback_plan_acknowledgement(
    plan: IntentPartialRollbackPlan,
    reviewer_id: str,
    disposition: str,
    reason: str,
    *,
    acknowledgement_id: str,
    acknowledgement_index: int,
    previous_acknowledgement: (
        IntentRollbackPlanAcknowledgementReceipt | None
    ) = None,
) -> IntentRollbackPlanAcknowledgementReceipt:
    expected_index = (
        1
        if previous_acknowledgement is None
        else previous_acknowledgement.acknowledgement_index + 1
    )
    if acknowledgement_index != expected_index:
        raise PublicationIntentError(
            "rollback acknowledgement index is not contiguous"
        )
    if (
        previous_acknowledgement is not None
        and (
            previous_acknowledgement.plan_sha256 != plan.sha256
            or previous_acknowledgement.source_graph_sha256
            != plan.source_graph_sha256
        )
    ):
        raise PublicationIntentError(
            "rollback acknowledgement chain references another plan"
        )
    return IntentRollbackPlanAcknowledgementReceipt(
        acknowledgement_index,
        (
            previous_acknowledgement.sha256
            if previous_acknowledgement
            else _ZERO_HASH
        ),
        acknowledgement_id,
        plan.sha256,
        plan.source_graph_sha256,
        reviewer_id,
        disposition,
        len(plan.actions),
        reason,
    )


def verify_intent_rollback_plan_acknowledgement(
    plan: IntentPartialRollbackPlan,
    receipt: IntentRollbackPlanAcknowledgementReceipt,
    *,
    previous_acknowledgement: (
        IntentRollbackPlanAcknowledgementReceipt | None
    ) = None,
) -> bool:
    rebuilt = build_intent_rollback_plan_acknowledgement(
        plan,
        receipt.reviewer_id,
        receipt.disposition,
        receipt.reason,
        acknowledgement_id=receipt.acknowledgement_id,
        acknowledgement_index=receipt.acknowledgement_index,
        previous_acknowledgement=previous_acknowledgement,
    )
    if rebuilt != receipt:
        raise PublicationIntentError(
            "rollback acknowledgement receipt mismatch"
        )
    return True
