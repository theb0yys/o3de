# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
for root in (
    REPO_ROOT / "Installer/Bootstrapper/LifecycleCoordinator/Source",
    REPO_ROOT / "Installer/Bootstrapper/PackageCopier/Source",
    REPO_ROOT / "Installer/Bootstrapper/ProcessLauncher/Source",
    REPO_ROOT / "Installer/Tests/Security",
):
    sys.path.insert(0, str(root))

from capability_process_launcher import build_launch_grant, launch_process  # noqa: E402
from lifecycle_execution_coordinator import LifecycleCoordinatorError, build_lifecycle_grant, coordinate_lifecycle  # noqa: E402
from package_payload_copier import build_copy_grant, stage_payload  # noqa: E402
from security_test_support import InstallerSecurityFixture  # noqa: E402


class LifecycleExecutionCoordinatorTests(unittest.TestCase):
    def test_install_completes_from_authenticated_copy_and_bounded_launch_evidence(self) -> None:
        with InstallerSecurityFixture() as fixture:
            copy_grant = build_copy_grant(
                fixture.session, authority_key_path=fixture.authority_key,
                issuer="copy", issued_at_utc="2026-07-22T12:04:00Z", expires_at_utc="2026-07-22T12:10:00Z",
                nonce="grant.foa-sdk.copy-lifecycle",
            )
            copy_receipt = stage_payload(
                copy_grant, REPO_ROOT, fixture.root / "staging", authority_key_path=fixture.authority_key,
                claim_root=fixture.claim_root, copied_at_utc="2026-07-22T12:05:00Z",
            )
            launch_grant = build_launch_grant(
                fixture.session, authority_key_path=fixture.authority_key,
                helper_reference="helper.foa-sdk.install", issuer="launch",
                issued_at_utc="2026-07-22T12:04:00Z", expires_at_utc="2026-07-22T12:10:00Z",
                nonce="grant.foa-sdk.launch-lifecycle",
            )
            launch_result = launch_process(
                launch_grant, fixture.execution_root, authority_key_path=fixture.authority_key,
                claim_root=fixture.claim_root, launched_at_utc="2026-07-22T12:05:00Z",
            )
            lifecycle = build_lifecycle_grant(
                fixture.session, authority_key_path=fixture.authority_key, operation="install", issuer="lifecycle",
                issued_at_utc="2026-07-22T12:04:00Z", expires_at_utc="2026-07-22T12:12:00Z",
                nonce="grant.foa-sdk.lifecycle-0001",
            )
            result = coordinate_lifecycle(
                lifecycle, authority_key_path=fixture.authority_key, completed_at_utc="2026-07-22T12:06:00Z",
                copy_receipt=copy_receipt, launch_result=launch_result,
            )
            self.assertTrue(result["completed"])
            self.assertEqual(result["status"], "completed")

    def test_missing_copy_evidence_fails_closed(self) -> None:
        with InstallerSecurityFixture() as fixture:
            lifecycle = build_lifecycle_grant(
                fixture.session, authority_key_path=fixture.authority_key, operation="install", issuer="lifecycle",
                issued_at_utc="2026-07-22T12:04:00Z", expires_at_utc="2026-07-22T12:12:00Z",
                nonce="grant.foa-sdk.lifecycle-missing-copy",
            )
            with self.assertRaisesRegex(LifecycleCoordinatorError, "copy receipt"):
                coordinate_lifecycle(
                    lifecycle, authority_key_path=fixture.authority_key,
                    completed_at_utc="2026-07-22T12:06:00Z",
                )


if __name__ == "__main__":
    unittest.main()
