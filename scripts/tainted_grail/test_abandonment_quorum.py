import tempfile
import unittest
from pathlib import Path

from semantic_repair.abandonment import build_lock_abandonment_review
from semantic_repair.abandonment_quorum import (
    build_lock_abandonment_decision,
    verify_abandonment_decision_against_lock,
)
from semantic_repair.errors import RepairError
from semantic_repair.ownership import ExclusiveResourceLock

FIXTURE = Path(__file__).parent / "fixtures" / "abandonment" / "quorum-decision.json"


class AbandonmentQuorumTests(unittest.TestCase):
    def test_two_distinct_reviews_form_non_mutating_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = ExclusiveResourceLock(Path(tmp) / "resource.lock", "resource")
            lock.acquire("stranded-owner")
            lock_before = lock.path.read_bytes()
            a = build_lock_abandonment_review(lock, "reviewer-a", "owner unavailable")
            b = build_lock_abandonment_review(lock, "reviewer-b", "manual recovery required")
            decision = build_lock_abandonment_decision((b, a), required_quorum=2)
            self.assertTrue(verify_abandonment_decision_against_lock(lock, decision))
            self.assertEqual(lock.path.read_bytes(), lock_before)
            self.assertEqual([r.reviewer_id for r in decision.reviews], ["reviewer-a", "reviewer-b"])
            self.assertEqual(decision.to_bytes(), FIXTURE.read_bytes())

    def test_duplicate_or_insufficient_reviewers_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = ExclusiveResourceLock(Path(tmp) / "resource.lock", "resource")
            lock.acquire("owner")
            review = build_lock_abandonment_review(lock, "reviewer", "reason")
            with self.assertRaises(RepairError):
                build_lock_abandonment_decision((review,), required_quorum=2)
            with self.assertRaises(RepairError):
                build_lock_abandonment_decision((review, review), required_quorum=2)


if __name__ == "__main__":
    unittest.main()
