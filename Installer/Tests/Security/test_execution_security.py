# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import copy
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
for root in (
    REPO_ROOT / "Installer/Bootstrapper/Security/Source",
    REPO_ROOT / "Installer/Tests/Security",
):
    sys.path.insert(0, str(root))

from execution_security import (  # noqa: E402
    ExecutionSecurityError,
    claim_once,
    rename_no_replace,
    run_bounded_process,
    validate_authority_proof,
)
from security_test_support import InstallerSecurityFixture  # noqa: E402


class ExecutionSecurityTests(unittest.TestCase):
    def test_reviewed_plan_derives_copy_launch_and_lifecycle_capabilities(self) -> None:
        with InstallerSecurityFixture() as fixture:
            self.assertEqual(
                fixture.operation_plan["capabilities"],
                [
                    "package-engine.copy-payload",
                    "package-engine.execute.install",
                    "package-engine.launch-process",
                    "package-engine.publish-installation-state",
                ],
            )
            self.assertEqual(fixture.session["authorized_capabilities"], fixture.operation_plan["capabilities"])

    def test_authority_proof_rejects_tamper_and_wrong_trust_key(self) -> None:
        with InstallerSecurityFixture() as fixture:
            tampered = copy.deepcopy(fixture.authority_proof)
            tampered["capabilities"] = ["package-engine.execute.install"]
            with self.assertRaises(ExecutionSecurityError):
                validate_authority_proof(
                    tampered, fixture.handoff, fixture.operation_plan, authority_key_path=fixture.authority_key
                )
            wrong = fixture.root / "wrong.key"; wrong.write_bytes(bytes.fromhex("24" * 32)); os.chmod(wrong, 0o600)
            with self.assertRaisesRegex(ExecutionSecurityError, "trust anchor"):
                validate_authority_proof(
                    fixture.authority_proof, fixture.handoff, fixture.operation_plan, authority_key_path=wrong
                )

    def test_claim_is_authenticated_atomic_and_one_shot(self) -> None:
        with InstallerSecurityFixture() as fixture:
            first = claim_once(
                fixture.claim_root, authority_key_path=fixture.authority_key,
                claim_kind="claim.foa-sdk.test", artifact_sha256="a" * 64,
                nonce="nonce.foa-sdk.test", claimed_at_utc="2026-07-22T12:00:00Z",
            )
            self.assertEqual(first["artifact_sha256"], "a" * 64)
            self.assertIn("authority_signature", first)
            with self.assertRaisesRegex(ExecutionSecurityError, "already been consumed"):
                claim_once(
                    fixture.claim_root, authority_key_path=fixture.authority_key,
                    claim_kind="claim.foa-sdk.test", artifact_sha256="a" * 64,
                    nonce="nonce.foa-sdk.test", claimed_at_utc="2026-07-22T12:00:01Z",
                )

    def test_atomic_no_replace_refuses_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"; source.mkdir()
            destination = root / "destination"; destination.mkdir()
            marker = destination / "keep"; marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(ExecutionSecurityError):
                rename_no_replace(source, destination)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    @unittest.skipUnless(Path("/bin/sh").is_file(), "POSIX shell fixture required")
    def test_output_limit_terminates_process_before_unbounded_capture(self) -> None:
        result = run_bounded_process(
            ["/bin/sh", "-c", "while :; do printf 1234567890; done"],
            cwd=Path("/") , environment={}, timeout_seconds=5, output_limit_bytes=1024,
        )
        self.assertTrue(result["output_limit_exceeded"])
        self.assertLessEqual(len(result["stdout"]), 1024)
        self.assertGreater(result["stdout_observed_bytes"], 1024)


if __name__ == "__main__":
    unittest.main()
