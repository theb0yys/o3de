"""Hash-chained workflow policy receipt migration histories."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .ci_migration import WorkflowPolicyReceiptV2
from .ci_policy import WorkflowPolicyReceipt
from .errors import WorkflowPolicyError

_ZERO_HASH = "0" * 64


def _canonical(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _hash(value: str, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise WorkflowPolicyError(f"{name} hash is invalid")
    return value


def _violations_sha(violations: tuple[str, ...]) -> str:
    return hashlib.sha256(_canonical({"violations": list(violations)})).hexdigest()


@dataclass(frozen=True)
class WorkflowPolicyReceiptV3:
    workflow_sha256: str
    status: str
    violations: tuple[str, ...]
    source_receipt_sha256: str
    migration_algorithm: str = "canonical-v2-to-v3-history"

    def __post_init__(self) -> None:
        _hash(self.workflow_sha256, "v3 workflow")
        _hash(self.source_receipt_sha256, "v3 source receipt")
        if self.status not in {"valid", "invalid"}:
            raise WorkflowPolicyError("v3 workflow receipt status is invalid")
        if any(not isinstance(item, str) for item in self.violations):
            raise WorkflowPolicyError("v3 workflow receipt violations are invalid")
        if (self.status == "valid") != (not self.violations):
            raise WorkflowPolicyError("v3 workflow receipt status is inconsistent")
        if self.migration_algorithm != "canonical-v2-to-v3-history":
            raise WorkflowPolicyError("v3 migration algorithm is unsupported")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 3,
            "policy_version": 3,
            "authority": "offline-workflow-policy-only",
            "runtime_authority": "none",
            "promotion": "none",
            "workflow_sha256": self.workflow_sha256,
            "status": self.status,
            "violations": list(self.violations),
            "source_receipt_sha256": self.source_receipt_sha256,
            "migration_algorithm": self.migration_algorithm,
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()

    @classmethod
    def from_bytes(cls, data: bytes) -> "WorkflowPolicyReceiptV3":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WorkflowPolicyError("invalid v3 workflow receipt") from exc
        expected = {
            "schema_version", "policy_version", "authority", "runtime_authority",
            "promotion", "workflow_sha256", "status", "violations",
            "source_receipt_sha256", "migration_algorithm",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise WorkflowPolicyError("v3 workflow receipt has unexpected fields")
        if (
            doc["schema_version"] != 3
            or doc["policy_version"] != 3
            or doc["authority"] != "offline-workflow-policy-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
            or not isinstance(doc["violations"], list)
        ):
            raise WorkflowPolicyError("v3 workflow receipt boundary is invalid")
        return cls(
            doc["workflow_sha256"],
            doc["status"],
            tuple(doc["violations"]),
            doc["source_receipt_sha256"],
            doc["migration_algorithm"],
        )


@dataclass(frozen=True)
class WorkflowReceiptMigrationHistoryEntry:
    index: int
    previous_entry_sha256: str
    source_policy_version: int
    target_policy_version: int
    workflow_sha256: str
    status: str
    violations_sha256: str
    source_receipt_sha256: str
    target_receipt_sha256: str
    entry_sha256: str

    def __post_init__(self) -> None:
        if type(self.index) is not int or self.index <= 0:
            raise WorkflowPolicyError("migration history index must be positive")
        if self.target_policy_version != self.source_policy_version + 1:
            raise WorkflowPolicyError("migration history versions must be contiguous")
        if self.status not in {"valid", "invalid"}:
            raise WorkflowPolicyError("migration history status is invalid")
        for value, name in (
            (self.previous_entry_sha256, "previous entry"),
            (self.workflow_sha256, "workflow"),
            (self.violations_sha256, "violations"),
            (self.source_receipt_sha256, "source receipt"),
            (self.target_receipt_sha256, "target receipt"),
            (self.entry_sha256, "entry"),
        ):
            _hash(value, name)
        expected = hashlib.sha256(_canonical(self.core_dict())).hexdigest()
        if expected != self.entry_sha256:
            raise WorkflowPolicyError("migration history entry hash mismatch")

    def core_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "index": self.index,
            "previous_entry_sha256": self.previous_entry_sha256,
            "source_policy_version": self.source_policy_version,
            "target_policy_version": self.target_policy_version,
            "workflow_sha256": self.workflow_sha256,
            "status": self.status,
            "violations_sha256": self.violations_sha256,
            "source_receipt_sha256": self.source_receipt_sha256,
            "target_receipt_sha256": self.target_receipt_sha256,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.core_dict(), "entry_sha256": self.entry_sha256}

    @classmethod
    def build(
        cls,
        index: int,
        previous_entry_sha256: str,
        source_policy_version: int,
        target_policy_version: int,
        workflow_sha256: str,
        status: str,
        violations_sha256: str,
        source_receipt_sha256: str,
        target_receipt_sha256: str,
    ) -> "WorkflowReceiptMigrationHistoryEntry":
        core = {
            "schema_version": 1,
            "index": index,
            "previous_entry_sha256": previous_entry_sha256,
            "source_policy_version": source_policy_version,
            "target_policy_version": target_policy_version,
            "workflow_sha256": workflow_sha256,
            "status": status,
            "violations_sha256": violations_sha256,
            "source_receipt_sha256": source_receipt_sha256,
            "target_receipt_sha256": target_receipt_sha256,
        }
        return cls(
            index,
            previous_entry_sha256,
            source_policy_version,
            target_policy_version,
            workflow_sha256,
            status,
            violations_sha256,
            source_receipt_sha256,
            target_receipt_sha256,
            hashlib.sha256(_canonical(core)).hexdigest(),
        )

    @classmethod
    def from_dict(cls, doc: Any) -> "WorkflowReceiptMigrationHistoryEntry":
        expected = {
            "schema_version", "index", "previous_entry_sha256",
            "source_policy_version", "target_policy_version", "workflow_sha256",
            "status", "violations_sha256", "source_receipt_sha256",
            "target_receipt_sha256", "entry_sha256",
        }
        if not isinstance(doc, dict) or set(doc) != expected or doc["schema_version"] != 1:
            raise WorkflowPolicyError("migration history entry boundary is invalid")
        return cls(
            doc["index"],
            doc["previous_entry_sha256"],
            doc["source_policy_version"],
            doc["target_policy_version"],
            doc["workflow_sha256"],
            doc["status"],
            doc["violations_sha256"],
            doc["source_receipt_sha256"],
            doc["target_receipt_sha256"],
            doc["entry_sha256"],
        )


@dataclass(frozen=True)
class WorkflowReceiptMigrationHistory:
    initial_policy_version: int
    final_policy_version: int
    workflow_sha256: str
    status: str
    violations_sha256: str
    entries: tuple[WorkflowReceiptMigrationHistoryEntry, ...]

    def __post_init__(self) -> None:
        if not self.entries:
            raise WorkflowPolicyError("migration history requires entries")
        _hash(self.workflow_sha256, "migration history workflow")
        _hash(self.violations_sha256, "migration history violations")
        if self.status not in {"valid", "invalid"}:
            raise WorkflowPolicyError("migration history status is invalid")
        previous = _ZERO_HASH
        source_version = self.initial_policy_version
        source_receipt = self.entries[0].source_receipt_sha256
        for index, entry in enumerate(self.entries, start=1):
            if (
                entry.index != index
                or entry.previous_entry_sha256 != previous
                or entry.source_policy_version != source_version
                or entry.workflow_sha256 != self.workflow_sha256
                or entry.status != self.status
                or entry.violations_sha256 != self.violations_sha256
                or (index > 1 and entry.source_receipt_sha256 != source_receipt)
            ):
                raise WorkflowPolicyError("migration history continuity failed")
            previous = entry.entry_sha256
            source_version = entry.target_policy_version
            source_receipt = entry.target_receipt_sha256
        if source_version != self.final_policy_version:
            raise WorkflowPolicyError("migration history final version mismatch")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "offline-workflow-receipt-migration-history-only",
            "runtime_authority": "none",
            "promotion": "none",
            "initial_policy_version": self.initial_policy_version,
            "final_policy_version": self.final_policy_version,
            "workflow_sha256": self.workflow_sha256,
            "status": self.status,
            "violations_sha256": self.violations_sha256,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()

    @classmethod
    def from_bytes(cls, data: bytes) -> "WorkflowReceiptMigrationHistory":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WorkflowPolicyError("invalid workflow receipt migration history") from exc
        expected = {
            "schema_version", "authority", "runtime_authority", "promotion",
            "initial_policy_version", "final_policy_version", "workflow_sha256",
            "status", "violations_sha256", "entries",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise WorkflowPolicyError("migration history has unexpected fields")
        if (
            doc["schema_version"] != 1
            or doc["authority"] != "offline-workflow-receipt-migration-history-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
            or not isinstance(doc["entries"], list)
        ):
            raise WorkflowPolicyError("migration history boundary is invalid")
        return cls(
            doc["initial_policy_version"],
            doc["final_policy_version"],
            doc["workflow_sha256"],
            doc["status"],
            doc["violations_sha256"],
            tuple(
                WorkflowReceiptMigrationHistoryEntry.from_dict(item)
                for item in doc["entries"]
            ),
        )


def migrate_workflow_policy_receipt_v2_to_v3(
    source: WorkflowPolicyReceiptV2,
) -> WorkflowPolicyReceiptV3:
    return WorkflowPolicyReceiptV3(
        source.workflow_sha256,
        source.status,
        source.violations,
        source.sha256,
    )


def build_workflow_receipt_migration_history(
    source_v1: WorkflowPolicyReceipt,
    target_v2: WorkflowPolicyReceiptV2,
) -> tuple[WorkflowPolicyReceiptV3, WorkflowReceiptMigrationHistory]:
    if (
        target_v2.workflow_sha256 != source_v1.workflow_sha256
        or target_v2.status != source_v1.status
        or target_v2.violations != source_v1.violations
        or target_v2.source_receipt_sha256 != source_v1.sha256
    ):
        raise WorkflowPolicyError("v1-to-v2 receipt continuity failed")
    target_v3 = migrate_workflow_policy_receipt_v2_to_v3(target_v2)
    violations_sha = _violations_sha(source_v1.violations)
    first = WorkflowReceiptMigrationHistoryEntry.build(
        1,
        _ZERO_HASH,
        1,
        2,
        source_v1.workflow_sha256,
        source_v1.status,
        violations_sha,
        source_v1.sha256,
        target_v2.sha256,
    )
    second = WorkflowReceiptMigrationHistoryEntry.build(
        2,
        first.entry_sha256,
        2,
        3,
        source_v1.workflow_sha256,
        source_v1.status,
        violations_sha,
        target_v2.sha256,
        target_v3.sha256,
    )
    history = WorkflowReceiptMigrationHistory(
        1,
        3,
        source_v1.workflow_sha256,
        source_v1.status,
        violations_sha,
        (first, second),
    )
    return target_v3, history


def verify_workflow_receipt_migration_history(
    source_v1: WorkflowPolicyReceipt,
    target_v2: WorkflowPolicyReceiptV2,
    target_v3: WorkflowPolicyReceiptV3,
    history: WorkflowReceiptMigrationHistory,
) -> bool:
    expected_v3, expected_history = build_workflow_receipt_migration_history(
        source_v1,
        target_v2,
    )
    if target_v3 != expected_v3 or history != expected_history:
        raise WorkflowPolicyError("workflow receipt migration history mismatch")
    return True
