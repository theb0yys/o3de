"""Lease-owned journal compaction with canonical checkpoint proofs."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .errors import CheckpointProofError
from .journal import CrashRecoveryJournal, JournalRecord, _ZERO_HASH, _canonical
from .ownership import ResourceLease

_SCHEMA_VERSION = 1
_CHECKPOINT_TRANSACTION_ID = "__journal_checkpoint__"
_CHECKPOINT_PHASE = "compacted-checkpoint"
_TERMINAL_PHASES = {
    "committed",
    "rolled-back",
    "cancelled",
    "intent-committed",
    "intent-rolled-back",
    _CHECKPOINT_PHASE,
}


def _canonical_line(doc: dict[str, Any]) -> bytes:
    return _canonical(doc) + b"\n"


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


def _restore(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
    else:
        _atomic_write(path, previous)


@dataclass(frozen=True)
class CheckpointTransactionState:
    transaction_id: str
    latest_phase: str
    record_count: int
    latest_record_hash: str
    owner_id: str | None = None
    lock_generation: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "latest_phase": self.latest_phase,
            "record_count": self.record_count,
            "latest_record_hash": self.latest_record_hash,
            "owner_id": self.owner_id,
            "lock_generation": self.lock_generation,
        }

    @classmethod
    def from_dict(cls, doc: Any) -> "CheckpointTransactionState":
        expected = {
            "transaction_id",
            "latest_phase",
            "record_count",
            "latest_record_hash",
            "owner_id",
            "lock_generation",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise CheckpointProofError("checkpoint transaction state has unexpected fields")
        if (
            not isinstance(doc["transaction_id"], str)
            or not doc["transaction_id"]
            or doc["latest_phase"] not in _TERMINAL_PHASES
            or type(doc["record_count"]) is not int
            or doc["record_count"] <= 0
            or not isinstance(doc["latest_record_hash"], str)
            or len(doc["latest_record_hash"]) != 64
        ):
            raise CheckpointProofError("checkpoint transaction state is invalid")
        owner = doc["owner_id"]
        generation = doc["lock_generation"]
        if (owner is None) != (generation is None):
            raise CheckpointProofError("checkpoint ownership fields must appear together")
        if owner is not None and (
            not isinstance(owner, str)
            or not owner
            or type(generation) is not int
            or generation <= 0
        ):
            raise CheckpointProofError("checkpoint ownership identity is invalid")
        return cls(
            doc["transaction_id"],
            doc["latest_phase"],
            doc["record_count"],
            doc["latest_record_hash"],
            owner,
            generation,
        )


@dataclass(frozen=True)
class JournalCheckpointProof:
    source_journal_sha256: str
    source_record_count: int
    source_final_record_hash: str
    checkpoint_payload_sha256: str
    compacted_journal_sha256: str
    compacted_record_hash: str
    terminal_states: tuple[CheckpointTransactionState, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": _SCHEMA_VERSION,
            "authority": "synthetic-journal-compaction-proof-only",
            "runtime_authority": "none",
            "promotion": "none",
            "source_journal_sha256": self.source_journal_sha256,
            "source_record_count": self.source_record_count,
            "source_final_record_hash": self.source_final_record_hash,
            "checkpoint_payload_sha256": self.checkpoint_payload_sha256,
            "compacted_journal_sha256": self.compacted_journal_sha256,
            "compacted_record_hash": self.compacted_record_hash,
            "terminal_states": [item.to_dict() for item in self.terminal_states],
        }

    def to_bytes(self) -> bytes:
        return _canonical_line(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()

    @classmethod
    def from_bytes(cls, data: bytes) -> "JournalCheckpointProof":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CheckpointProofError("invalid journal checkpoint proof") from exc
        expected = {
            "schema_version",
            "authority",
            "runtime_authority",
            "promotion",
            "source_journal_sha256",
            "source_record_count",
            "source_final_record_hash",
            "checkpoint_payload_sha256",
            "compacted_journal_sha256",
            "compacted_record_hash",
            "terminal_states",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise CheckpointProofError("journal checkpoint proof has unexpected fields")
        if (
            doc["schema_version"] != _SCHEMA_VERSION
            or doc["authority"] != "synthetic-journal-compaction-proof-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
            or type(doc["source_record_count"]) is not int
            or doc["source_record_count"] <= 0
        ):
            raise CheckpointProofError("journal checkpoint proof boundary is invalid")
        hashes = (
            doc["source_journal_sha256"],
            doc["source_final_record_hash"],
            doc["checkpoint_payload_sha256"],
            doc["compacted_journal_sha256"],
            doc["compacted_record_hash"],
        )
        if any(not isinstance(value, str) or len(value) != 64 for value in hashes):
            raise CheckpointProofError("journal checkpoint proof contains invalid hashes")
        states = doc["terminal_states"]
        if not isinstance(states, list) or not states:
            raise CheckpointProofError("journal checkpoint proof requires terminal states")
        parsed = tuple(CheckpointTransactionState.from_dict(item) for item in states)
        if tuple(sorted(item.transaction_id for item in parsed)) != tuple(
            item.transaction_id for item in parsed
        ):
            raise CheckpointProofError("checkpoint terminal states are not sorted")
        return cls(
            doc["source_journal_sha256"],
            doc["source_record_count"],
            doc["source_final_record_hash"],
            doc["checkpoint_payload_sha256"],
            doc["compacted_journal_sha256"],
            doc["compacted_record_hash"],
            parsed,
        )


def _terminal_states(records: Iterable[JournalRecord]) -> tuple[CheckpointTransactionState, ...]:
    grouped: dict[str, list[JournalRecord]] = {}
    for record in records:
        grouped.setdefault(record.transaction_id, []).append(record)
    states: list[CheckpointTransactionState] = []
    for transaction_id in sorted(grouped):
        tx_records = grouped[transaction_id]
        latest = tx_records[-1]
        if latest.phase not in _TERMINAL_PHASES:
            raise CheckpointProofError(
                f"transaction {transaction_id} is not terminal: {latest.phase}"
            )
        ownerships: set[tuple[str, int]] = set()
        for record in tx_records:
            owner = record.payload.get("journal_owner_id")
            generation = record.payload.get("journal_lock_generation")
            if owner is None and generation is None:
                continue
            if not isinstance(owner, str) or type(generation) is not int:
                raise CheckpointProofError(
                    f"transaction {transaction_id} has invalid ownership metadata"
                )
            ownerships.add((owner, generation))
        if len(ownerships) > 1:
            raise CheckpointProofError(
                f"transaction {transaction_id} changed ownership during its history"
            )
        owner_id, lock_generation = (
            next(iter(ownerships)) if ownerships else (None, None)
        )
        states.append(
            CheckpointTransactionState(
                transaction_id,
                latest.phase,
                len(tx_records),
                latest.record_hash,
                owner_id,
                lock_generation,
            )
        )
    return tuple(states)


def compact_terminal_journal_owned(
    journal: CrashRecoveryJournal,
    lease: ResourceLease,
    proof_path: Path,
) -> JournalCheckpointProof:
    """Replace a fully terminal journal with one checkpoint record and proof."""
    journal.lock.assert_owned(lease)
    proof_path = Path(proof_path)
    if proof_path.resolve(strict=False) == journal.path.resolve(strict=False):
        raise CheckpointProofError("checkpoint proof path must differ from journal path")
    records, torn = journal.read_records(allow_torn_tail=True)
    if torn:
        raise CheckpointProofError("journal must be recovered before compaction")
    if not records:
        raise CheckpointProofError("cannot compact an empty journal")

    source_bytes = journal.path.read_bytes()
    states = _terminal_states(records)
    payload = {
        "checkpoint_schema_version": _SCHEMA_VERSION,
        "runtime_authority": "none",
        "promotion": "none",
        "source_journal_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_record_count": len(records),
        "source_final_record_hash": records[-1].record_hash,
        "terminal_states": [item.to_dict() for item in states],
    }
    payload_sha = hashlib.sha256(_canonical(payload)).hexdigest()
    core = {
        "schema_version": 1,
        "sequence": 1,
        "transaction_id": _CHECKPOINT_TRANSACTION_ID,
        "phase": _CHECKPOINT_PHASE,
        "payload": payload,
        "previous_hash": _ZERO_HASH,
    }
    record_hash = hashlib.sha256(_canonical(core)).hexdigest()
    checkpoint = JournalRecord(
        1,
        _CHECKPOINT_TRANSACTION_ID,
        _CHECKPOINT_PHASE,
        payload,
        _ZERO_HASH,
        record_hash,
    )
    compacted_bytes = _canonical_line(checkpoint.to_dict())
    proof = JournalCheckpointProof(
        payload["source_journal_sha256"],
        len(records),
        records[-1].record_hash,
        payload_sha,
        hashlib.sha256(compacted_bytes).hexdigest(),
        record_hash,
        states,
    )

    journal_before = source_bytes
    proof_before = proof_path.read_bytes() if proof_path.exists() else None
    try:
        _atomic_write(journal.path, compacted_bytes)
        _atomic_write(proof_path, proof.to_bytes())
        verify_checkpoint_proof(journal.path, proof)
    except Exception:
        _restore(journal.path, journal_before)
        _restore(proof_path, proof_before)
        raise
    return proof


def verify_checkpoint_proof(
    journal_path: Path,
    proof: JournalCheckpointProof | bytes,
) -> bool:
    parsed = JournalCheckpointProof.from_bytes(proof) if isinstance(proof, bytes) else proof
    raw = Path(journal_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != parsed.compacted_journal_sha256:
        raise CheckpointProofError("compacted journal SHA-256 does not match proof")
    records, torn = CrashRecoveryJournal(Path(journal_path)).read_records(
        allow_torn_tail=True
    )
    if torn or len(records) != 1:
        raise CheckpointProofError("compacted journal must contain one complete record")
    record = records[0]
    if (
        record.transaction_id != _CHECKPOINT_TRANSACTION_ID
        or record.phase != _CHECKPOINT_PHASE
        or record.record_hash != parsed.compacted_record_hash
        or hashlib.sha256(_canonical(record.payload)).hexdigest()
        != parsed.checkpoint_payload_sha256
        or record.payload.get("source_journal_sha256")
        != parsed.source_journal_sha256
        or record.payload.get("source_record_count")
        != parsed.source_record_count
        or record.payload.get("source_final_record_hash")
        != parsed.source_final_record_hash
        or tuple(
            CheckpointTransactionState.from_dict(item)
            for item in record.payload.get("terminal_states", [])
        )
        != parsed.terminal_states
    ):
        raise CheckpointProofError("compacted checkpoint record does not match proof")
    return True
