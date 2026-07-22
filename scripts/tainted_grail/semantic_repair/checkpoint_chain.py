"""Canonical checkpoint proof chains and bounded rotation anchors."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .compaction import JournalCheckpointProof
from .errors import CheckpointProofError

_SCHEMA_VERSION = 1
_ZERO_HASH = "0" * 64
_PROOF_KIND = "checkpoint-proof"
_ROTATION_KIND = "rotation-anchor"


def _canonical(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path = Path(path)
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
class CheckpointChainEntry:
    index: int
    kind: str
    previous_entry_sha256: str
    payload: dict[str, Any]
    entry_sha256: str

    def core_dict(self) -> dict[str, Any]:
        return {
            "schema_version": _SCHEMA_VERSION,
            "index": self.index,
            "kind": self.kind,
            "previous_entry_sha256": self.previous_entry_sha256,
            "payload": self.payload,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.core_dict(), "entry_sha256": self.entry_sha256}

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @classmethod
    def build(
        cls,
        index: int,
        kind: str,
        previous_entry_sha256: str,
        payload: dict[str, Any],
    ) -> "CheckpointChainEntry":
        if type(index) is not int or index <= 0:
            raise CheckpointProofError("checkpoint chain index must be positive")
        if kind not in {_PROOF_KIND, _ROTATION_KIND}:
            raise CheckpointProofError("checkpoint chain entry kind is unsupported")
        if not isinstance(previous_entry_sha256, str) or len(previous_entry_sha256) != 64:
            raise CheckpointProofError("checkpoint chain previous hash is invalid")
        core = {
            "schema_version": _SCHEMA_VERSION,
            "index": index,
            "kind": kind,
            "previous_entry_sha256": previous_entry_sha256,
            "payload": dict(payload),
        }
        return cls(index, kind, previous_entry_sha256, dict(payload), _sha(_canonical(core)))

    @classmethod
    def from_dict(cls, doc: Any) -> "CheckpointChainEntry":
        expected = {
            "schema_version",
            "index",
            "kind",
            "previous_entry_sha256",
            "payload",
            "entry_sha256",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise CheckpointProofError("checkpoint chain entry has unexpected fields")
        if doc["schema_version"] != _SCHEMA_VERSION or not isinstance(doc["payload"], dict):
            raise CheckpointProofError("checkpoint chain entry boundary is invalid")
        built = cls.build(
            doc["index"],
            doc["kind"],
            doc["previous_entry_sha256"],
            doc["payload"],
        )
        if doc["entry_sha256"] != built.entry_sha256:
            raise CheckpointProofError("checkpoint chain entry hash mismatch")
        return built


def read_checkpoint_chain(path: Path) -> tuple[CheckpointChainEntry, ...]:
    path = Path(path)
    if not path.exists():
        return ()
    entries: list[CheckpointChainEntry] = []
    expected_previous = _ZERO_HASH
    for index, raw in enumerate(path.read_bytes().splitlines(), start=1):
        try:
            doc = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CheckpointProofError(f"checkpoint chain line {index} is invalid") from exc
        entry = CheckpointChainEntry.from_dict(doc)
        if entry.index != index:
            raise CheckpointProofError("checkpoint chain index mismatch")
        if entry.previous_entry_sha256 != expected_previous:
            raise CheckpointProofError("checkpoint chain link mismatch")
        entries.append(entry)
        expected_previous = entry.entry_sha256
    return tuple(entries)


def chain_sha256(path: Path) -> str:
    raw = Path(path).read_bytes() if Path(path).exists() else b""
    return _sha(raw)


def append_checkpoint_proof(
    path: Path,
    proof: JournalCheckpointProof,
) -> CheckpointChainEntry:
    path = Path(path)
    entries = read_checkpoint_chain(path)
    previous = entries[-1].entry_sha256 if entries else _ZERO_HASH
    payload = {
        "authority": "synthetic-checkpoint-chain-only",
        "runtime_authority": "none",
        "promotion": "none",
        "proof_sha256": proof.sha256,
        "source_journal_sha256": proof.source_journal_sha256,
        "compacted_journal_sha256": proof.compacted_journal_sha256,
        "compacted_record_hash": proof.compacted_record_hash,
    }
    entry = CheckpointChainEntry.build(len(entries) + 1, _PROOF_KIND, previous, payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(entry.to_bytes())
        handle.flush()
        os.fsync(handle.fileno())
    return entry


def rotate_checkpoint_chain(
    path: Path,
    *,
    max_entries: int = 8,
) -> CheckpointChainEntry | None:
    if type(max_entries) is not int or max_entries <= 0:
        raise CheckpointProofError("max_entries must be a positive integer")
    path = Path(path)
    entries = read_checkpoint_chain(path)
    if len(entries) <= max_entries:
        return None
    raw = path.read_bytes()
    payload = {
        "authority": "synthetic-checkpoint-chain-rotation-only",
        "runtime_authority": "none",
        "promotion": "none",
        "rotated_chain_sha256": _sha(raw),
        "rotated_entry_count": len(entries),
        "rotated_final_entry_sha256": entries[-1].entry_sha256,
    }
    anchor = CheckpointChainEntry.build(1, _ROTATION_KIND, _ZERO_HASH, payload)
    _atomic_write(path, anchor.to_bytes())
    return anchor


def verify_checkpoint_chain_contains_proof(
    entries: Iterable[CheckpointChainEntry],
    proof: JournalCheckpointProof,
) -> bool:
    proof_sha = proof.sha256
    if any(
        entry.kind == _PROOF_KIND and entry.payload.get("proof_sha256") == proof_sha
        for entry in entries
    ):
        return True
    raise CheckpointProofError("checkpoint proof is not present in the active chain")
