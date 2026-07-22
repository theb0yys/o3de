import unittest
from pathlib import Path

from semantic_repair import WorkflowPolicyError, validate_offline_workflow

WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "semantic-hook-offline.yml"


class WorkflowPolicyTests(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_committed_workflow_is_read_only_and_non_publishing(self):
        validate_offline_workflow(self.text)

    def test_write_permission_is_rejected(self):
        with self.assertRaises(WorkflowPolicyError):
            validate_offline_workflow(self.text.replace("contents: read", "contents: write"))

    def test_extra_write_permission_is_rejected(self):
        mutated = self.text.replace(
            "  contents: read",
            "  contents: read\n  packages: write",
        )
        with self.assertRaises(WorkflowPolicyError):
            validate_offline_workflow(mutated)

    def test_artifact_publication_is_rejected(self):
        mutated = self.text + "\n      - uses: actions/upload-artifact@v4\n"
        with self.assertRaises(WorkflowPolicyError):
            validate_offline_workflow(mutated)

    def test_secret_reference_is_rejected(self):
        mutated = self.text + "\n      - run: echo ${{ secrets.SYNTHETIC }}\n"
        with self.assertRaises(WorkflowPolicyError):
            validate_offline_workflow(mutated)


if __name__ == "__main__":
    unittest.main()
