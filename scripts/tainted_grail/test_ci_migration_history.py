import hashlib
import unittest
from pathlib import Path

from semantic_repair.ci_migration import WorkflowPolicyReceiptV2
from semantic_repair.ci_migration_history import (
    WorkflowPolicyReceiptV3,
    WorkflowReceiptMigrationHistory,
    build_workflow_receipt_migration_history,
    verify_workflow_receipt_migration_history,
)
from semantic_repair.ci_policy import WorkflowPolicyReceipt
from semantic_repair.errors import WorkflowPolicyError

FIXTURES = Path(__file__).parent / "fixtures" / "ci"
WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "semantic-hook-offline.yml"
VIOLATIONS = (
    "workflow permissions must be exactly contents: read",
    "offline workflow contains forbidden publication token: contents: write",
)


def source_receipt(text, invalid=False):
    return WorkflowPolicyReceipt(
        hashlib.sha256(text.encode()).hexdigest(),
        "invalid" if invalid else "valid",
        VIOLATIONS if invalid else (),
    )


class MigrationHistoryTests(unittest.TestCase):
    def test_valid_history_and_v3_receipt_match_goldens(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        source = source_receipt(text)
        target_v2 = WorkflowPolicyReceiptV2(
            source.workflow_sha256, source.status, source.violations, source.sha256
        )
        target_v3, history = build_workflow_receipt_migration_history(source, target_v2)
        self.assertEqual(history.to_bytes(), (FIXTURES / "workflow-receipt-migration-history-valid.json").read_bytes())
        self.assertEqual(target_v3.to_bytes(), (FIXTURES / "workflow-policy-receipt-v3-valid.json").read_bytes())
        self.assertEqual(WorkflowReceiptMigrationHistory.from_bytes(history.to_bytes()), history)
        self.assertEqual(WorkflowPolicyReceiptV3.from_bytes(target_v3.to_bytes()), target_v3)
        self.assertTrue(verify_workflow_receipt_migration_history(source, target_v2, target_v3, history))

    def test_invalid_history_preserves_complete_violation_set(self):
        text = WORKFLOW.read_text(encoding="utf-8").replace("contents: read", "contents: write")
        source = source_receipt(text, invalid=True)
        target_v2 = WorkflowPolicyReceiptV2(
            source.workflow_sha256, source.status, source.violations, source.sha256
        )
        target_v3, history = build_workflow_receipt_migration_history(source, target_v2)
        self.assertEqual(history.to_bytes(), (FIXTURES / "workflow-receipt-migration-history-invalid.json").read_bytes())
        self.assertEqual(target_v3.to_bytes(), (FIXTURES / "workflow-policy-receipt-v3-invalid.json").read_bytes())
        self.assertEqual(target_v3.violations, VIOLATIONS)

    def test_broken_v1_to_v2_link_fails_closed(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        source = source_receipt(text)
        target_v2 = WorkflowPolicyReceiptV2(
            source.workflow_sha256, source.status, source.violations, "0" * 64
        )
        with self.assertRaises(WorkflowPolicyError):
            build_workflow_receipt_migration_history(source, target_v2)


if __name__ == "__main__":
    unittest.main()
