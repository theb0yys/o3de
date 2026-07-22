import unittest
from pathlib import Path

from semantic_repair import (
    RepairError,
    SnapshotReplayWindowReceipt,
    build_replay_window_sequence_proof,
    verify_replay_window_sequence_proof,
)

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "api_v2"
    / "replay-window-sequence-proof.json"
)


class ReplayWindowSequenceProofTests(unittest.TestCase):
    def _receipts(self):
        return (
            SnapshotReplayWindowReceipt(
                2,
                4,
                64,
                2,
                "a" * 64,
                "b" * 64,
                "accepted",
            ),
            SnapshotReplayWindowReceipt(
                4,
                4,
                64,
                0,
                "c" * 64,
                "c" * 64,
                "already-current",
            ),
            SnapshotReplayWindowReceipt(
                4,
                3,
                64,
                -1,
                "c" * 64,
                "d" * 64,
                "replayed-stale",
            ),
            SnapshotReplayWindowReceipt(
                4,
                70,
                64,
                66,
                "c" * 64,
                "e" * 64,
                "replay-window-exceeded",
            ),
        )

    def test_sequence_proof_matches_golden(self):
        proof = build_replay_window_sequence_proof(
            self._receipts()
        )
        self.assertEqual(proof.to_bytes(), FIXTURE.read_bytes())
        self.assertEqual(proof.initial_generation, 2)
        self.assertEqual(proof.final_generation, 4)
        self.assertTrue(
            verify_replay_window_sequence_proof(
                proof,
                self._receipts(),
            )
        )

    def test_sequence_discontinuity_fails_closed(self):
        receipts = list(self._receipts())
        receipts[1] = SnapshotReplayWindowReceipt(
            3,
            4,
            64,
            1,
            "c" * 64,
            "c" * 64,
            "accepted",
        )
        with self.assertRaises(RepairError):
            build_replay_window_sequence_proof(receipts)


if __name__ == "__main__":
    unittest.main()
