"""Compaction proofs for API v2 replay-window sequence histories."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .errors import RepairError
from .replay_sequence import ReplayWindowSequenceProof

_ZERO_HASH = "0" * 64


def _canonical(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


@dataclass(frozen=True)
class ReplaySequenceCompactionProof:
    source_sequence_sha256: str
    source_entry_count: int
    initial_generation: int
    final_generation: int
    first_entry_sha256: str
    final_entry_sha256: str
    status_counts: tuple[tuple[str, int], ...]
    previous_compaction_sha256: str
    compacted_summary_sha256: str

    def __post_init__(self) -> None:
        for value in (
            self.source_sequence_sha256,
            self.first_entry_sha256,
            self.final_entry_sha256,
            self.previous_compaction_sha256,
            self.compacted_summary_sha256,
        ):
            if not isinstance(value, str) or len(value) != 64:
                raise RepairError("replay sequence compaction hash is invalid")
        if type(self.source_entry_count) is not int or self.source_entry_count <= 0:
            raise RepairError("replay sequence compaction entry count must be positive")
        if self.status_counts != tuple(sorted(self.status_counts)):
            raise RepairError("replay sequence compaction status counts must be sorted")
        if sum(count for _, count in self.status_counts) != self.source_entry_count:
            raise RepairError("replay sequence compaction status count mismatch")

    def summary_dict(self) -> dict[str, Any]:
        return {
            "source_sequence_sha256": self.source_sequence_sha256,
            "source_entry_count": self.source_entry_count,
            "initial_generation": self.initial_generation,
            "final_generation": self.final_generation,
            "first_entry_sha256": self.first_entry_sha256,
            "final_entry_sha256": self.final_entry_sha256,
            "status_counts": [
                {"status": status, "count": count}
                for status, count in self.status_counts
            ],
            "previous_compaction_sha256": self.previous_compaction_sha256,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-api-v2-replay-sequence-compaction-proof-only",
            "runtime_authority": "none",
            "promotion": "none",
            **self.summary_dict(),
            "compacted_summary_sha256": self.compacted_summary_sha256,
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()

    @classmethod
    def from_bytes(cls, data: bytes) -> "ReplaySequenceCompactionProof":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RepairError("invalid replay sequence compaction proof") from exc
        expected = {
            "schema_version", "authority", "runtime_authority", "promotion",
            "source_sequence_sha256", "source_entry_count", "initial_generation",
            "final_generation", "first_entry_sha256", "final_entry_sha256",
            "status_counts", "previous_compaction_sha256",
            "compacted_summary_sha256",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise RepairError("replay sequence compaction proof has unexpected fields")
        if (
            doc["schema_version"] != 1
            or doc["authority"] != "synthetic-api-v2-replay-sequence-compaction-proof-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
            or not isinstance(doc["status_counts"], list)
        ):
            raise RepairError("replay sequence compaction proof boundary is invalid")
        counts = []
        for item in doc["status_counts"]:
            if not isinstance(item, dict) or set(item) != {"status", "count"}:
                raise RepairError("replay sequence compaction status count is invalid")
            counts.append((item["status"], item["count"]))
        return cls(
            doc["source_sequence_sha256"],
            doc["source_entry_count"],
            doc["initial_generation"],
            doc["final_generation"],
            doc["first_entry_sha256"],
            doc["final_entry_sha256"],
            tuple(counts),
            doc["previous_compaction_sha256"],
            doc["compacted_summary_sha256"],
        )


def _validate_sequence(proof: ReplayWindowSequenceProof) -> None:
    if not proof.entries:
        raise RepairError("replay sequence compaction requires entries")
    previous = _ZERO_HASH
    expected_generation = proof.initial_generation
    for index, entry in enumerate(proof.entries, start=1):
        if (
            entry.index != index
            or entry.previous_entry_sha256 != previous
            or entry.current_generation != expected_generation
        ):
            raise RepairError("replay sequence compaction continuity failed")
        core = {
            "schema_version": 1,
            "index": entry.index,
            "previous_entry_sha256": entry.previous_entry_sha256,
            "receipt_sha256": entry.receipt_sha256,
            "current_generation": entry.current_generation,
            "incoming_generation": entry.incoming_generation,
            "status": entry.status,
            "resulting_generation": entry.resulting_generation,
        }
        expected_hash = hashlib.sha256(_canonical(core)).hexdigest()
        if expected_hash != entry.entry_sha256:
            raise RepairError("replay sequence entry hash mismatch")
        expected_generation = entry.resulting_generation
        previous = entry.entry_sha256
    if expected_generation != proof.final_generation:
        raise RepairError("replay sequence final generation mismatch")


def build_replay_sequence_compaction_proof(
    proof: ReplayWindowSequenceProof,
    *,
    previous_compaction: ReplaySequenceCompactionProof | None = None,
) -> ReplaySequenceCompactionProof:
    _validate_sequence(proof)
    counts: dict[str, int] = {}
    for entry in proof.entries:
        counts[entry.status] = counts.get(entry.status, 0) + 1
    status_counts = tuple(sorted(counts.items()))
    summary = {
        "source_sequence_sha256": proof.sha256,
        "source_entry_count": len(proof.entries),
        "initial_generation": proof.initial_generation,
        "final_generation": proof.final_generation,
        "first_entry_sha256": proof.entries[0].entry_sha256,
        "final_entry_sha256": proof.entries[-1].entry_sha256,
        "status_counts": [
            {"status": status, "count": count}
            for status, count in status_counts
        ],
        "previous_compaction_sha256": (
            previous_compaction.sha256 if previous_compaction else _ZERO_HASH
        ),
    }
    return ReplaySequenceCompactionProof(
        proof.sha256,
        len(proof.entries),
        proof.initial_generation,
        proof.final_generation,
        proof.entries[0].entry_sha256,
        proof.entries[-1].entry_sha256,
        status_counts,
        summary["previous_compaction_sha256"],
        hashlib.sha256(_canonical(summary)).hexdigest(),
    )


def verify_replay_sequence_compaction_proof(
    source: ReplayWindowSequenceProof,
    compacted: ReplaySequenceCompactionProof,
    *,
    previous_compaction: ReplaySequenceCompactionProof | None = None,
) -> bool:
    rebuilt = build_replay_sequence_compaction_proof(
        source,
        previous_compaction=previous_compaction,
    )
    if rebuilt != compacted:
        raise RepairError("replay sequence compaction proof mismatch")
    return True
