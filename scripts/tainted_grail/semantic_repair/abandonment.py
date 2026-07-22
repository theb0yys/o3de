"""Canonical manual-review records for observed stranded resource leases."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import LockOwnershipError, RepairError
from .ownership import ExclusiveResourceLock, LeaseIdentity

_SCHEMA_VERSION = 1


def _canonical(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _nonempty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RepairError(f"{name} must be non-empty text")
    return value


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


@dataclass(frozen=True)
class LockAbandonmentReview:
    resource_id: str
    observed_owner_id: str
    observed_generation: int
    lock_sha256: str
    generation_state_sha256: str
    reviewer_id: str
    reason: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.resource_id, "resource_id"),
            (self.observed_owner_id, "observed_owner_id"),
            (self.reviewer_id, "reviewer_id"),
            (self.reason, "reason"),
        ):
            _nonempty(value, name)
        if type(self.observed_generation) is not int or self.observed_generation <= 0:
            raise RepairError("observed_generation must be a positive integer")
        if any(
            not isinstance(value, str) or len(value) != 64
            for value in (self.lock_sha256, self.generation_state_sha256)
        ):
            raise RepairError("abandonment review hashes must be SHA-256 values")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": _SCHEMA_VERSION,
            "authority": "synthetic-lock-abandonment-review-only",
            "runtime_authority": "none",
            "promotion": "none",
            "recommended_action": "manual-review-no-lock-theft",
            "resource_id": self.resource_id,
            "observed_owner_id": self.observed_owner_id,
            "observed_generation": self.observed_generation,
            "lock_sha256": self.lock_sha256,
            "generation_state_sha256": self.generation_state_sha256,
            "reviewer_id": self.reviewer_id,
            "reason": self.reason,
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()

    @classmethod
    def from_bytes(cls, data: bytes) -> "LockAbandonmentReview":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RepairError("invalid lock abandonment review") from exc
        expected = {
            "schema_version",
            "authority",
            "runtime_authority",
            "promotion",
            "recommended_action",
            "resource_id",
            "observed_owner_id",
            "observed_generation",
            "lock_sha256",
            "generation_state_sha256",
            "reviewer_id",
            "reason",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise RepairError("lock abandonment review has unexpected fields")
        if (
            doc["schema_version"] != _SCHEMA_VERSION
            or doc["authority"] != "synthetic-lock-abandonment-review-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
            or doc["recommended_action"] != "manual-review-no-lock-theft"
        ):
            raise RepairError("lock abandonment review boundary is invalid")
        return cls(
            doc["resource_id"],
            doc["observed_owner_id"],
            doc["observed_generation"],
            doc["lock_sha256"],
            doc["generation_state_sha256"],
            doc["reviewer_id"],
            doc["reason"],
        )


def build_lock_abandonment_review(
    lock: ExclusiveResourceLock,
    reviewer_id: str,
    reason: str,
) -> LockAbandonmentReview:
    identity: LeaseIdentity | None = lock.current_identity()
    if identity is None:
        raise LockOwnershipError("no active resource lease to review")
    lock_bytes = lock.path.read_bytes()
    if not lock.generation_path.exists():
        raise LockOwnershipError("lease generation state is absent")
    if lock.current_generation() != identity.generation:
        raise LockOwnershipError("lease and generation state disagree")
    generation_bytes = lock.generation_path.read_bytes()
    return LockAbandonmentReview(
        identity.resource_id,
        identity.owner_id,
        identity.generation,
        hashlib.sha256(lock_bytes).hexdigest(),
        hashlib.sha256(generation_bytes).hexdigest(),
        _nonempty(reviewer_id, "reviewer_id"),
        _nonempty(reason, "reason"),
    )


def write_lock_abandonment_review(
    review: LockAbandonmentReview,
    path: Path,
) -> Path:
    _atomic_write(Path(path), review.to_bytes())
    return Path(path)
