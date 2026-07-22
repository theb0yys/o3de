import unittest
from pathlib import Path
from semantic_repair.archive_retention import CheckpointArchiveTombstoneManifest
from semantic_repair.errors import CheckpointProofError
from semantic_repair.tombstone_lifecycle import (
    ArchiveRestorationReviewRecord,
    ArchiveTombstoneSupersessionRecord,
    build_archive_restoration_review,
    build_archive_tombstone_supersession,
    verify_archive_restoration_review,
    verify_archive_tombstone_supersession,
)

FIXTURES = Path(__file__).parent / "fixtures" / "checkpoint_archive"

class TombstoneLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.first = CheckpointArchiveTombstoneManifest(
            1, "tg.synthetic.archive-001", 1, "archive-001.jsonl",
            "a"*64, "b"*64, "0"*64, "retention policy",
        )
        self.second = CheckpointArchiveTombstoneManifest(
            2, "tg.synthetic.archive-001", 1, "archive-001.jsonl",
            "a"*64, "b"*64, self.first.sha256, "corrected metadata reason",
        )

    def test_supersession_and_restoration_review_goldens(self):
        record = build_archive_tombstone_supersession(
            self.first, self.second, ("reviewer-b", "reviewer-a"),
            "supersede earlier metadata",
        )
        self.assertEqual(
            record.to_bytes(),
            (FIXTURES / "tombstone-supersession.json").read_bytes(),
        )
        self.assertEqual(
            ArchiveTombstoneSupersessionRecord.from_bytes(record.to_bytes()),
            record,
        )
        self.assertTrue(
            verify_archive_tombstone_supersession(
                self.first, self.second, record
            )
        )
        review = build_archive_restoration_review(
            record,
            ("reviewer-c", "reviewer-a"),
            "review metadata visibility",
            review_id="tg.synthetic.batch013.restoration-review-001",
        )
        self.assertEqual(
            review.to_bytes(),
            (FIXTURES / "archive-restoration-review.json").read_bytes(),
        )
        self.assertEqual(
            ArchiveRestorationReviewRecord.from_bytes(review.to_bytes()),
            review,
        )
        self.assertTrue(verify_archive_restoration_review(record, review))

    def test_cross_archive_or_duplicate_reviewers_fail(self):
        other = CheckpointArchiveTombstoneManifest(
            2, "other", 1, "archive-001.jsonl",
            "a"*64, "b"*64, self.first.sha256, "different",
        )
        with self.assertRaises(CheckpointProofError):
            build_archive_tombstone_supersession(
                self.first, other, ("a", "b"), "invalid"
            )
        with self.assertRaises(CheckpointProofError):
            build_archive_tombstone_supersession(
                self.first, self.second, ("same", "same"), "invalid"
            )

if __name__ == "__main__":
    unittest.main()
