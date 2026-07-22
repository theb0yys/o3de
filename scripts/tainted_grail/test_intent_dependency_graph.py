import unittest
from pathlib import Path

from semantic_repair import (
    IntentDependencyNode,
    PublicationIntentError,
    build_intent_dependency_graph,
)

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "intent_dependencies"
    / "publication-intent-dependency-graph.json"
)


class IntentDependencyGraphTests(unittest.TestCase):
    def _nodes(self):
        return (
            IntentDependencyNode("assets", "intent-committed"),
            IntentDependencyNode(
                "catalog",
                "intent-prepared",
                ("assets",),
            ),
            IntentDependencyNode(
                "localization",
                "intent-rolled-back",
            ),
            IntentDependencyNode(
                "release-index",
                "intent-prepared",
                ("catalog", "localization"),
            ),
        )

    def test_graph_matches_golden_and_orders_deterministically(self):
        graph = build_intent_dependency_graph(reversed(self._nodes()))
        self.assertEqual(graph.to_bytes(), FIXTURE.read_bytes())
        self.assertEqual(
            graph.topological_order,
            ("assets", "catalog", "localization", "release-index"),
        )
        self.assertEqual(graph.runnable_intents, ("catalog",))
        self.assertEqual(graph.blocked_intents, ("release-index",))

    def test_cycle_fails_closed(self):
        with self.assertRaises(PublicationIntentError):
            build_intent_dependency_graph(
                (
                    IntentDependencyNode(
                        "a",
                        "intent-prepared",
                        ("b",),
                    ),
                    IntentDependencyNode(
                        "b",
                        "intent-prepared",
                        ("a",),
                    ),
                )
            )

    def test_missing_dependency_fails_closed(self):
        with self.assertRaises(PublicationIntentError):
            build_intent_dependency_graph(
                (
                    IntentDependencyNode(
                        "a",
                        "intent-prepared",
                        ("missing",),
                    ),
                )
            )


if __name__ == "__main__":
    unittest.main()
