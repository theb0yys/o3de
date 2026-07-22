import tempfile
import unittest
from pathlib import Path

from semantic_repair import (
    CheckpointProofError,
    CompactionBackupLimits,
    CompactionQuotaLedger,
    reserve_compaction_backup_quota,
)

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "compaction"
    / "repeated-compaction-quota-ledger.json"
)
LIMITS = CompactionBackupLimits(
    max_operations=4,
    max_total_backup_bytes=64,
    max_single_operation_bytes=32,
)


class RepeatedCompactionQuotaTests(unittest.TestCase):
    def test_repeated_reservations_match_golden(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quota.json"
            reserve_compaction_backup_quota(
                path,
                "compact-001",
                (b"journal-one", b"proof-one"),
                limits=LIMITS,
            )
            ledger = reserve_compaction_backup_quota(
                path,
                "compact-002",
                (b"journal-two", b"chain-two"),
                limits=LIMITS,
            )
            self.assertEqual(ledger.to_bytes(), FIXTURE.read_bytes())
            self.assertEqual(
                CompactionQuotaLedger.from_bytes(path.read_bytes()),
                ledger,
            )

    def test_duplicate_and_operation_count_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quota.json"
            limits = CompactionBackupLimits(1, 16, 16)
            reserve_compaction_backup_quota(
                path,
                "one",
                (b"1234",),
                limits=limits,
            )
            with self.assertRaises(CheckpointProofError):
                reserve_compaction_backup_quota(
                    path,
                    "one",
                    (b"x",),
                    limits=limits,
                )
            with self.assertRaises(CheckpointProofError):
                reserve_compaction_backup_quota(
                    path,
                    "two",
                    (b"x",),
                    limits=limits,
                )

    def test_single_and_cumulative_bytes_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quota.json"
            limits = CompactionBackupLimits(4, 10, 6)
            with self.assertRaises(CheckpointProofError):
                reserve_compaction_backup_quota(
                    path,
                    "oversized",
                    (b"1234567",),
                    limits=limits,
                )
            reserve_compaction_backup_quota(
                path,
                "one",
                (b"123456",),
                limits=limits,
            )
            with self.assertRaises(CheckpointProofError):
                reserve_compaction_backup_quota(
                    path,
                    "two",
                    (b"12345",),
                    limits=limits,
                )


if __name__ == "__main__":
    unittest.main()
