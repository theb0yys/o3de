import tempfile
import unittest
from pathlib import Path

from semantic_repair.errors import PublicationIntentError, SimulatedCrash
from semantic_repair.journal import CrashRecoveryJournal
from semantic_repair.publication_intent import (
    MultiFileIntentPublisher,
    PublicationTarget,
)


class PublicationIntentTests(unittest.TestCase):
    def test_multi_file_commit_and_crash_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journal = CrashRecoveryJournal(root / "intent.jsonl")
            lease = journal.acquire("writer")
            publisher = MultiFileIntentPublisher(root / "out", journal)

            receipt = publisher.publish_owned(
                lease,
                "intent-ok",
                (
                    PublicationTarget("a.txt", b"a1"),
                    PublicationTarget("nested/b.txt", b"b1"),
                ),
            )
            self.assertEqual(receipt.status, "committed")
            self.assertEqual((root / "out" / "a.txt").read_bytes(), b"a1")
            self.assertEqual((root / "out" / "nested" / "b.txt").read_bytes(), b"b1")

            (root / "out" / "a.txt").write_bytes(b"a-old")
            (root / "out" / "nested" / "b.txt").write_bytes(b"b-old")
            with self.assertRaises(SimulatedCrash):
                publisher.publish_owned(
                    lease,
                    "intent-crash",
                    (
                        PublicationTarget("a.txt", b"a2"),
                        PublicationTarget("nested/b.txt", b"b2"),
                    ),
                    crash_after_target=1,
                )
            self.assertEqual((root / "out" / "a.txt").read_bytes(), b"a2")
            recovered = publisher.recover_owned(lease, "intent-crash")
            self.assertEqual(recovered.status, "rolled-back")
            self.assertEqual((root / "out" / "a.txt").read_bytes(), b"a-old")
            self.assertEqual((root / "out" / "nested" / "b.txt").read_bytes(), b"b-old")
            plan = journal.recovery_plan()
            steps = {step.transaction_id: step.action.value for step in plan.steps}
            self.assertEqual(steps["intent-ok"], "none")
            self.assertEqual(steps["intent-crash"], "none")

    def test_unknown_post_crash_bytes_require_manual_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journal = CrashRecoveryJournal(root / "intent.jsonl")
            lease = journal.acquire("writer")
            publisher = MultiFileIntentPublisher(root / "out", journal)
            with self.assertRaises(SimulatedCrash):
                publisher.publish_owned(
                    lease,
                    "intent-unknown",
                    (PublicationTarget("a.txt", b"after"),),
                    crash_after_target=1,
                )
            (root / "out" / "a.txt").write_bytes(b"third-state")
            with self.assertRaises(PublicationIntentError):
                publisher.recover_owned(lease, "intent-unknown")
            self.assertEqual((root / "out" / "a.txt").read_bytes(), b"third-state")


if __name__ == "__main__":
    unittest.main()
