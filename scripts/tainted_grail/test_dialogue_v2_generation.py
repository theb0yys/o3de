import unittest
from pathlib import Path

from semantic_repair import (
    CommandRegistration,
    DialogueRegistryV2,
    RegistrationToken,
    RegistrySnapshot,
    RepairError,
    StaleGenerationError,
)

FIXTURES = Path(__file__).parent / "fixtures" / "api_v2"


class DialogueGenerationTests(unittest.TestCase):
    def test_generation_two_snapshot_is_canonical(self):
        registry = DialogueRegistryV2()
        registry.register(CommandRegistration("foa.synthetic.a", "open", "Open"))
        registry.register(CommandRegistration("foa.synthetic.b", "close", "Close"))
        expected = (FIXTURES / "registry-snapshot-generation-2.json").read_bytes()
        self.assertEqual(registry.to_snapshot_bytes(), expected)
        self.assertEqual(RegistrySnapshot.from_bytes(expected).to_bytes(), expected)

    def test_stale_snapshot_is_rejected_after_newer_generation(self):
        current = DialogueRegistryV2()
        current.apply_snapshot_bytes(
            (FIXTURES / "registry-snapshot-generation-2.json").read_bytes()
        )
        with self.assertRaises(StaleGenerationError):
            current.apply_snapshot_bytes(
                (FIXTURES / "registry-snapshot-stale-generation-1.json").read_bytes()
            )

    def test_equal_generation_conflict_is_rejected(self):
        registry = DialogueRegistryV2()
        registry.apply_snapshot_bytes(
            (FIXTURES / "registry-snapshot-generation-2.json").read_bytes()
        )
        conflicting = RegistrySnapshot(
            2,
            (
                RegistrationToken(
                    "v2:foa.synthetic.a:different",
                    "foa.synthetic.a",
                    "different",
                    2,
                ),
            ),
        )
        with self.assertRaises(RepairError):
            registry.apply_snapshot(conflicting)

    def test_mutations_advance_generation_and_tokens_preserve_registration_generation(self):
        registry = DialogueRegistryV2()
        token = registry.register(CommandRegistration("owner", "command", "Command"))
        self.assertEqual(token.generation, 1)
        self.assertEqual(registry.generation, 1)
        registry.unregister("owner", token)
        self.assertEqual(registry.generation, 2)
        self.assertEqual(registry.to_snapshot_bytes(), RegistrySnapshot(2, ()).to_bytes())


if __name__ == "__main__":
    unittest.main()
