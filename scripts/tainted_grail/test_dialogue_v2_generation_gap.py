import unittest
from pathlib import Path

from semantic_repair.dialogue_v2 import (
    DEFAULT_MAX_GENERATION_GAP,
    DialogueRegistryV2,
    RegistrySnapshot,
)
from semantic_repair.errors import RepairError, StaleGenerationError

FIXTURES = Path(__file__).parent / "fixtures" / "api_v2"


class DialogueGenerationGapTests(unittest.TestCase):
    def base_registry(self):
        registry = DialogueRegistryV2()
        registry.apply_snapshot_bytes(
            (FIXTURES / "registry-snapshot-generation-2.json").read_bytes()
        )
        self.assertEqual(registry.generation, 2)
        return registry

    def test_serialized_gap_within_limit_applies(self):
        registry = self.base_registry()
        self.assertTrue(
            registry.apply_snapshot_bytes(
                (FIXTURES / "registry-snapshot-gap-accepted-4.json").read_bytes(),
                max_generation_gap=2,
            )
        )
        self.assertEqual(registry.generation, 4)

    def test_serialized_gap_above_limit_fails_closed(self):
        registry = self.base_registry()
        with self.assertRaises(StaleGenerationError):
            registry.apply_snapshot_bytes(
                (FIXTURES / "registry-snapshot-gap-rejected-67.json").read_bytes(),
                max_generation_gap=DEFAULT_MAX_GENERATION_GAP,
            )
        self.assertEqual(registry.generation, 2)

    def test_gap_limit_must_be_positive(self):
        with self.assertRaises(RepairError):
            DialogueRegistryV2().apply_snapshot(
                RegistrySnapshot(1, ()),
                max_generation_gap=0,
            )


if __name__ == "__main__":
    unittest.main()
