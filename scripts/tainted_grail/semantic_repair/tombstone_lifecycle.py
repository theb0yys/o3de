"""Supersession and restoration-review records for archive tombstones."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from .archive_retention import CheckpointArchiveTombstoneManifest
from .errors import CheckpointProofError


def _canonical(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _reviewers(values: Iterable[str]) -> tuple[str, ...]:
    reviewers = tuple(sorted(tuple(values)))
    if (
        len(reviewers) < 2
        or len(reviewers) != len(set(reviewers))
        or any(not isinstance(value, str) or not value.strip() for value in reviewers)
    ):
        raise CheckpointProofError(
            "archive tombstone lifecycle reviewers must be distinct and meet quorum"
        )
    return reviewers


@dataclass(frozen=True)
class ArchiveTombstoneSupersessionRecord:
    previous_tombstone_sha256: str
    replacement_tombstone_sha256: str
    archive_id: str
    archive_index: int
    archive_sha256: str
    archive_manifest_sha256: str
    previous_tombstone_index: int
    replacement_tombstone_index: int
    reviewers: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        for value in (
            self.previous_tombstone_sha256,
            self.replacement_tombstone_sha256,
            self.archive_sha256,
            self.archive_manifest_sha256,
        ):
            if not isinstance(value, str) or len(value) != 64:
                raise CheckpointProofError("archive tombstone supersession hash is invalid")
        if not isinstance(self.archive_id, str) or not self.archive_id.strip():
            raise CheckpointProofError(
                "archive tombstone supersession archive_id must be non-empty"
            )
        if type(self.archive_index) is not int or self.archive_index <= 0:
            raise CheckpointProofError(
                "archive tombstone supersession archive index must be positive"
            )
        if (
            type(self.previous_tombstone_index) is not int
            or type(self.replacement_tombstone_index) is not int
            or self.previous_tombstone_index <= 0
            or self.replacement_tombstone_index <= self.previous_tombstone_index
        ):
            raise CheckpointProofError(
                "archive tombstone supersession indices are invalid"
            )
        _reviewers(self.reviewers)
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise CheckpointProofError(
                "archive tombstone supersession reason must be non-empty"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-checkpoint-archive-tombstone-supersession-only",
            "runtime_authority": "none",
            "promotion": "none",
            "effect": "tombstone-superseded-no-archive-mutation",
            "previous_tombstone_sha256": self.previous_tombstone_sha256,
            "replacement_tombstone_sha256": self.replacement_tombstone_sha256,
            "archive_id": self.archive_id,
            "archive_index": self.archive_index,
            "archive_sha256": self.archive_sha256,
            "archive_manifest_sha256": self.archive_manifest_sha256,
            "previous_tombstone_index": self.previous_tombstone_index,
            "replacement_tombstone_index": self.replacement_tombstone_index,
            "reviewers": list(self.reviewers),
            "reason": self.reason,
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return _sha(self.to_bytes())

    @classmethod
    def from_bytes(cls, data: bytes) -> "ArchiveTombstoneSupersessionRecord":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CheckpointProofError(
                "invalid archive tombstone supersession record"
            ) from exc
        expected = {
            "schema_version",
            "authority",
            "runtime_authority",
            "promotion",
            "effect",
            "previous_tombstone_sha256",
            "replacement_tombstone_sha256",
            "archive_id",
            "archive_index",
            "archive_sha256",
            "archive_manifest_sha256",
            "previous_tombstone_index",
            "replacement_tombstone_index",
            "reviewers",
            "reason",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise CheckpointProofError(
                "archive tombstone supersession record has unexpected fields"
            )
        if (
            doc["schema_version"] != 1
            or doc["authority"]
            != "synthetic-checkpoint-archive-tombstone-supersession-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
            or doc["effect"] != "tombstone-superseded-no-archive-mutation"
            or not isinstance(doc["reviewers"], list)
        ):
            raise CheckpointProofError(
                "archive tombstone supersession boundary is invalid"
            )
        return cls(
            doc["previous_tombstone_sha256"],
            doc["replacement_tombstone_sha256"],
            doc["archive_id"],
            doc["archive_index"],
            doc["archive_sha256"],
            doc["archive_manifest_sha256"],
            doc["previous_tombstone_index"],
            doc["replacement_tombstone_index"],
            tuple(doc["reviewers"]),
            doc["reason"],
        )


@dataclass(frozen=True)
class ArchiveRestorationReviewRecord:
    review_id: str
    target_kind: str
    target_sha256: str
    archive_id: str
    archive_index: int
    archive_sha256: str
    archive_manifest_sha256: str
    reviewers: tuple[str, ...]
    reason: str
    requested_outcome: str = "manual-restoration-review-no-file-mutation"

    def __post_init__(self) -> None:
        if not isinstance(self.review_id, str) or not self.review_id.strip():
            raise CheckpointProofError(
                "archive restoration review_id must be non-empty"
            )
        if self.target_kind not in {"tombstone", "supersession"}:
            raise CheckpointProofError(
                "archive restoration review target kind is unsupported"
            )
        for value in (
            self.target_sha256,
            self.archive_sha256,
            self.archive_manifest_sha256,
        ):
            if not isinstance(value, str) or len(value) != 64:
                raise CheckpointProofError(
                    "archive restoration review hash is invalid"
                )
        if not isinstance(self.archive_id, str) or not self.archive_id.strip():
            raise CheckpointProofError(
                "archive restoration review archive_id must be non-empty"
            )
        if type(self.archive_index) is not int or self.archive_index <= 0:
            raise CheckpointProofError(
                "archive restoration review archive index must be positive"
            )
        _reviewers(self.reviewers)
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise CheckpointProofError(
                "archive restoration review reason must be non-empty"
            )
        if (
            self.requested_outcome
            != "manual-restoration-review-no-file-mutation"
        ):
            raise CheckpointProofError(
                "archive restoration review outcome is unsupported"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-checkpoint-archive-restoration-review-only",
            "runtime_authority": "none",
            "promotion": "none",
            "effect": "restoration-review-recorded-no-archive-mutation",
            "review_id": self.review_id,
            "target_kind": self.target_kind,
            "target_sha256": self.target_sha256,
            "archive_id": self.archive_id,
            "archive_index": self.archive_index,
            "archive_sha256": self.archive_sha256,
            "archive_manifest_sha256": self.archive_manifest_sha256,
            "reviewers": list(self.reviewers),
            "reason": self.reason,
            "requested_outcome": self.requested_outcome,
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return _sha(self.to_bytes())

    @classmethod
    def from_bytes(cls, data: bytes) -> "ArchiveRestorationReviewRecord":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CheckpointProofError(
                "invalid archive restoration review record"
            ) from exc
        expected = {
            "schema_version",
            "authority",
            "runtime_authority",
            "promotion",
            "effect",
            "review_id",
            "target_kind",
            "target_sha256",
            "archive_id",
            "archive_index",
            "archive_sha256",
            "archive_manifest_sha256",
            "reviewers",
            "reason",
            "requested_outcome",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise CheckpointProofError(
                "archive restoration review record has unexpected fields"
            )
        if (
            doc["schema_version"] != 1
            or doc["authority"]
            != "synthetic-checkpoint-archive-restoration-review-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
            or doc["effect"]
            != "restoration-review-recorded-no-archive-mutation"
            or not isinstance(doc["reviewers"], list)
        ):
            raise CheckpointProofError(
                "archive restoration review boundary is invalid"
            )
        return cls(
            doc["review_id"],
            doc["target_kind"],
            doc["target_sha256"],
            doc["archive_id"],
            doc["archive_index"],
            doc["archive_sha256"],
            doc["archive_manifest_sha256"],
            tuple(doc["reviewers"]),
            doc["reason"],
            doc["requested_outcome"],
        )


def build_archive_tombstone_supersession(
    previous: CheckpointArchiveTombstoneManifest,
    replacement: CheckpointArchiveTombstoneManifest,
    reviewers: Iterable[str],
    reason: str,
) -> ArchiveTombstoneSupersessionRecord:
    previous_identity = (
        previous.archive_id,
        previous.archive_index,
        previous.archive_sha256,
        previous.archive_manifest_sha256,
    )
    replacement_identity = (
        replacement.archive_id,
        replacement.archive_index,
        replacement.archive_sha256,
        replacement.archive_manifest_sha256,
    )
    if previous_identity != replacement_identity:
        raise CheckpointProofError(
            "archive tombstone supersession crosses archive identity"
        )
    if replacement.previous_tombstone_sha256 != previous.sha256:
        raise CheckpointProofError(
            "replacement tombstone does not chain from previous tombstone"
        )
    return ArchiveTombstoneSupersessionRecord(
        previous.sha256,
        replacement.sha256,
        previous.archive_id,
        previous.archive_index,
        previous.archive_sha256,
        previous.archive_manifest_sha256,
        previous.tombstone_index,
        replacement.tombstone_index,
        _reviewers(reviewers),
        reason,
    )


def verify_archive_tombstone_supersession(
    previous: CheckpointArchiveTombstoneManifest,
    replacement: CheckpointArchiveTombstoneManifest,
    record: ArchiveTombstoneSupersessionRecord,
) -> bool:
    rebuilt = build_archive_tombstone_supersession(
        previous,
        replacement,
        record.reviewers,
        record.reason,
    )
    if rebuilt != record:
        raise CheckpointProofError(
            "archive tombstone supersession record mismatch"
        )
    return True


def _restoration_target(
    target: CheckpointArchiveTombstoneManifest
    | ArchiveTombstoneSupersessionRecord,
) -> tuple[str, str, str, int, str, str]:
    if isinstance(target, CheckpointArchiveTombstoneManifest):
        return (
            "tombstone",
            target.sha256,
            target.archive_id,
            target.archive_index,
            target.archive_sha256,
            target.archive_manifest_sha256,
        )
    if isinstance(target, ArchiveTombstoneSupersessionRecord):
        return (
            "supersession",
            target.sha256,
            target.archive_id,
            target.archive_index,
            target.archive_sha256,
            target.archive_manifest_sha256,
        )
    raise CheckpointProofError(
        "archive restoration review target is unsupported"
    )


def build_archive_restoration_review(
    target: CheckpointArchiveTombstoneManifest
    | ArchiveTombstoneSupersessionRecord,
    reviewers: Iterable[str],
    reason: str,
    *,
    review_id: str,
) -> ArchiveRestorationReviewRecord:
    kind, target_sha, archive_id, archive_index, archive_sha, manifest_sha = (
        _restoration_target(target)
    )
    return ArchiveRestorationReviewRecord(
        review_id,
        kind,
        target_sha,
        archive_id,
        archive_index,
        archive_sha,
        manifest_sha,
        _reviewers(reviewers),
        reason,
    )


def verify_archive_restoration_review(
    target: CheckpointArchiveTombstoneManifest
    | ArchiveTombstoneSupersessionRecord,
    review: ArchiveRestorationReviewRecord,
) -> bool:
    rebuilt = build_archive_restoration_review(
        target,
        review.reviewers,
        review.reason,
        review_id=review.review_id,
    )
    if rebuilt != review:
        raise CheckpointProofError(
            "archive restoration review record mismatch"
        )
    return True
