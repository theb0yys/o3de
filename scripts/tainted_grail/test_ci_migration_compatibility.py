import unittest
from pathlib import Path

from semantic_repair.ci_migration import (
    migrate_workflow_policy_receipt_v1_to_v2,
)
from semantic_repair.ci_migration_compatibility import (
    WorkflowMigrationCompatibilityMatrix,
    build_workflow_migration_compatibility_matrix,
    verify_workflow_migration_compatibility_matrix,
)
from semantic_repair.ci_migration_history import (
    build_workflow_receipt_migration_history,
)
from semantic_repair.ci_policy import build_offline_workflow_receipt
from semantic_repair.errors import WorkflowPolicyError

WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "semantic-hook-offline.yml"
FIXTURES = Path(__file__).parent / "fixtures" / "ci"

class WorkflowMigrationCompatibilityTests(unittest.TestCase):
    def _build(self, text):
        source = build_offline_workflow_receipt(text)
        target_v2 = migrate_workflow_policy_receipt_v1_to_v2(source)
        target_v3, history = build_workflow_receipt_migration_history(
            source, target_v2
        )
        matrix = build_workflow_migration_compatibility_matrix(
            source, target_v2, target_v3, history
        )
        return source, target_v2, target_v3, history, matrix

    def test_valid_matrix_matches_golden(self):
        objects = self._build(WORKFLOW.read_text(encoding="utf-8"))
        source, target_v2, target_v3, history, matrix = objects
        self.assertEqual(
            matrix.to_bytes(),
            (FIXTURES / "workflow-migration-compatibility-valid.json").read_bytes(),
        )
        self.assertEqual(
            WorkflowMigrationCompatibilityMatrix.from_bytes(matrix.to_bytes()),
            matrix,
        )
        self.assertTrue(
            verify_workflow_migration_compatibility_matrix(
                source, target_v2, target_v3, history, matrix
            )
        )
        downgrade = next(
            cell for cell in matrix.cells
            if cell.source_policy_version == 3
            and cell.target_policy_version == 1
        )
        self.assertFalse(downgrade.compatible)
        self.assertEqual(downgrade.migration_path, ())

    def test_invalid_matrix_preserves_violation_identity(self):
        text = WORKFLOW.read_text(encoding="utf-8").replace(
            "contents: read", "contents: write"
        )
        *_, matrix = self._build(text)
        self.assertEqual(
            matrix.to_bytes(),
            (FIXTURES / "workflow-migration-compatibility-invalid.json").read_bytes(),
        )
        self.assertEqual(matrix.status, "invalid")

    def test_incomplete_matrix_fails_closed(self):
        *_, matrix = self._build(WORKFLOW.read_text(encoding="utf-8"))
        with self.assertRaises(WorkflowPolicyError):
            WorkflowMigrationCompatibilityMatrix(
                matrix.workflow_sha256,
                matrix.status,
                matrix.violations_sha256,
                matrix.policy_versions,
                matrix.cells[:-1],
            )

if __name__ == "__main__":
    unittest.main()
