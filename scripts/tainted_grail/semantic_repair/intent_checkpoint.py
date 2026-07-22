"""Checkpoint integration for terminal multi-file publication intent journals."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .compaction import JournalCheckpointProof
from .errors import PublicationIntentError
from .interrupted_compaction import compact_terminal_journal_resilient_owned
from .journal import CrashRecoveryJournal
from .ownership import ResourceLease
from .publication_intent import PublicationIntent

_INTENT_TERMINAL = {"intent-committed", "intent-rolled-back"}


def _canonical(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


@dataclass(frozen=True)
class IntentCheckpointState:
    intent_id: str
    status: str
    intent_sha256: str
    final_record_hash: str

    def to_dict(self) -> dict[str, str]:
        return {
            "intent_id": self.intent_id,
            "status": self.status,
            "intent_sha256": self.intent_sha256,
            "final_record_hash": self.final_record_hash,
        }


@dataclass(frozen=True)
class IntentJournalCheckpointReceipt:
    source_journal_sha256: str
    checkpoint_proof_sha256: str
    checkpoint_chain_sha256: str
    intents: tuple[IntentCheckpointState, ...]

    def to_bytes(self) -> bytes:
        return _canonical(
            {
                "schema_version": 1,
                "authority": "synthetic-intent-journal-checkpoint-only",
                "runtime_authority": "none",
                "promotion": "none",
                "source_journal_sha256": self.source_journal_sha256,
                "checkpoint_proof_sha256": self.checkpoint_proof_sha256,
                "checkpoint_chain_sha256": self.checkpoint_chain_sha256,
                "intents": [item.to_dict() for item in self.intents],
            }
        )


def _intent_states(journal: CrashRecoveryJournal) -> tuple[IntentCheckpointState, ...]:
    records, torn = journal.read_records(allow_torn_tail=True)
    if torn:
        raise PublicationIntentError("intent journal must be recovered before checkpointing")
    grouped = {}
    for record in records:
        if record.phase.startswith("intent-"):
            grouped.setdefault(record.transaction_id, []).append(record)
    if not grouped:
        raise PublicationIntentError("intent journal contains no publication intents")
    states = []
    for intent_id in sorted(grouped):
        tx_records = grouped[intent_id]
        latest = tx_records[-1]
        if latest.phase not in _INTENT_TERMINAL:
            raise PublicationIntentError(f"publication intent {intent_id} is not terminal")
        prepared = next(
            (record for record in tx_records if record.phase == "intent-prepared"),
            None,
        )
        if prepared is None:
            raise PublicationIntentError(f"publication intent {intent_id} has no prepared record")
        intent = PublicationIntent.from_dict(prepared.payload.get("publication_intent"))
        expected_sha = prepared.payload.get("intent_sha256")
        if expected_sha != intent.sha256:
            raise PublicationIntentError(f"publication intent {intent_id} hash mismatch")
        states.append(
            IntentCheckpointState(intent_id, latest.phase, intent.sha256, latest.record_hash)
        )
    return tuple(states)


def checkpoint_publication_intent_journal_owned(
    journal: CrashRecoveryJournal,
    lease: ResourceLease,
    proof_path: Path,
    chain_path: Path,
    *,
    max_chain_entries: int = 8,
) -> IntentJournalCheckpointReceipt:
    states = _intent_states(journal)
    source_sha = hashlib.sha256(journal.path.read_bytes()).hexdigest()
    result = compact_terminal_journal_resilient_owned(
        journal,
        lease,
        proof_path,
        chain_path,
        max_chain_entries=max_chain_entries,
    )
    proof = JournalCheckpointProof.from_bytes(Path(proof_path).read_bytes())
    if proof.source_journal_sha256 != source_sha:
        raise PublicationIntentError("intent checkpoint proof does not bind source journal")
    proof_ids = {state.transaction_id for state in proof.terminal_states}
    if any(state.intent_id not in proof_ids for state in states):
        raise PublicationIntentError("intent checkpoint proof omitted a publication intent")
    return IntentJournalCheckpointReceipt(
        source_sha,
        proof.sha256,
        result.chain_sha256,
        states,
    )
