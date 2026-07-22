import unittest
from pathlib import Path

from semantic_repair import (
    WorkflowPolicyError,
    WorkflowReceiptMigrationFixture,
    build_offline_workflow_receipt,
    build_workflow_receipt_migration_fixture,
    migrate_workflow_policy_receipt_v1_to_v2,
    verify_workflow_receipt_migration,
)

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "semantic-hook-offline.yml"
FIXTURES = Path(__file__).parent / "fixtures" / "ci"


class WorkflowReceiptMigrationTests(unittest.TestCase):
    def test_valid_workflow_migration_matches_fixture(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        source = build_offline_workflow_receipt(text)
        target = migrate_workflow_policy_receipt_v1_to_v2(source)
        fixture = build_workflow_receipt_migration_fixture(
            "tg.synthetic.batch011.workflow-receipt-migration-valid",
            source,
        )
        self.assertEqual(
            fixture.to_bytes(),
            (
                FIXTURES
                / "workflow-receipt-migration-valid.json"
            ).read_bytes(),
        )
        self.assertTrue(
            verify_workflow_receipt_migration(
                source,
                target,
                fixture,
            )
        )
        self.assertEqual(target.status, "valid")

    def test_invalid_workflow_migration_preserves_violations(self):
        text = WORKFLOW.read_text(encoding="utf-8").replace(
            "contents: read",
            "contents: write",
        )
        source = build_offline_workflow_receipt(text)
        target = migrate_workflow_policy_receipt_v1_to_v2(source)
        fixture = build_workflow_receipt_migration_fixture(
            "tg.synthetic.batch011.workflow-receipt-migration-invalid",
            source,
        )
        self.assertEqual(
            fixture.to_bytes(),
            (
                FIXTURES
                / "workflow-receipt-migration-invalid.json"
            ).read_bytes(),
        )
        self.assertTrue(
            verify_workflow_receipt_migration(
                source,
                target,
                fixture,
            )
        )
        self.assertEqual(target.status, "invalid")
        self.assertEqual(target.violations, source.violations)

    def test_migration_tamper_fails_closed(self):
        source = build_offline_workflow_receipt(
            WORKFLOW.read_text(encoding="utf-8")
        )
        target = migrate_workflow_policy_receipt_v1_to_v2(source)
        fixture = WorkflowReceiptMigrationFixture(
            "tampered",
            1,
            2,
            source.workflow_sha256,
            source.sha256,
            "0" * 64,
            source.status,
        )
        with self.assertRaises(WorkflowPolicyError):
            verify_workflow_receipt_migration(
                source,
                target,
                fixture,
            )


if __name__ == "__main__":
    unittest.main()
