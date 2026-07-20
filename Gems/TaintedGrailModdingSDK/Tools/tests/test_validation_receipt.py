#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = TOOLS_ROOT / "validation_receipt.py"
COMMIT = "a" * 40
OTHER_COMMIT = "b" * 40


class ValidationReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.repository_temporary.cleanup)
        self.repository = Path(self.repository_temporary.name) / "repo"
        self.repository.mkdir()
        subprocess.run(
            ["git", "-C", str(self.repository), "init"],
            check=True,
            capture_output=True,
        )
        (self.repository / "tracked.txt").write_text("fixture\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.repository), "add", "tracked.txt"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(self.repository),
                "-c",
                "user.name=Receipt Test",
                "-c",
                "user.email=receipt@example.invalid",
                "commit",
                "-m",
                "fixture",
            ],
            check=True,
            capture_output=True,
        )
        commit = subprocess.run(
            ["git", "-C", str(self.repository), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        global COMMIT
        COMMIT = commit

    def run_tool(
        self,
        *arguments: str,
        expected: int = 0,
    ) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repo-root",
                str(self.repository),
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            completed.returncode,
            expected,
            msg=f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )
        return completed

    def initialize(self, output: Path) -> None:
        self.run_tool(
            "init",
            "--output",
            str(output),
            "--tester-alias",
            "test-reviewer",
            "--platform",
            "Windows 11 x64",
            "--configuration",
            "profile",
        )

    def record_passed(
        self,
        output: Path,
        gate: str,
        minute: int,
        log: Path | None = None,
    ) -> None:
        arguments = [
            "record",
            "--output",
            str(output),
            "--name",
            gate,
            "--notes",
            f"Synthetic unit-test pass at minute {minute}.",
            "--",
            sys.executable,
            "-c",
            "print('validation passed')",
        ]
        self.run_tool(*arguments)

    def record_not_run(self, output: Path, gate: str) -> None:
        self.run_tool(
            "skip",
            "--output",
            str(output),
            "--name",
            gate,
            "--reason",
            "Unavailable in the synthetic unit-test environment.",
        )

    def accept_risk(self, output: Path, gate: str) -> None:
        self.run_tool(
            "accept-risk",
            "--output",
            str(output),
            "--gate",
            gate,
            "--maintainer-alias",
            "test-maintainer",
            "--rationale",
            "Synthetic unit-test acceptance for a deliberately not-run gate.",
        )

    def make_merge_ready(self, output: Path, log: Path | None = None) -> None:
        self.initialize(output)
        self.record_passed(output, "git-diff-check", 1, log)
        self.record_passed(output, "local-validation", 2)
        for minute, gate in enumerate(
            (
                "o3de-configure",
                "o3de-build",
                "compiled-tests",
            ),
            start=1,
        ):
            self.record_passed(output, gate, minute + 2)
        self.record_not_run(output, "windows-ui")
        self.accept_risk(output, "windows-ui")
        self.run_tool(
            "finalize",
            "--output",
            str(output),
            "--expected-commit",
            COMMIT,
        )

    def test_merge_ready_receipt_verifies_and_summarizes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "receipt"
            log = root / "local.log"
            log.write_text("validation passed\n", encoding="utf-8")
            self.make_merge_ready(output, log)

            self.run_tool(
                "verify",
                "--output",
                str(output),
                "--expected-commit",
                COMMIT,
                "--require-merge-ready",
            )
            summary = self.run_tool(
                "summarize",
                "--output",
                str(output),
                "--expected-commit",
                COMMIT,
                "--require-merge-ready",
            )
            self.assertIn("## Exact-head validation receipt", summary.stdout)
            self.assertIn("`local-validation`", summary.stdout)
            self.assertIn("Maintainer risk acceptances", summary.stdout)

    def test_tampered_log_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "receipt"
            log = root / "local.log"
            log.write_text("validation passed\n", encoding="utf-8")
            self.make_merge_ready(output, log)
            copied = output / "logs/git-diff-check.stdout.log"
            copied.write_text("tampered\n", encoding="utf-8")

            result = self.run_tool(
                "verify",
                "--output",
                str(output),
                "--expected-commit",
                COMMIT,
                "--require-merge-ready",
                expected=1,
            )
            self.assertIn("hash or byte count does not match", result.stderr)

    def test_wrong_expected_commit_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "receipt"
            self.make_merge_ready(output)
            result = self.run_tool(
                "verify",
                "--output",
                str(output),
                "--expected-commit",
                OTHER_COMMIT,
                "--require-merge-ready",
                expected=1,
            )
            self.assertIn("does not match", result.stderr)

    def test_mandatory_local_validation_cannot_be_waived(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "receipt"
            self.initialize(output)
            self.record_passed(output, "git-diff-check", 1)
            self.record_not_run(output, "local-validation")
            for gate in (
                "o3de-configure",
                "o3de-build",
                "compiled-tests",
                "windows-ui",
            ):
                self.record_not_run(output, gate)
            result = self.run_tool(
                "finalize",
                "--output",
                str(output),
                "--expected-commit",
                COMMIT,
                expected=1,
            )
            self.assertIn("local-validation must pass", result.stderr)

    def test_skipped_host_gate_requires_maintainer_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "receipt"
            self.initialize(output)
            self.record_passed(output, "git-diff-check", 1)
            self.record_passed(output, "local-validation", 2)
            self.record_passed(output, "o3de-configure", 3)
            self.record_passed(output, "o3de-build", 4)
            self.record_passed(output, "compiled-tests", 5)
            self.record_not_run(output, "windows-ui")
            result = self.run_tool(
                "finalize",
                "--output",
                str(output),
                "--expected-commit",
                COMMIT,
                expected=1,
            )
            self.assertIn("explicit maintainer risk acceptance", result.stderr)

    def test_finalized_receipt_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "receipt"
            self.make_merge_ready(output)
            result = self.run_tool(
                "skip",
                "--output",
                str(output),
                "--name",
                "windows-ui",
                "--reason",
                "Synthetic rerun.",
                expected=1,
            )
            self.assertIn("immutable", result.stderr)

    def test_record_executes_command_and_derives_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "receipt"
            self.initialize(output)
            result = self.run_tool(
                "record",
                "--output",
                str(output),
                "--name",
                "git-diff-check",
                "--",
                sys.executable,
                "-c",
                "import sys; print('failed gate'); sys.exit(7)",
                expected=1,
            )
            self.assertIn("failed", result.stdout)
            receipt = json.loads(
                (output / "validation-receipt.json").read_text(encoding="utf-8")
            )
            gate = receipt["gates"][0]
            self.assertEqual(gate["status"], "failed")
            self.assertEqual(gate["exit_code"], 7)
            self.assertIn(sys.executable, gate["command"])
            self.assertEqual(gate["stdout_log"]["path"], "logs/git-diff-check.stdout.log")

    def test_init_rejects_dirty_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "receipt"
            (self.repository / "tracked.txt").write_text("dirty\n", encoding="utf-8")
            result = self.run_tool(
                "init",
                "--output",
                str(output),
                "--tester-alias",
                "test-reviewer",
                "--platform",
                "Windows 11 x64",
                "--configuration",
                "profile",
                expected=1,
            )
            self.assertIn("clean", result.stderr)

    def test_mandatory_compiled_gate_cannot_be_waived(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "receipt"
            self.initialize(output)
            self.record_passed(output, "git-diff-check", 1)
            self.record_passed(output, "local-validation", 2)
            self.record_passed(output, "o3de-configure", 3)
            self.record_passed(output, "o3de-build", 4)
            self.record_not_run(output, "compiled-tests")
            self.record_not_run(output, "windows-ui")
            self.accept_risk(output, "windows-ui")
            result = self.run_tool(
                "finalize",
                "--output",
                str(output),
                "--expected-commit",
                COMMIT,
                expected=1,
            )
            self.assertIn("compiled-tests must pass", result.stderr)

    @unittest.skipUnless(os.name == "nt", "Windows reparse-point behavior")
    def test_output_directory_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target"
            target.mkdir()
            output = root / "receipt-link"
            try:
                output.symlink_to(target, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            result = self.run_tool(
                "init",
                "--output",
                str(output),
                "--tester-alias",
                "test-reviewer",
                "--platform",
                "Windows 11 x64",
                "--configuration",
                "profile",
                expected=1,
            )
            self.assertIn("storage indirection", result.stderr)

    def test_receipt_json_uses_exact_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "receipt"
            self.initialize(output)
            receipt = json.loads(
                (output / "validation-receipt.json").read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["schema_version"], 1)
            self.assertEqual(receipt["source_commit"], COMMIT)
            self.assertEqual(receipt["gates"], [])
            self.assertEqual(receipt["risk_acceptances"], [])
            self.assertIsNone(receipt["finalized_at_utc"])


if __name__ == "__main__":
    unittest.main()
