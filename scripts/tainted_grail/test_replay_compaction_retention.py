import hashlib
import json
import unittest
from dataclasses import replace
from pathlib import Path
from semantic_repair.errors import RepairError
from semantic_repair.replay_compaction_retention import (
    ReplayCompactionRetentionPlan,
    ReplayCompactionRetentionPolicy,
    build_replay_compaction_retention_plan,
    verify_replay_compaction_retention_plan,
)
from semantic_repair.replay_sequence_compaction import (
    ReplaySequenceCompactionProof,
)

FIXTURE = Path(__file__).parent / "fixtures" / "api_v2" / "replay-compaction-retention-plan.json"

def make_proof(seqchar, initial, final, previous, statuses):
    status_counts = tuple(sorted(statuses))
    summary = {
        "source_sequence_sha256": seqchar * 64,
        "source_entry_count": sum(count for _, count in status_counts),
        "initial_generation": initial,
        "final_generation": final,
        "first_entry_sha256": chr(ord(seqchar) + 1) * 64,
        "final_entry_sha256": chr(ord(seqchar) + 2) * 64,
        "status_counts": [
            {"status": status, "count": count}
            for status, count in status_counts
        ],
        "previous_compaction_sha256": previous,
    }
    summary_sha = hashlib.sha256(
        (json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()
    return ReplaySequenceCompactionProof(
        summary["source_sequence_sha256"],
        summary["source_entry_count"],
        initial, final,
        summary["first_entry_sha256"],
        summary["final_entry_sha256"],
        status_counts, previous, summary_sha,
    )

class ReplayCompactionRetentionTests(unittest.TestCase):
    def _proofs(self):
        first = make_proof(
            "6", 1, 2, "0"*64,
            (("accepted", 1), ("already-current", 1)),
        )
        second = make_proof(
            "7", 2, 2, first.sha256,
            (("replayed-stale", 2),),
        )
        third = make_proof(
            "8", 2, 4, second.sha256,
            (("accepted", 1), ("replay-window-exceeded", 1)),
        )
        return first, second, third

    def test_retention_golden_and_round_trip(self):
        proofs = self._proofs()
        plan = build_replay_compaction_retention_plan(
            proofs, policy=ReplayCompactionRetentionPolicy(2)
        )
        self.assertEqual(plan.to_bytes(), FIXTURE.read_bytes())
        self.assertEqual(
            ReplayCompactionRetentionPlan.from_bytes(plan.to_bytes()),
            plan,
        )
        self.assertTrue(
            verify_replay_compaction_retention_plan(proofs, plan)
        )

    def test_broken_chain_fails(self):
        first, second, third = self._proofs()
        broken = replace(third, previous_compaction_sha256="0"*64)
        with self.assertRaises(RepairError):
            build_replay_compaction_retention_plan(
                (first, second, broken),
                policy=ReplayCompactionRetentionPolicy(2),
            )

if __name__ == "__main__":
    unittest.main()
