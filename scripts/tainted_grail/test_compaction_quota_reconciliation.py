import unittest
from dataclasses import replace
from pathlib import Path
from semantic_repair.compaction_quota import (
    CompactionBackupLimits,
    CompactionQuotaLedger,
    CompactionQuotaReservation,
)
from semantic_repair.errors import CheckpointProofError
from semantic_repair.quota_lifecycle import (
    CompactionQuotaLedgerCompactionRecord,
    CompactionQuotaReleaseRecord,
)
from semantic_repair.quota_reconciliation import (
    CompactionQuotaReconciliationJournal,
    build_compaction_quota_reconciliation_journal,
    verify_compaction_quota_reconciliation_journal,
)

FIXTURE = Path(__file__).parent / "fixtures" / "compaction" / "quota-reconciliation-journal.json"

class QuotaReconciliationTests(unittest.TestCase):
    def _objects(self):
        limits = CompactionBackupLimits(8, 1024, 512)
        a = CompactionQuotaReservation("op-a", 1, 100, 100, "1"*64)
        b = CompactionQuotaReservation("op-b", 2, 200, 300, "2"*64)
        c = CompactionQuotaReservation("op-c", 3, 50, 350, "3"*64)
        source = CompactionQuotaLedger(limits, (a, b, c))
        r1 = CompactionQuotaReleaseRecord(
            1, source.sha256, "op-a", 1, 100, a.operation_sha256,
            "0"*64, "backup retired",
        )
        r2 = CompactionQuotaReleaseRecord(
            2, source.sha256, "op-c", 3, 50, c.operation_sha256,
            r1.sha256, "backup retired",
        )
        compacted = CompactionQuotaLedger(
            limits,
            (CompactionQuotaReservation(
                "op-b", 1, 200, 200, b.operation_sha256
            ),),
        )
        record = CompactionQuotaLedgerCompactionRecord(
            source.sha256, (r1.sha256, r2.sha256), ("op-a", "op-c"),
            150, ("op-b",), 200, compacted.sha256,
        )
        return source, (r1, r2), compacted, record

    def test_reconciliation_golden_and_round_trip(self):
        source, releases, compacted, record = self._objects()
        journal = build_compaction_quota_reconciliation_journal(
            source, releases, compacted, record
        )
        self.assertEqual(journal.to_bytes(), FIXTURE.read_bytes())
        self.assertEqual(
            CompactionQuotaReconciliationJournal.from_bytes(
                journal.to_bytes()
            ),
            journal,
        )
        self.assertTrue(
            verify_compaction_quota_reconciliation_journal(
                source, releases, compacted, record, journal
            )
        )

    def test_tampered_balance_fails(self):
        source, releases, compacted, record = self._objects()
        journal = build_compaction_quota_reconciliation_journal(
            source, releases, compacted, record
        )
        with self.assertRaises(CheckpointProofError):
            replace(journal, remaining_backup_bytes=201)

if __name__ == "__main__":
    unittest.main()
