import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from semantic_repair import (
    DiagnosticLimits,
    DiagnosticSession,
    LockOwnershipError,
    StaleGenerationError,
)

FIXTURE = Path(__file__).parent / "fixtures" / "concurrency" / "two-writer-publication.json"


class TwoWriterPublicationTests(unittest.TestCase):
    def test_fixture_schedule_and_generation_checked_publication(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(fixture["runtime_authority"], "none")
        self.assertEqual(fixture["promotion"], "none")
        with tempfile.TemporaryDirectory() as tmp:
            a = DiagnosticSession(Path(tmp), "shared")
            b = DiagnosticSession(Path(tmp), "shared")
            lease_a = a.acquire_writer("writer-a", expected_lock_generation=1)
            with self.assertRaises(LockOwnershipError):
                b.acquire_writer("writer-b", expected_lock_generation=2)
            receipt_a = a.publish_owned(
                lease_a,
                "rows.csv",
                b"writer-a\n",
                {"count": 1},
                expected_generation=0,
            )
            self.assertEqual(receipt_a.publication_generation, 1)
            a.publication_lock.release(lease_a)

            lease_b = b.acquire_writer("writer-b", expected_lock_generation=2)
            with self.assertRaises(StaleGenerationError):
                b.publish_owned(
                    lease_b,
                    "rows.csv",
                    b"stale\n",
                    {"count": 2},
                    expected_generation=0,
                )
            receipt_b = b.publish_owned(
                lease_b,
                "rows.csv",
                b"writer-b\n",
                {"count": 2},
                expected_generation=1,
            )
            b.publication_lock.release(lease_b)

            state = b.publication_state()
            self.assertEqual(state.generation, 2)
            self.assertEqual(state.last_owner_id, "writer-b")
            self.assertEqual(
                state.published_bytes,
                len(b"writer-a\n") + len(b"writer-b\n"),
            )
            self.assertEqual((b.session_dir / "rows.csv").read_bytes(), b"writer-b\n")
            self.assertEqual(receipt_b.lock_generation, 2)

    def test_state_write_failure_restores_all_three_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = DiagnosticSession(
                Path(tmp),
                "shared",
                DiagnosticLimits(field_bytes=64, row_bytes=256, session_bytes=1024),
            )
            lease_a = session.acquire_writer("writer-a", expected_lock_generation=1)
            session.publish_owned(
                lease_a,
                "rows.csv",
                b"before\n",
                {"count": 1},
                expected_generation=0,
            )
            session.publication_lock.release(lease_a)
            before = {
                path: path.read_bytes()
                for path in (
                    session.session_dir / "rows.csv",
                    session.session_dir / "diagnostic-summary.json",
                    session.publication_state_path,
                )
            }

            lease_b = session.acquire_writer("writer-b", expected_lock_generation=2)
            import semantic_repair.diagnostics as diagnostics

            original = diagnostics._atomic_write
            failed = False

            def fail_once(path, data):
                nonlocal failed
                if path == session.publication_state_path and not failed:
                    failed = True
                    raise OSError("injected publication-state failure")
                return original(path, data)

            with mock.patch(
                "semantic_repair.diagnostics._atomic_write",
                side_effect=fail_once,
            ):
                with self.assertRaises(OSError):
                    session.publish_owned(
                        lease_b,
                        "rows.csv",
                        b"after\n",
                        {"count": 2},
                        expected_generation=1,
                    )
            for path, data in before.items():
                self.assertEqual(path.read_bytes(), data)
            session.publication_lock.release(lease_b)


if __name__ == "__main__":
    unittest.main()
