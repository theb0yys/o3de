"""Withdrawal, resolution, and immutable histories for abandonment appeals."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from .abandonment_appeal import AbandonmentDecisionAppeal
from .errors import RepairError

_ZERO_HASH = "0" * 64
_OUTCOMES = {
    "upheld-manual-review",
    "denied-manual-review",
    "superseded-manual-review",
    "closed-withdrawn",
}


def _canonical(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _reviewers(values: Iterable[str]) -> tuple[str, ...]:
    reviewers = tuple(sorted(tuple(values)))
    if len(reviewers) < 2 or len(reviewers) != len(set(reviewers)) or any(not isinstance(v, str) or not v.strip() for v in reviewers):
        raise RepairError("abandonment appeal history reviewers must be distinct and meet quorum")
    return reviewers


def _load(data: bytes, expected: set[str], authority: str, effect: str | None = None) -> dict[str, Any]:
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RepairError("invalid abandonment appeal history artifact") from exc
    if not isinstance(doc, dict) or set(doc) != expected:
        raise RepairError("abandonment appeal history artifact has unexpected fields")
    if doc["schema_version"] != 1 or doc["authority"] != authority or doc["runtime_authority"] != "none" or doc["promotion"] != "none":
        raise RepairError("abandonment appeal history boundary is invalid")
    if effect is not None and doc["effect"] != effect:
        raise RepairError("abandonment appeal history effect is invalid")
    return doc


@dataclass(frozen=True)
class AbandonmentAppealWithdrawalRecord:
    appeal_sha256: str
    appeal_id: str
    resource_id: str
    observed_generation: int
    reviewers: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if len(self.appeal_sha256) != 64 or not self.appeal_id.strip() or not self.resource_id.strip() or type(self.observed_generation) is not int or self.observed_generation <= 0 or not self.reason.strip():
            raise RepairError("appeal withdrawal boundary is invalid")
        _reviewers(self.reviewers)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-lock-abandonment-appeal-withdrawal-only",
            "runtime_authority": "none",
            "promotion": "none",
            "effect": "appeal-withdrawn-lock-retained",
            "appeal_sha256": self.appeal_sha256,
            "appeal_id": self.appeal_id,
            "resource_id": self.resource_id,
            "observed_generation": self.observed_generation,
            "reviewers": list(self.reviewers),
            "reason": self.reason,
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return _sha(self.to_bytes())

    @classmethod
    def from_bytes(cls, data: bytes) -> "AbandonmentAppealWithdrawalRecord":
        doc = _load(data, {"schema_version", "authority", "runtime_authority", "promotion", "effect", "appeal_sha256", "appeal_id", "resource_id", "observed_generation", "reviewers", "reason"}, "synthetic-lock-abandonment-appeal-withdrawal-only", "appeal-withdrawn-lock-retained")
        if not isinstance(doc["reviewers"], list):
            raise RepairError("appeal withdrawal reviewers are invalid")
        return cls(doc["appeal_sha256"], doc["appeal_id"], doc["resource_id"], doc["observed_generation"], tuple(doc["reviewers"]), doc["reason"])


@dataclass(frozen=True)
class AbandonmentAppealResolutionRecord:
    appeal_sha256: str
    appeal_id: str
    resource_id: str
    observed_generation: int
    withdrawal_sha256: str
    outcome: str
    reviewers: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if len(self.appeal_sha256) != 64 or len(self.withdrawal_sha256) != 64 or not self.appeal_id.strip() or not self.resource_id.strip() or type(self.observed_generation) is not int or self.observed_generation <= 0 or self.outcome not in _OUTCOMES or not self.reason.strip():
            raise RepairError("appeal resolution boundary is invalid")
        _reviewers(self.reviewers)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-lock-abandonment-appeal-resolution-only",
            "runtime_authority": "none",
            "promotion": "none",
            "effect": "appeal-resolved-lock-retained",
            "appeal_sha256": self.appeal_sha256,
            "appeal_id": self.appeal_id,
            "resource_id": self.resource_id,
            "observed_generation": self.observed_generation,
            "withdrawal_sha256": self.withdrawal_sha256,
            "outcome": self.outcome,
            "reviewers": list(self.reviewers),
            "reason": self.reason,
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return _sha(self.to_bytes())

    @classmethod
    def from_bytes(cls, data: bytes) -> "AbandonmentAppealResolutionRecord":
        doc = _load(data, {"schema_version", "authority", "runtime_authority", "promotion", "effect", "appeal_sha256", "appeal_id", "resource_id", "observed_generation", "withdrawal_sha256", "outcome", "reviewers", "reason"}, "synthetic-lock-abandonment-appeal-resolution-only", "appeal-resolved-lock-retained")
        if not isinstance(doc["reviewers"], list):
            raise RepairError("appeal resolution reviewers are invalid")
        return cls(doc["appeal_sha256"], doc["appeal_id"], doc["resource_id"], doc["observed_generation"], doc["withdrawal_sha256"], doc["outcome"], tuple(doc["reviewers"]), doc["reason"])


@dataclass(frozen=True)
class AbandonmentAppealHistoryEntry:
    index: int
    previous_entry_sha256: str
    event_kind: str
    event_sha256: str
    outcome: str
    entry_sha256: str

    def __post_init__(self) -> None:
        if type(self.index) is not int or self.index <= 0 or self.event_kind not in {"withdrawal", "resolution"} or any(len(v) != 64 for v in (self.previous_entry_sha256, self.event_sha256, self.entry_sha256)):
            raise RepairError("appeal history entry boundary is invalid")
        if _sha(_canonical(self.core_dict())) != self.entry_sha256:
            raise RepairError("appeal history entry hash mismatch")

    def core_dict(self) -> dict[str, Any]:
        return {"schema_version": 1, "index": self.index, "previous_entry_sha256": self.previous_entry_sha256, "event_kind": self.event_kind, "event_sha256": self.event_sha256, "outcome": self.outcome}

    def to_dict(self) -> dict[str, Any]:
        return {**self.core_dict(), "entry_sha256": self.entry_sha256}

    @classmethod
    def build(cls, index: int, previous: str, kind: str, event_sha: str, outcome: str) -> "AbandonmentAppealHistoryEntry":
        core = {"schema_version": 1, "index": index, "previous_entry_sha256": previous, "event_kind": kind, "event_sha256": event_sha, "outcome": outcome}
        return cls(index, previous, kind, event_sha, outcome, _sha(_canonical(core)))

    @classmethod
    def from_dict(cls, doc: Any) -> "AbandonmentAppealHistoryEntry":
        expected = {"schema_version", "index", "previous_entry_sha256", "event_kind", "event_sha256", "outcome", "entry_sha256"}
        if not isinstance(doc, dict) or set(doc) != expected or doc["schema_version"] != 1:
            raise RepairError("appeal history entry is invalid")
        return cls(doc["index"], doc["previous_entry_sha256"], doc["event_kind"], doc["event_sha256"], doc["outcome"], doc["entry_sha256"])


@dataclass(frozen=True)
class AbandonmentAppealLifecycleHistory:
    appeal_sha256: str
    appeal_id: str
    resource_id: str
    observed_generation: int
    entries: tuple[AbandonmentAppealHistoryEntry, ...]

    def __post_init__(self) -> None:
        if len(self.appeal_sha256) != 64 or not self.entries:
            raise RepairError("appeal lifecycle history boundary is invalid")
        previous = _ZERO_HASH
        for index, entry in enumerate(self.entries, 1):
            if entry.index != index or entry.previous_entry_sha256 != previous:
                raise RepairError("appeal lifecycle history chain is invalid")
            previous = entry.entry_sha256
        kinds = tuple(entry.event_kind for entry in self.entries)
        if kinds not in {("withdrawal",), ("resolution",), ("withdrawal", "resolution")}:
            raise RepairError("appeal lifecycle history ordering is invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-lock-abandonment-appeal-history-only",
            "runtime_authority": "none",
            "promotion": "none",
            "lock_mutation_authority": "none",
            "appeal_sha256": self.appeal_sha256,
            "appeal_id": self.appeal_id,
            "resource_id": self.resource_id,
            "observed_generation": self.observed_generation,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return _sha(self.to_bytes())

    @classmethod
    def from_bytes(cls, data: bytes) -> "AbandonmentAppealLifecycleHistory":
        doc = _load(data, {"schema_version", "authority", "runtime_authority", "promotion", "lock_mutation_authority", "appeal_sha256", "appeal_id", "resource_id", "observed_generation", "entries"}, "synthetic-lock-abandonment-appeal-history-only")
        if doc["lock_mutation_authority"] != "none" or not isinstance(doc["entries"], list):
            raise RepairError("appeal lifecycle history boundary is invalid")
        return cls(doc["appeal_sha256"], doc["appeal_id"], doc["resource_id"], doc["observed_generation"], tuple(AbandonmentAppealHistoryEntry.from_dict(item) for item in doc["entries"]))


def build_abandonment_appeal_withdrawal(appeal: AbandonmentDecisionAppeal, reviewers: Iterable[str], reason: str) -> AbandonmentAppealWithdrawalRecord:
    return AbandonmentAppealWithdrawalRecord(appeal.sha256, appeal.appeal_id, appeal.resource_id, appeal.observed_generation, _reviewers(reviewers), reason)


def build_abandonment_appeal_resolution(appeal: AbandonmentDecisionAppeal, reviewers: Iterable[str], outcome: str, reason: str, *, withdrawal: AbandonmentAppealWithdrawalRecord | None = None) -> AbandonmentAppealResolutionRecord:
    if withdrawal is not None:
        if withdrawal.appeal_sha256 != appeal.sha256 or withdrawal.appeal_id != appeal.appeal_id:
            raise RepairError("appeal resolution withdrawal references another appeal")
        if outcome != "closed-withdrawn":
            raise RepairError("withdrawn appeal must resolve as closed-withdrawn")
    elif outcome == "closed-withdrawn":
        raise RepairError("closed-withdrawn resolution requires a withdrawal record")
    return AbandonmentAppealResolutionRecord(appeal.sha256, appeal.appeal_id, appeal.resource_id, appeal.observed_generation, withdrawal.sha256 if withdrawal else _ZERO_HASH, outcome, _reviewers(reviewers), reason)


def build_abandonment_appeal_lifecycle_history(appeal: AbandonmentDecisionAppeal, *, withdrawal: AbandonmentAppealWithdrawalRecord | None = None, resolution: AbandonmentAppealResolutionRecord | None = None) -> AbandonmentAppealLifecycleHistory:
    if withdrawal is None and resolution is None:
        raise RepairError("appeal lifecycle history requires an event")
    for event in (withdrawal, resolution):
        if event is not None and (event.appeal_sha256 != appeal.sha256 or event.appeal_id != appeal.appeal_id or event.resource_id != appeal.resource_id or event.observed_generation != appeal.observed_generation):
            raise RepairError("appeal lifecycle event references another appeal")
    expected_withdrawal = withdrawal.sha256 if withdrawal else _ZERO_HASH
    if resolution is not None and resolution.withdrawal_sha256 != expected_withdrawal:
        raise RepairError("appeal resolution withdrawal reference mismatch")
    entries: list[AbandonmentAppealHistoryEntry] = []
    previous = _ZERO_HASH
    if withdrawal is not None:
        entry = AbandonmentAppealHistoryEntry.build(1, previous, "withdrawal", withdrawal.sha256, "withdrawn")
        entries.append(entry)
        previous = entry.entry_sha256
    if resolution is not None:
        entries.append(AbandonmentAppealHistoryEntry.build(len(entries) + 1, previous, "resolution", resolution.sha256, resolution.outcome))
    return AbandonmentAppealLifecycleHistory(appeal.sha256, appeal.appeal_id, appeal.resource_id, appeal.observed_generation, tuple(entries))


def verify_abandonment_appeal_lifecycle_history(appeal: AbandonmentDecisionAppeal, history: AbandonmentAppealLifecycleHistory, *, withdrawal: AbandonmentAppealWithdrawalRecord | None = None, resolution: AbandonmentAppealResolutionRecord | None = None) -> bool:
    rebuilt = build_abandonment_appeal_lifecycle_history(appeal, withdrawal=withdrawal, resolution=resolution)
    if rebuilt != history:
        raise RepairError("abandonment appeal lifecycle history mismatch")
    return True
