import unittest
from pathlib import Path
from semantic_repair.abandonment_appeal import AbandonmentDecisionAppeal
from semantic_repair.appeal_history import (
    AbandonmentAppealLifecycleHistory,
    AbandonmentAppealResolutionRecord,
    AbandonmentAppealWithdrawalRecord,
    build_abandonment_appeal_lifecycle_history,
    build_abandonment_appeal_resolution,
    build_abandonment_appeal_withdrawal,
    verify_abandonment_appeal_lifecycle_history,
)
from semantic_repair.errors import RepairError

FIXTURES = Path(__file__).parent / "fixtures" / "abandonment"

class AppealHistoryTests(unittest.TestCase):
    def _appeal(self):
        return AbandonmentDecisionAppeal(
            "tg.synthetic.batch013.appeal-001", "decision", "5"*64,
            "journal:synthetic", 3, ("reviewer-a", "reviewer-b"),
            "reconsider observation",
        )

    def test_withdrawal_resolution_history_goldens(self):
        appeal = self._appeal()
        withdrawal = build_abandonment_appeal_withdrawal(
            appeal, ("reviewer-c", "reviewer-a"),
            "appeal withdrawn after clarification",
        )
        resolution = build_abandonment_appeal_resolution(
            appeal, ("reviewer-c", "reviewer-b"), "closed-withdrawn",
            "close withdrawn appeal", withdrawal=withdrawal,
        )
        history = build_abandonment_appeal_lifecycle_history(
            appeal, withdrawal=withdrawal, resolution=resolution
        )
        self.assertEqual(
            withdrawal.to_bytes(),
            (FIXTURES / "appeal-withdrawal.json").read_bytes(),
        )
        self.assertEqual(
            resolution.to_bytes(),
            (FIXTURES / "appeal-resolution.json").read_bytes(),
        )
        self.assertEqual(
            history.to_bytes(),
            (FIXTURES / "appeal-lifecycle-history.json").read_bytes(),
        )
        self.assertEqual(
            AbandonmentAppealWithdrawalRecord.from_bytes(
                withdrawal.to_bytes()
            ),
            withdrawal,
        )
        self.assertEqual(
            AbandonmentAppealResolutionRecord.from_bytes(
                resolution.to_bytes()
            ),
            resolution,
        )
        self.assertEqual(
            AbandonmentAppealLifecycleHistory.from_bytes(
                history.to_bytes()
            ),
            history,
        )
        self.assertTrue(
            verify_abandonment_appeal_lifecycle_history(
                appeal, history,
                withdrawal=withdrawal, resolution=resolution,
            )
        )

    def test_withdrawn_appeal_cannot_use_nonwithdrawn_outcome(self):
        appeal = self._appeal()
        withdrawal = build_abandonment_appeal_withdrawal(
            appeal, ("a", "b"), "withdraw"
        )
        with self.assertRaises(RepairError):
            build_abandonment_appeal_resolution(
                appeal, ("a", "b"), "upheld-manual-review",
                "invalid", withdrawal=withdrawal,
            )

if __name__ == "__main__":
    unittest.main()
