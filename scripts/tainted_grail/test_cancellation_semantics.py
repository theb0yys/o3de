import json
import tempfile
import unittest
from pathlib import Path

from semantic_repair import (
    CancellationRequested,
    CancellationToken,
    CrashRecoveryJournal,
    MappingTransaction,
    MountConversionTransaction,
    StateTransitionError,
    SyntheticMountState,
    TransactionPhase,
    TypedFieldAdapter,
)


class CancellationSemanticsTests(unittest.TestCase):
    def test_mapping_cancel_before_commit_restores_original(self):
        record = {"quantity": 2}
        tx = MappingTransaction(
            TypedFieldAdapter("profile", "item", "quantity", int),
            record,
            "profile",
            "item",
            9,
        )
        tx.prepare()
        token = CancellationToken()
        token.request("operator cancelled")
        with self.assertRaises(CancellationRequested):
            tx.commit(cancellation=token)
        self.assertEqual(record["quantity"], 2)
        self.assertEqual(tx.phase, TransactionPhase.CANCELLED)
        self.assertNotIn(TransactionPhase.FAILED, tx.history)

    def test_mount_cancel_after_stage_restores_exact_snapshot_and_journals_cancel(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = CrashRecoveryJournal(Path(tmp) / "cancel.jsonl")
            state = SyntheticMountState(
                None,
                ("mount", "pet"),
                {"mount_kind": "none"},
                {"follow": True, "combat": True},
                [],
            )
            before = json.dumps(state.__dict__, sort_keys=True)
            tx = MountConversionTransaction(state, journal=journal)
            tx.prepare()
            token = CancellationToken()

            def after_stage(stage):
                if stage == "movement":
                    token.request("scene changed")

            with self.assertRaises(CancellationRequested):
                tx.commit(
                    wolf_id="wolf",
                    cancellation=token,
                    after_stage=after_stage,
                )
            self.assertEqual(json.dumps(state.__dict__, sort_keys=True), before)
            self.assertEqual(tx.phase, TransactionPhase.CANCELLED)
            phases = [record.phase for record in journal.read_records()[0]]
            self.assertIn("cancel-requested", phases)
            self.assertIn("cancelling", phases)
            self.assertIn("cancelled", phases)
            self.assertNotIn("failed", phases)

    def test_committed_transaction_cannot_be_cancelled(self):
        record = {"quantity": 2}
        tx = MappingTransaction(
            TypedFieldAdapter("profile", "item", "quantity", int),
            record,
            "profile",
            "item",
            3,
        )
        tx.prepare()
        tx.commit()
        with self.assertRaises(StateTransitionError):
            tx.cancel("too late")


if __name__ == "__main__":
    unittest.main()
