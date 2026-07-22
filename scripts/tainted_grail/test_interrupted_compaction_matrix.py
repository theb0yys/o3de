import json
import tempfile
import unittest
from pathlib import Path

from semantic_repair.errors import SimulatedCrash
from semantic_repair.interrupted_compaction import (
    compact_terminal_journal_resilient_owned,
    recover_interrupted_compaction_owned,
)
from semantic_repair.journal import CrashRecoveryJournal

FIXTURE = Path(__file__).parent / "fixtures" / "compaction" / "interrupted-compaction-matrix.json"


class InterruptedCompactionMatrixTests(unittest.TestCase):
    def _case(self, stage, prior_proof):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journal = CrashRecoveryJournal(root / "journal.jsonl")
            lease = journal.acquire("writer")
            journal.append_owned(lease, "tx", "committed", {"value": 1})
            source = journal.path.read_bytes()
            proof = root / "checkpoint-proof.json"
            chain = root / "checkpoint-chain.jsonl"
            if prior_proof:
                proof.write_bytes(b"prior-proof\n")
            with self.assertRaises(SimulatedCrash):
                compact_terminal_journal_resilient_owned(
                    journal,
                    lease,
                    proof,
                    chain,
                    crash_after_stage=stage,
                )
            receipt = recover_interrupted_compaction_owned(journal, lease)
            expected = "finalized" if stage == "chain-published" else "rolled-back"
            self.assertEqual(receipt.status, expected)
            if expected == "rolled-back":
                self.assertEqual(journal.path.read_bytes(), source)
                self.assertEqual(proof.exists(), prior_proof)
                if prior_proof:
                    self.assertEqual(proof.read_bytes(), b"prior-proof\n")
            else:
                self.assertNotEqual(journal.path.read_bytes(), source)
                self.assertTrue(proof.exists())
                self.assertTrue(chain.exists())
            return {
                "prior_proof": prior_proof,
                "stage": stage,
                "recovery": expected,
                "journal_state": "compacted" if expected == "finalized" else "source-restored",
            }

    def test_matrix_matches_golden(self):
        cases = []
        for prior_proof in (False, True):
            for stage in ("prepared", "journal-replaced", "proof-published", "chain-published"):
                cases.append(self._case(stage, prior_proof))
        doc = {
            "schema_version": 1,
            "authority": "synthetic-interrupted-compaction-matrix-only",
            "runtime_authority": "none",
            "promotion": "none",
            "cases": cases,
        }
        encoded = (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode()
        self.assertEqual(encoded, FIXTURE.read_bytes())


if __name__ == "__main__":
    unittest.main()
