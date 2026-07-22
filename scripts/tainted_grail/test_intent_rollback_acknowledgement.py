import unittest
from pathlib import Path
from semantic_repair.dependency_rollback import (
    IntentPartialRollbackAction,
    IntentPartialRollbackPlan,
)
from semantic_repair.errors import PublicationIntentError
from semantic_repair.rollback_acknowledgement import (
    IntentRollbackPlanAcknowledgementReceipt,
    build_intent_rollback_plan_acknowledgement,
    verify_intent_rollback_plan_acknowledgement,
)

FIXTURES = Path(__file__).parent / "fixtures" / "intent_dependencies"

class RollbackAcknowledgementTests(unittest.TestCase):
    def _plan(self):
        return IntentPartialRollbackPlan(
            "4"*64,
            ("intent-a",),
            ("intent-a", "intent-b", "intent-c"),
            ("intent-c", "intent-b", "intent-a"),
            (
                IntentPartialRollbackAction(
                    "intent-c", "intent-prepared",
                    "cancel-and-rollback-prepared", (),
                ),
                IntentPartialRollbackAction(
                    "intent-b", "intent-committed",
                    "rollback-committed", ("intent-c",),
                ),
                IntentPartialRollbackAction(
                    "intent-a", "intent-committed",
                    "rollback-committed", ("intent-b",),
                ),
            ),
        )

    def test_acknowledgement_chain_goldens(self):
        plan = self._plan()
        first = build_intent_rollback_plan_acknowledgement(
            plan, "reviewer-a",
            "acknowledged-for-manual-execution-review",
            "plan reviewed",
            acknowledgement_id="tg.synthetic.batch013.rollback-ack-001",
            acknowledgement_index=1,
        )
        second = build_intent_rollback_plan_acknowledgement(
            plan, "reviewer-b",
            "declined-for-manual-execution-review",
            "requires revised plan",
            acknowledgement_id="tg.synthetic.batch013.rollback-ack-002",
            acknowledgement_index=2,
            previous_acknowledgement=first,
        )
        self.assertEqual(
            first.to_bytes(),
            (FIXTURES / "rollback-plan-acknowledgement-001.json").read_bytes(),
        )
        self.assertEqual(
            second.to_bytes(),
            (FIXTURES / "rollback-plan-acknowledgement-002.json").read_bytes(),
        )
        self.assertEqual(
            IntentRollbackPlanAcknowledgementReceipt.from_bytes(
                second.to_bytes()
            ),
            second,
        )
        self.assertTrue(
            verify_intent_rollback_plan_acknowledgement(
                plan, second, previous_acknowledgement=first
            )
        )

    def test_chain_cannot_switch_plans(self):
        plan = self._plan()
        first = build_intent_rollback_plan_acknowledgement(
            plan, "reviewer-a",
            "acknowledged-for-manual-execution-review",
            "plan reviewed", acknowledgement_id="a",
            acknowledgement_index=1,
        )
        other = IntentPartialRollbackPlan(
            "9"*64, plan.trigger_intents, plan.affected_intents,
            plan.rollback_order, plan.actions,
        )
        with self.assertRaises(PublicationIntentError):
            build_intent_rollback_plan_acknowledgement(
                other, "reviewer-b",
                "acknowledged-for-manual-execution-review",
                "invalid", acknowledgement_id="b",
                acknowledgement_index=2,
                previous_acknowledgement=first,
            )

if __name__ == "__main__":
    unittest.main()
