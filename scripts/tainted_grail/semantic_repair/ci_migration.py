"""Deterministic migration fixtures for offline workflow policy receipts."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .ci_policy import WorkflowPolicyReceipt
from .errors import WorkflowPolicyError


def _canonical(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


@dataclass(frozen=True)
class WorkflowPolicyReceiptV2:
    workflow_sha256: str
    status: str
    violations: tuple[str, ...]
    source_receipt_sha256: str
    migration_algorithm: str = "canonical-v1-to-v2"

    def __post_init__(self) -> None:
        if any(
            not isinstance(value, str) or len(value) != 64
            for value in (
                self.workflow_sha256,
                self.source_receipt_sha256,
            )
        ):
            raise WorkflowPolicyError(
                "migrated workflow receipt hash is invalid"
            )
        if self.status not in {"valid", "invalid"}:
            raise WorkflowPolicyError(
                "migrated workflow receipt status is invalid"
            )
        if (self.status == "valid") != (not self.violations):
            raise WorkflowPolicyError(
                "migrated workflow receipt status is inconsistent"
            )
        if self.migration_algorithm != "canonical-v1-to-v2":
            raise WorkflowPolicyError(
                "migrated workflow receipt algorithm is unsupported"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 2,
            "policy_version": 2,
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
    def from_bytes(cls, data: bytes) -> "WorkflowPolicyReceiptV2":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WorkflowPolicyError(
                "invalid migrated workflow receipt"
            ) from exc
        expected = {
            "schema_version",
            "policy_version",
            "authority",
            "runtime_authority",
            "promotion",
            "workflow_sha256",
            "status",
            "violations",
            "source_receipt_sha256",
            "migration_algorithm",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise WorkflowPolicyError(
                "migrated workflow receipt has unexpected fields"
            )
        if (
            doc["schema_version"] != 2
            or doc["policy_version"] != 2
            or doc["authority"] != "offline-workflow-policy-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
            or not isinstance(doc["violations"], list)
        ):
            raise WorkflowPolicyError(
                "migrated workflow receipt boundary is invalid"
            )
        return cls(
            doc["workflow_sha256"],
            doc["status"],
            tuple(doc["violations"]),
            doc["source_receipt_sha256"],
            doc["migration_algorithm"],
        )


@dataclass(frozen=True)
class WorkflowReceiptMigrationFixture:
    fixture_id: str
    source_policy_version: int
    target_policy_version: int
    workflow_sha256: str
    source_receipt_sha256: str
    target_receipt_sha256: str
    status: str

    def __post_init__(self) -> None:
        if not isinstance(self.fixture_id, str) or not self.fixture_id.strip():
            raise WorkflowPolicyError(
                "migration fixture_id must be non-empty"
            )
        if self.source_policy_version != 1 or self.target_policy_version != 2:
            raise WorkflowPolicyError(
                "workflow receipt migration versions are unsupported"
            )
        if any(
            not isinstance(value, str) or len(value) != 64
            for value in (
                self.workflow_sha256,
                self.source_receipt_sha256,
                self.target_receipt_sha256,
            )
        ):
            raise WorkflowPolicyError(
                "workflow receipt migration hash is invalid"
            )
        if self.status not in {"valid", "invalid"}:
            raise WorkflowPolicyError(
                "workflow receipt migration status is invalid"
            )

    def to_bytes(self) -> bytes:
        return _canonical(
            {
                "schema_version": 1,
                "authority": "offline-workflow-receipt-migration-fixture-only",
                "runtime_authority": "none",
                "promotion": "none",
                "fixture_id": self.fixture_id,
                "source_policy_version": self.source_policy_version,
                "target_policy_version": self.target_policy_version,
                "workflow_sha256": self.workflow_sha256,
                "source_receipt_sha256": self.source_receipt_sha256,
                "target_receipt_sha256": self.target_receipt_sha256,
                "status": self.status,
            }
        )


def migrate_workflow_policy_receipt_v1_to_v2(
    source: WorkflowPolicyReceipt,
) -> WorkflowPolicyReceiptV2:
    return WorkflowPolicyReceiptV2(
        source.workflow_sha256,
        source.status,
        source.violations,
        source.sha256,
    )


def build_workflow_receipt_migration_fixture(
    fixture_id: str,
    source: WorkflowPolicyReceipt,
) -> WorkflowReceiptMigrationFixture:
    target = migrate_workflow_policy_receipt_v1_to_v2(source)
    return WorkflowReceiptMigrationFixture(
        fixture_id,
        1,
        2,
        source.workflow_sha256,
        source.sha256,
        target.sha256,
        source.status,
    )


def verify_workflow_receipt_migration(
    source: WorkflowPolicyReceipt,
    target: WorkflowPolicyReceiptV2,
    fixture: WorkflowReceiptMigrationFixture,
) -> bool:
    expected_target = migrate_workflow_policy_receipt_v1_to_v2(source)
    expected_fixture = build_workflow_receipt_migration_fixture(
        fixture.fixture_id,
        source,
    )
    if target != expected_target or fixture != expected_fixture:
        raise WorkflowPolicyError(
            "workflow receipt migration fixture mismatch"
        )
    return True
