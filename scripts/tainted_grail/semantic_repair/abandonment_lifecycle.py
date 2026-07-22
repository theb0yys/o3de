"""Immutable revocation and supersession records for quorum abandonment decisions."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from .abandonment_quorum import LockAbandonmentDecision
from .errors import RepairError


def _canonical(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _reviewers(values: Iterable[str], *, minimum: int) -> tuple[str, ...]:
    supplied = tuple(values)
    if any(
        not isinstance(value, str) or not value.strip()
        for value in supplied
    ):
        raise RepairError(
            "abandonment lifecycle reviewer IDs must be non-empty"
        )
    reviewers = tuple(sorted(supplied))
    if (
        len(reviewers) < minimum
        or len(reviewers) != len(set(reviewers))
    ):
        raise RepairError(
            "abandonment lifecycle reviewers must be distinct and meet quorum"
        )
    return reviewers


@dataclass(frozen=True)
class AbandonmentDecisionRevocation:
    decision_sha256: str
    resource_id: str
    observed_owner_id: str
    observed_generation: int
    reviewers: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if len(self.decision_sha256) != 64:
            raise RepairError("revoked decision hash is invalid")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise RepairError("revocation reason must be non-empty")
        _reviewers(self.reviewers, minimum=2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-lock-abandonment-revocation-only",
            "runtime_authority": "none",
            "promotion": "none",
            "effect": "decision-revoked-lock-retained",
            "decision_sha256": self.decision_sha256,
            "resource_id": self.resource_id,
            "observed_owner_id": self.observed_owner_id,
            "observed_generation": self.observed_generation,
            "reviewers": list(self.reviewers),
            "reason": self.reason,
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()


@dataclass(frozen=True)
class AbandonmentDecisionSupersession:
    previous_decision_sha256: str
    revocation_sha256: str
    replacement_decision_sha256: str
    resource_id: str
    previous_generation: int
    replacement_generation: int
    reviewers: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if any(
            len(value) != 64
            for value in (
                self.previous_decision_sha256,
                self.revocation_sha256,
                self.replacement_decision_sha256,
            )
        ):
            raise RepairError("supersession hash is invalid")
        if self.replacement_generation < self.previous_generation:
            raise RepairError(
                "supersession cannot move to an older lock generation"
            )
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise RepairError("supersession reason must be non-empty")
        _reviewers(self.reviewers, minimum=2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-lock-abandonment-supersession-only",
            "runtime_authority": "none",
            "promotion": "none",
            "effect": "decision-superseded-lock-retained",
            "previous_decision_sha256": self.previous_decision_sha256,
            "revocation_sha256": self.revocation_sha256,
            "replacement_decision_sha256": self.replacement_decision_sha256,
            "resource_id": self.resource_id,
            "previous_generation": self.previous_generation,
            "replacement_generation": self.replacement_generation,
            "reviewers": list(self.reviewers),
            "reason": self.reason,
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()


def revoke_abandonment_decision(
    decision: LockAbandonmentDecision,
    reviewers: Iterable[str],
    reason: str,
) -> AbandonmentDecisionRevocation:
    supplied = _reviewers(
        reviewers,
        minimum=decision.required_quorum,
    )
    return AbandonmentDecisionRevocation(
        decision.sha256,
        decision.resource_id,
        decision.observed_owner_id,
        decision.observed_generation,
        supplied,
        reason,
    )


def supersede_abandonment_decision(
    previous: LockAbandonmentDecision,
    replacement: LockAbandonmentDecision,
    revocation: AbandonmentDecisionRevocation,
    reviewers: Iterable[str],
    reason: str,
) -> AbandonmentDecisionSupersession:
    if revocation.decision_sha256 != previous.sha256:
        raise RepairError(
            "supersession revocation does not reference previous decision"
        )
    if previous.resource_id != replacement.resource_id:
        raise RepairError(
            "supersession decisions target different resources"
        )
    if previous.sha256 == replacement.sha256:
        raise RepairError(
            "supersession requires a distinct replacement decision"
        )
    supplied = _reviewers(
        reviewers,
        minimum=max(
            previous.required_quorum,
            replacement.required_quorum,
        ),
    )
    return AbandonmentDecisionSupersession(
        previous.sha256,
        revocation.sha256,
        replacement.sha256,
        previous.resource_id,
        previous.observed_generation,
        replacement.observed_generation,
        supplied,
        reason,
    )
