import hashlib
import json
import unittest
from dataclasses import replace
from pathlib import Path

from semantic_repair.errors import RepairError
from semantic_repair.replay_sequence import ReplaySequenceEntry, ReplayWindowSequenceProof
from semantic_repair.replay_sequence_compaction import (
    ReplaySequenceCompactionProof,
    build_replay_sequence_compaction_proof,
    verify_replay_sequence_compaction_proof,
)

FIXTURES = Path(__file__).parent / "fixtures" / "api_v2"
ZERO = "0" * 64


def hx(value):
    return hashlib.sha256(value.encode()).hexdigest()


def entry(index, previous, receipt, current, incoming, status, resulting):
    core = {
        "schema_version": 1,
        "index": index,
        "previous_entry_sha256": previous,
        "receipt_sha256": receipt,
        "current_generation": current,
        "incoming_generation": incoming,
        "status": status,
        "resulting_generation": resulting,
    }
    digest = hashlib.sha256(
        (json.dumps(core, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()
    return ReplaySequenceEntry(index, previous, receipt, current, incoming, status, resulting, digest)


def first_sequence():
    previous = ZERO
    values = []
    specs = (
        (2, 4, "accepted", 4),
        (4, 4, "already-current", 4),
        (4, 3, "replayed-stale", 4),
        (4, 70, "replay-window-exceeded", 4),
    )
    for index, (current, incoming, status, resulting) in enumerate(specs, start=1):
        item = entry(index, previous, hx(f"receipt-{index}"), current, incoming, status, resulting)
        values.append(item)
        previous = item.entry_sha256
    return ReplayWindowSequenceProof(2, 4, tuple(values))


def second_sequence():
    previous = ZERO
    values = []
    specs = ((4, 5, "accepted", 5), (5, 5, "same-generation-conflict", 5))
    for index, (current, incoming, status, resulting) in enumerate(specs, start=1):
        item = entry(index, previous, hx(f"receipt2-{index}"), current, incoming, status, resulting)
        values.append(item)
        previous = item.entry_sha256
    return ReplayWindowSequenceProof(4, 5, tuple(values))


class ReplaySequenceCompactionTests(unittest.TestCase):
    def test_compaction_chain_matches_goldens(self):
        first = build_replay_sequence_compaction_proof(first_sequence())
        second = build_replay_sequence_compaction_proof(second_sequence(), previous_compaction=first)
        self.assertEqual(first.to_bytes(), (FIXTURES / "replay-sequence-compaction-proof-001.json").read_bytes())
        self.assertEqual(second.to_bytes(), (FIXTURES / "replay-sequence-compaction-proof-002.json").read_bytes())
        self.assertEqual(second.previous_compaction_sha256, first.sha256)
        self.assertEqual(ReplaySequenceCompactionProof.from_bytes(second.to_bytes()), second)
        self.assertTrue(
            verify_replay_sequence_compaction_proof(
                second_sequence(), second, previous_compaction=first
            )
        )

    def test_tampered_sequence_entry_fails_closed(self):
        source = first_sequence()
        broken = replace(source.entries[0], entry_sha256="0" * 64)
        with self.assertRaises(RepairError):
            build_replay_sequence_compaction_proof(
                ReplayWindowSequenceProof(2, 4, (broken,) + source.entries[1:])
            )


if __name__ == "__main__":
    unittest.main()
