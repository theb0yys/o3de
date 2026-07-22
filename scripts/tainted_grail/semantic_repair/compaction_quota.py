"""Cumulative backup quotas for repeated synthetic compaction operations."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import CheckpointProofError


def _canonical(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


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
class CompactionBackupLimits:
    max_operations: int = 16
    max_total_backup_bytes: int = 4 * 1024 * 1024
    max_single_operation_bytes: int = 1024 * 1024

    def __post_init__(self) -> None:
        if any(
            type(value) is not int or value <= 0
            for value in (
                self.max_operations,
                self.max_total_backup_bytes,
                self.max_single_operation_bytes,
            )
        ):
            raise CheckpointProofError(
                "compaction backup limits must be positive integers"
            )
        if self.max_single_operation_bytes > self.max_total_backup_bytes:
            raise CheckpointProofError(
                "single-operation quota cannot exceed total quota"
            )


@dataclass(frozen=True)
class CompactionQuotaReservation:
    operation_id: str
    operation_index: int
    operation_backup_bytes: int
    cumulative_backup_bytes: int
    operation_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.operation_id, str) or not self.operation_id.strip():
            raise CheckpointProofError(
                "compaction quota operation_id must be non-empty"
            )
        if type(self.operation_index) is not int or self.operation_index <= 0:
            raise CheckpointProofError(
                "compaction quota operation index must be positive"
            )
        if (
            type(self.operation_backup_bytes) is not int
            or self.operation_backup_bytes < 0
        ):
            raise CheckpointProofError(
                "compaction operation backup bytes are invalid"
            )
        if (
            type(self.cumulative_backup_bytes) is not int
            or self.cumulative_backup_bytes < 0
        ):
            raise CheckpointProofError(
                "compaction cumulative backup bytes are invalid"
            )
        if (
            not isinstance(self.operation_sha256, str)
            or len(self.operation_sha256) != 64
        ):
            raise CheckpointProofError("compaction operation hash is invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "operation_index": self.operation_index,
            "operation_backup_bytes": self.operation_backup_bytes,
            "cumulative_backup_bytes": self.cumulative_backup_bytes,
            "operation_sha256": self.operation_sha256,
        }


@dataclass(frozen=True)
class CompactionQuotaLedger:
    limits: CompactionBackupLimits
    reservations: tuple[CompactionQuotaReservation, ...] = ()

    def __post_init__(self) -> None:
        ids = [item.operation_id for item in self.reservations]
        if len(ids) != len(set(ids)):
            raise CheckpointProofError(
                "compaction quota operation IDs must be unique"
            )
        cumulative = 0
        for index, item in enumerate(self.reservations, start=1):
            if item.operation_index != index:
                raise CheckpointProofError(
                    "compaction quota operation indices are not contiguous"
                )
            cumulative += item.operation_backup_bytes
            if item.cumulative_backup_bytes != cumulative:
                raise CheckpointProofError(
                    "compaction quota cumulative bytes mismatch"
                )
        if (
            len(self.reservations) > self.limits.max_operations
            or cumulative > self.limits.max_total_backup_bytes
        ):
            raise CheckpointProofError(
                "compaction quota ledger exceeds configured limits"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-repeated-compaction-quota-only",
            "runtime_authority": "none",
            "promotion": "none",
            "limits": {
                "max_operations": self.limits.max_operations,
                "max_total_backup_bytes": self.limits.max_total_backup_bytes,
                "max_single_operation_bytes": self.limits.max_single_operation_bytes,
            },
            "reservations": [item.to_dict() for item in self.reservations],
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()

    @classmethod
    def from_bytes(cls, data: bytes) -> "CompactionQuotaLedger":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CheckpointProofError("invalid compaction quota ledger") from exc
        expected = {
            "schema_version",
            "authority",
            "runtime_authority",
            "promotion",
            "limits",
            "reservations",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise CheckpointProofError(
                "compaction quota ledger has unexpected fields"
            )
        if (
            doc["schema_version"] != 1
            or doc["authority"] != "synthetic-repeated-compaction-quota-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
        ):
            raise CheckpointProofError(
                "compaction quota ledger boundary is invalid"
            )
        limits_doc = doc["limits"]
        if not isinstance(limits_doc, dict) or set(limits_doc) != {
            "max_operations",
            "max_total_backup_bytes",
            "max_single_operation_bytes",
        }:
            raise CheckpointProofError("compaction quota limits are invalid")
        if not isinstance(doc["reservations"], list):
            raise CheckpointProofError(
                "compaction quota reservations must be an array"
            )
        limits = CompactionBackupLimits(**limits_doc)
        reservations = tuple(
            CompactionQuotaReservation(**item) for item in doc["reservations"]
        )
        return cls(limits, reservations)


def reserve_compaction_backup_quota(
    ledger_path: Path,
    operation_id: str,
    backup_parts: tuple[bytes, ...],
    *,
    limits: CompactionBackupLimits = CompactionBackupLimits(),
) -> CompactionQuotaLedger:
    if not isinstance(operation_id, str) or not operation_id.strip():
        raise CheckpointProofError("operation_id must be non-empty text")
    if any(not isinstance(part, bytes) for part in backup_parts):
        raise CheckpointProofError("compaction backup parts must be bytes")
    ledger_path = Path(ledger_path)
    current = (
        CompactionQuotaLedger.from_bytes(ledger_path.read_bytes())
        if ledger_path.exists()
        else CompactionQuotaLedger(limits)
    )
    if current.limits != limits:
        raise CheckpointProofError(
            "compaction quota limits differ from existing ledger"
        )
    if any(item.operation_id == operation_id for item in current.reservations):
        raise CheckpointProofError(
            "compaction quota operation_id is already reserved"
        )
    operation_bytes = sum(len(part) for part in backup_parts)
    if operation_bytes > limits.max_single_operation_bytes:
        raise CheckpointProofError(
            "compaction backup exceeds single-operation quota"
        )
    if len(current.reservations) + 1 > limits.max_operations:
        raise CheckpointProofError(
            "compaction backup operation quota exceeded"
        )
    cumulative = (
        current.reservations[-1].cumulative_backup_bytes
        if current.reservations
        else 0
    ) + operation_bytes
    if cumulative > limits.max_total_backup_bytes:
        raise CheckpointProofError(
            "compaction cumulative backup quota exceeded"
        )
    digest_input = b"".join(
        len(part).to_bytes(8, "big") + part for part in backup_parts
    )
    digest = hashlib.sha256(digest_input).hexdigest()
    reservation = CompactionQuotaReservation(
        operation_id,
        len(current.reservations) + 1,
        operation_bytes,
        cumulative,
        digest,
    )
    updated = CompactionQuotaLedger(
        limits,
        current.reservations + (reservation,),
    )
    _atomic_write(ledger_path, updated.to_bytes())
    return updated
