"""Immutable appeal records for lock-abandonment quorum lifecycle artifacts."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from .abandonment_lifecycle import (
    AbandonmentDecisionRevocation,
    AbandonmentDecisionSupersession,
)
from .abandonment_quorum import LockAbandonmentDecision
from .errors import RepairError


def _canonical(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


@dataclass(frozen=True)
class AbandonmentDecisionAppeal:
    appeal_id: str
    target_kind: str
    target_sha256: str
    resource_id: str
    observed_generation: int
    reviewers: tuple[str, ...]
    reason: str
    requested_outcome: str = "manual-reconsideration-no-lock-theft"

    def __post_init__(self) -> None:
        if not isinstance(self.appeal_id, str) or not self.appeal_id.strip():
            raise RepairError("abandonment appeal_id must be non-empty")
        if self.target_kind not in {"decision", "revocation", "supersession"}:
            raise RepairError("abandonment appeal target kind is unsupported")
        if len(self.target_sha256) != 64:
            raise RepairError("abandonment appeal target hash is invalid")
        if not isinstance(self.resource_id, str) or not self.resource_id.strip():
            raise RepairError("abandonment appeal resource_id must be non-empty")
        if type(self.observed_generation) is not int or self.observed_generation <= 0:
            raise RepairError("abandonment appeal generation must be positive")
        if (
            self.reviewers != tuple(sorted(self.reviewers))
            or len(self.reviewers) < 2
            or len(self.reviewers) != len(set(self.reviewers))
            or any(not isinstance(item, str) or not item.strip() for item in self.reviewers)
        ):
            raise RepairError("abandonment appeal reviewers must be distinct, sorted, and meet quorum")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise RepairError("abandonment appeal reason must be non-empty")
        if self.requested_outcome != "manual-reconsideration-no-lock-theft":
            raise RepairError("abandonment appeal outcome is unsupported")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-lock-abandonment-appeal-only",
            "runtime_authority": "none",
            "promotion": "none",
            "effect": "appeal-recorded-lock-retained",
            "appeal_id": self.appeal_id,
            "target_kind": self.target_kind,
            "target_sha256": self.target_sha256,
            "resource_id": self.resource_id,
            "observed_generation": self.observed_generation,
            "reviewers": list(self.reviewers),
            "reason": self.reason,
            "requested_outcome": self.requested_outcome,
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()

    @classmethod
    def from_bytes(cls, data: bytes) -> "AbandonmentDecisionAppeal":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RepairError("invalid abandonment appeal") from exc
        expected = {
            "schema_version", "authority", "runtime_authority", "promotion",
            "effect", "appeal_id", "target_kind", "target_sha256",
            "resource_id", "observed_generation", "reviewers", "reason",
            "requested_outcome",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise RepairError("abandonment appeal has unexpected fields")
        if (
            doc["schema_version"] != 1
            or doc["authority"] != "synthetic-lock-abandonment-appeal-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
            or doc["effect"] != "appeal-recorded-lock-retained"
            or not isinstance(doc["reviewers"], list)
        ):
            raise RepairError("abandonment appeal boundary is invalid")
        return cls(
            doc["appeal_id"],
            doc["target_kind"],
            doc["target_sha256"],
            doc["resource_id"],
            doc["observed_generation"],
            tuple(doc["reviewers"]),
            doc["reason"],
            doc["requested_outcome"],
        )


def _target_identity(
    target: LockAbandonmentDecision
    | AbandonmentDecisionRevocation
    | AbandonmentDecisionSupersession,
) -> tuple[str, str, str, int]:
    if isinstance(target, LockAbandonmentDecision):
        return "decision", target.sha256, target.resource_id, target.observed_generation
    if isinstance(target, AbandonmentDecisionRevocation):
        return "revocation", target.sha256, target.resource_id, target.observed_generation
    if isinstance(target, AbandonmentDecisionSupersession):
        return "supersession", target.sha256, target.resource_id, target.replacement_generation
    raise RepairError("abandonment appeal target is unsupported")


def build_abandonment_decision_appeal(
    target: LockAbandonmentDecision
    | AbandonmentDecisionRevocation
    | AbandonmentDecisionSupersession,
    reviewers: Iterable[str],
    reason: str,
    *,
    appeal_id: str,
) -> AbandonmentDecisionAppeal:
    kind, target_sha, resource_id, generation = _target_identity(target)
    return AbandonmentDecisionAppeal(
        appeal_id,
        kind,
        target_sha,
        resource_id,
        generation,
        tuple(sorted(tuple(reviewers))),
        reason,
    )


def verify_abandonment_decision_appeal(
    target: LockAbandonmentDecision
    | AbandonmentDecisionRevocation
    | AbandonmentDecisionSupersession,
    appeal: AbandonmentDecisionAppeal,
) -> bool:
    rebuilt = build_abandonment_decision_appeal(
        target,
        appeal.reviewers,
        appeal.reason,
        appeal_id=appeal.appeal_id,
    )
    if rebuilt != appeal:
        raise RepairError("abandonment appeal does not match target")
    return True
