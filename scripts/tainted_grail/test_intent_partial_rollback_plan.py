import unittest
from pathlib import Path

from semantic_repair.dependency_rollback import (
    IntentPartialRollbackPlan,
    build_intent_partial_rollback_plan,
    verify_intent_partial_rollback_plan,
)
from semantic_repair.errors import PublicationIntentError
from semantic_repair.intent_dependencies import IntentDependencyGraph, IntentDependencyNode

FIXTURE = Path(__file__).parent / "fixtures" / "intent_dependencies" / "partial-rollback-plan.json"


def graph():
    nodes = (
        IntentDependencyNode("a", "intent-committed", ()),
        IntentDependencyNode("b", "intent-committed", ("a",)),
        IntentDependencyNode("c", "intent-prepared", ("b",)),
        IntentDependencyNode("d", "intent-committed", ("b",)),
        IntentDependencyNode("e", "intent-prepared", ("c", "d")),
        IntentDependencyNode("f", "intent-rolled-back", ("a",)),
    )
    return IntentDependencyGraph(nodes, ("a", "b", "c", "d", "e", "f"), ("c",), ("e",))


class PartialRollbackPlanTests(unittest.TestCase):
    def test_reverse_dependency_plan_matches_golden(self):
        source = graph()
        plan = build_intent_partial_rollback_plan(source, ("b",))
        self.assertEqual(plan.to_bytes(), FIXTURE.read_bytes())
        self.assertEqual(IntentPartialRollbackPlan.from_bytes(plan.to_bytes()), plan)
        self.assertEqual(plan.rollback_order, ("e", "d", "c", "b"))
        self.assertEqual(plan.to_dict()["execution_authority"], "none")
        self.assertTrue(verify_intent_partial_rollback_plan(source, plan))

    def test_missing_trigger_fails_closed(self):
        with self.assertRaises(PublicationIntentError):
            build_intent_partial_rollback_plan(graph(), ("missing",))


if __name__ == "__main__":
    unittest.main()
