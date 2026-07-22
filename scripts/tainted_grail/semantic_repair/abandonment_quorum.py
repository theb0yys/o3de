"""Reviewer-quorum decisions for stranded locks without lock theft."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .abandonment import LockAbandonmentReview
from .errors import LockOwnershipError, RepairError
from .ownership import ExclusiveResourceLock


def _canonical(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


@dataclass(frozen=True)
class QuorumReviewReference:
    reviewer_id: str
    review_sha256: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "reviewer_id": self.reviewer_id,
            "review_sha256": self.review_sha256,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class LockAbandonmentDecision:
    resource_id: str
    observed_owner_id: str
    observed_generation: int
    lock_sha256: str
    generation_state_sha256: str
    required_quorum: int
    reviews: tuple[QuorumReviewReference, ...]

    def __post_init__(self) -> None:
        if type(self.required_quorum) is not int or self.required_quorum < 2:
            raise RepairError("abandonment decision quorum must be at least two")
        if len(self.reviews) < self.required_quorum:
            raise RepairError("abandonment decision does not meet reviewer quorum")
        reviewers = [review.reviewer_id for review in self.reviews]
        if reviewers != sorted(reviewers) or len(reviewers) != len(set(reviewers)):
            raise RepairError("abandonment decision reviewers must be unique and sorted")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-lock-abandonment-quorum-only",
            "runtime_authority": "none",
            "promotion": "none",
            "decision": "quorum-met-retain-lock",
            "recommended_action": "manual-review-no-lock-theft",
            "resource_id": self.resource_id,
            "observed_owner_id": self.observed_owner_id,
            "observed_generation": self.observed_generation,
            "lock_sha256": self.lock_sha256,
            "generation_state_sha256": self.generation_state_sha256,
            "required_quorum": self.required_quorum,
            "reviews": [review.to_dict() for review in self.reviews],
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()


def build_lock_abandonment_decision(
    reviews: Iterable[LockAbandonmentReview],
    *,
    required_quorum: int = 2,
) -> LockAbandonmentDecision:
    supplied = tuple(reviews)
    if not supplied:
        raise RepairError("abandonment decision requires reviews")
    first = supplied[0]
    observation = (
        first.resource_id,
        first.observed_owner_id,
        first.observed_generation,
        first.lock_sha256,
        first.generation_state_sha256,
    )
    for review in supplied:
        current = (
            review.resource_id,
            review.observed_owner_id,
            review.observed_generation,
            review.lock_sha256,
            review.generation_state_sha256,
        )
        if current != observation:
            raise RepairError("abandonment reviews do not describe one lock observation")
    refs = tuple(
        sorted(
            (
                QuorumReviewReference(review.reviewer_id, review.sha256, review.reason)
                for review in supplied
            ),
            key=lambda item: item.reviewer_id,
        )
    )
    return LockAbandonmentDecision(*observation, required_quorum, refs)


def verify_abandonment_decision_against_lock(
    lock: ExclusiveResourceLock,
    decision: LockAbandonmentDecision,
) -> bool:
    identity = lock.current_identity()
    if identity is None:
        raise LockOwnershipError("abandonment decision lock is no longer present")
    lock_sha = hashlib.sha256(lock.path.read_bytes()).hexdigest()
    if not lock.generation_path.exists():
        raise LockOwnershipError("abandonment decision generation state is absent")
    generation_sha = hashlib.sha256(lock.generation_path.read_bytes()).hexdigest()
    if (
        identity.resource_id != decision.resource_id
        or identity.owner_id != decision.observed_owner_id
        or identity.generation != decision.observed_generation
        or lock_sha != decision.lock_sha256
        or generation_sha != decision.generation_state_sha256
    ):
        raise LockOwnershipError("abandonment decision no longer matches the observed lock")
    return True
