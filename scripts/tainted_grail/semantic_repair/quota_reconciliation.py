"""Hash-chained reconciliation journals for compaction quota lifecycles."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from .compaction_quota import CompactionQuotaLedger
from .errors import CheckpointProofError
from .quota_lifecycle import (
    CompactionQuotaLedgerCompactionRecord,
    CompactionQuotaReleaseRecord,
    verify_compaction_quota_ledger_compaction,
)

_ZERO_HASH = "0" * 64
_EVENTS = {
    "source-ledger",
    "release-record",
    "compacted-ledger",
    "compaction-record",
}


def _canonical(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class QuotaReconciliationEntry:
    index: int
    previous_entry_sha256: str
    event: str
    object_id: str
    object_sha256: str
    byte_delta: int
    balance_after_bytes: int
    entry_sha256: str

    def __post_init__(self) -> None:
        if type(self.index) is not int or self.index <= 0:
            raise CheckpointProofError(
                "quota reconciliation entry index must be positive"
            )
        if self.event not in _EVENTS:
            raise CheckpointProofError(
                "quota reconciliation event is unsupported"
            )
        if not isinstance(self.object_id, str) or not self.object_id.strip():
            raise CheckpointProofError(
                "quota reconciliation object_id must be non-empty"
            )
        for value in (
            self.previous_entry_sha256,
            self.object_sha256,
            self.entry_sha256,
        ):
            if not isinstance(value, str) or len(value) != 64:
                raise CheckpointProofError(
                    "quota reconciliation entry hash is invalid"
                )
        if type(self.byte_delta) is not int:
            raise CheckpointProofError(
                "quota reconciliation byte delta must be an integer"
            )
        if (
            type(self.balance_after_bytes) is not int
            or self.balance_after_bytes < 0
        ):
            raise CheckpointProofError(
                "quota reconciliation balance is invalid"
            )
        expected = _sha(_canonical(self.core_dict()))
        if expected != self.entry_sha256:
            raise CheckpointProofError(
                "quota reconciliation entry hash mismatch"
            )

    def core_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "index": self.index,
            "previous_entry_sha256": self.previous_entry_sha256,
            "event": self.event,
            "object_id": self.object_id,
            "object_sha256": self.object_sha256,
            "byte_delta": self.byte_delta,
            "balance_after_bytes": self.balance_after_bytes,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.core_dict(), "entry_sha256": self.entry_sha256}

    @classmethod
    def build(
        cls,
        index: int,
        previous_entry_sha256: str,
        event: str,
        object_id: str,
        object_sha256: str,
        byte_delta: int,
        balance_after_bytes: int,
    ) -> "QuotaReconciliationEntry":
        core = {
            "schema_version": 1,
            "index": index,
            "previous_entry_sha256": previous_entry_sha256,
            "event": event,
            "object_id": object_id,
            "object_sha256": object_sha256,
            "byte_delta": byte_delta,
            "balance_after_bytes": balance_after_bytes,
        }
        return cls(
            index,
            previous_entry_sha256,
            event,
            object_id,
            object_sha256,
            byte_delta,
            balance_after_bytes,
            _sha(_canonical(core)),
        )

    @classmethod
    def from_dict(cls, doc: Any) -> "QuotaReconciliationEntry":
        expected = {
            "schema_version",
            "index",
            "previous_entry_sha256",
            "event",
            "object_id",
            "object_sha256",
            "byte_delta",
            "balance_after_bytes",
            "entry_sha256",
        }
        if (
            not isinstance(doc, dict)
            or set(doc) != expected
            or doc["schema_version"] != 1
        ):
            raise CheckpointProofError(
                "quota reconciliation entry boundary is invalid"
            )
        return cls(
            doc["index"],
            doc["previous_entry_sha256"],
            doc["event"],
            doc["object_id"],
            doc["object_sha256"],
            doc["byte_delta"],
            doc["balance_after_bytes"],
            doc["entry_sha256"],
        )


@dataclass(frozen=True)
class CompactionQuotaReconciliationJournal:
    source_ledger_sha256: str
    source_reserved_bytes: int
    released_backup_bytes: int
    remaining_backup_bytes: int
    compacted_ledger_sha256: str
    compaction_record_sha256: str
    entries: tuple[QuotaReconciliationEntry, ...]

    def __post_init__(self) -> None:
        for value in (
            self.source_ledger_sha256,
            self.compacted_ledger_sha256,
            self.compaction_record_sha256,
        ):
            if not isinstance(value, str) or len(value) != 64:
                raise CheckpointProofError(
                    "quota reconciliation journal hash is invalid"
                )
        for value in (
            self.source_reserved_bytes,
            self.released_backup_bytes,
            self.remaining_backup_bytes,
        ):
            if type(value) is not int or value < 0:
                raise CheckpointProofError(
                    "quota reconciliation byte total is invalid"
                )
        if (
            self.source_reserved_bytes
            != self.released_backup_bytes + self.remaining_backup_bytes
        ):
            raise CheckpointProofError(
                "quota reconciliation byte totals do not balance"
            )
        if len(self.entries) < 4:
            raise CheckpointProofError(
                "quota reconciliation journal is incomplete"
            )
        previous = _ZERO_HASH
        balance = 0
        for index, entry in enumerate(self.entries, start=1):
            if (
                entry.index != index
                or entry.previous_entry_sha256 != previous
            ):
                raise CheckpointProofError(
                    "quota reconciliation journal chain is invalid"
                )
            balance += entry.byte_delta
            if balance != entry.balance_after_bytes:
                raise CheckpointProofError(
                    "quota reconciliation running balance mismatch"
                )
            previous = entry.entry_sha256
        if balance != self.remaining_backup_bytes:
            raise CheckpointProofError(
                "quota reconciliation final balance mismatch"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-compaction-quota-reconciliation-journal-only",
            "runtime_authority": "none",
            "promotion": "none",
            "mutation_authority": "none",
            "source_ledger_sha256": self.source_ledger_sha256,
            "source_reserved_bytes": self.source_reserved_bytes,
            "released_backup_bytes": self.released_backup_bytes,
            "remaining_backup_bytes": self.remaining_backup_bytes,
            "compacted_ledger_sha256": self.compacted_ledger_sha256,
            "compaction_record_sha256": self.compaction_record_sha256,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return _sha(self.to_bytes())

    @classmethod
    def from_bytes(cls, data: bytes) -> "CompactionQuotaReconciliationJournal":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CheckpointProofError(
                "invalid quota reconciliation journal"
            ) from exc
        expected = {
            "schema_version",
            "authority",
            "runtime_authority",
            "promotion",
            "mutation_authority",
            "source_ledger_sha256",
            "source_reserved_bytes",
            "released_backup_bytes",
            "remaining_backup_bytes",
            "compacted_ledger_sha256",
            "compaction_record_sha256",
            "entries",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise CheckpointProofError(
                "quota reconciliation journal has unexpected fields"
            )
        if (
            doc["schema_version"] != 1
            or doc["authority"]
            != "synthetic-compaction-quota-reconciliation-journal-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
            or doc["mutation_authority"] != "none"
            or not isinstance(doc["entries"], list)
        ):
            raise CheckpointProofError(
                "quota reconciliation journal boundary is invalid"
            )
        return cls(
            doc["source_ledger_sha256"],
            doc["source_reserved_bytes"],
            doc["released_backup_bytes"],
            doc["remaining_backup_bytes"],
            doc["compacted_ledger_sha256"],
            doc["compaction_record_sha256"],
            tuple(
                QuotaReconciliationEntry.from_dict(item)
                for item in doc["entries"]
            ),
        )


def _ledger_total(ledger: CompactionQuotaLedger) -> int:
    return (
        ledger.reservations[-1].cumulative_backup_bytes
        if ledger.reservations
        else 0
    )


def build_compaction_quota_reconciliation_journal(
    source: CompactionQuotaLedger,
    releases: Iterable[CompactionQuotaReleaseRecord],
    compacted: CompactionQuotaLedger,
    record: CompactionQuotaLedgerCompactionRecord,
) -> CompactionQuotaReconciliationJournal:
    supplied = tuple(sorted(releases, key=lambda item: item.release_index))
    verify_compaction_quota_ledger_compaction(
        source,
        supplied,
        compacted,
        record,
    )
    source_total = _ledger_total(source)
    remaining_total = _ledger_total(compacted)
    if source_total != record.released_backup_bytes + remaining_total:
        raise CheckpointProofError(
            "quota reconciliation source and compacted totals differ"
        )

    entries: list[QuotaReconciliationEntry] = []
    previous = _ZERO_HASH
    balance = source_total
    first = QuotaReconciliationEntry.build(
        1,
        previous,
        "source-ledger",
        "source-ledger",
        source.sha256,
        source_total,
        source_total,
    )
    entries.append(first)
    previous = first.entry_sha256

    for release in supplied:
        balance -= release.released_backup_bytes
        entry = QuotaReconciliationEntry.build(
            len(entries) + 1,
            previous,
            "release-record",
            release.operation_id,
            release.sha256,
            -release.released_backup_bytes,
            balance,
        )
        entries.append(entry)
        previous = entry.entry_sha256

    compacted_entry = QuotaReconciliationEntry.build(
        len(entries) + 1,
        previous,
        "compacted-ledger",
        "compacted-ledger",
        compacted.sha256,
        0,
        balance,
    )
    entries.append(compacted_entry)
    previous = compacted_entry.entry_sha256

    record_entry = QuotaReconciliationEntry.build(
        len(entries) + 1,
        previous,
        "compaction-record",
        "compaction-record",
        record.sha256,
        0,
        balance,
    )
    entries.append(record_entry)

    return CompactionQuotaReconciliationJournal(
        source.sha256,
        source_total,
        record.released_backup_bytes,
        remaining_total,
        compacted.sha256,
        record.sha256,
        tuple(entries),
    )


def verify_compaction_quota_reconciliation_journal(
    source: CompactionQuotaLedger,
    releases: Iterable[CompactionQuotaReleaseRecord],
    compacted: CompactionQuotaLedger,
    record: CompactionQuotaLedgerCompactionRecord,
    journal: CompactionQuotaReconciliationJournal,
) -> bool:
    rebuilt = build_compaction_quota_reconciliation_journal(
        source,
        releases,
        compacted,
        record,
    )
    if rebuilt != journal:
        raise CheckpointProofError(
            "quota reconciliation journal mismatch"
        )
    return True
