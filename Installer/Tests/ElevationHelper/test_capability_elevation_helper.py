# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
for root in (
    REPO_ROOT / "Installer/Bootstrapper/ElevationHelper/Source",
    REPO_ROOT / "Installer/Bootstrapper/ProcessLauncher/Source",
    REPO_ROOT / "Installer/Tests/Security",
):
    sys.path.insert(0, str(root))

from capability_elevation_helper import (  # noqa: E402
    ElevationError,
    build_consent,
    build_elevation_grant,
    request_elevation,
    validate_consent,
    validate_elevation_result,
)
from capability_process_launcher import build_launch_grant  # noqa: E402
from controlled_elevation_bootstrapper import execute_bootstrap_request  # noqa: E402
from security_test_support import InstallerSecurityFixture  # noqa: E402


class CapabilityElevationHelperTests(unittest.TestCase):
    def _grant(self, fixture: InstallerSecurityFixture) -> dict[str, object]:
        launch = build_launch_grant(
            fixture.session, authority_key_path=fixture.authority_key,
            helper_reference="helper.foa-sdk.install", issuer="FOA-SDK launch broker",
            issued_at_utc="2026-07-22T12:04:00Z", expires_at_utc="2026-07-22T12:10:00Z",
            nonce="grant.foa-sdk.launch-elevated",
        )
        consent = build_consent(
            authority_key_path=fixture.authority_key,
            consent_reference="consent.foa-sdk.elevation-0001", approved_by="FOA-SDK trusted UI",
            approved_at_utc="2026-07-22T12:05:00Z", helper_reference="helper.foa-sdk.install",
            launch_grant_sha256=str(launch["grant_sha256"]), rationale="Protected installation target.",
        )
        self.assertEqual(validate_consent(consent, authority_key_path=fixture.authority_key), consent)
        return build_elevation_grant(
            fixture.session, launch, consent, authority_key_path=fixture.authority_key,
            issuer="FOA-SDK elevation broker", issued_at_utc="2026-07-22T12:06:00Z",
            expires_at_utc="2026-07-22T12:09:00Z", nonce="grant.foa-sdk.elevation-0001",
        )

    def test_consent_is_authenticated_and_wrong_key_fails(self) -> None:
        with InstallerSecurityFixture(elevated=True) as fixture:
            grant = self._grant(fixture)
            consent = grant["consent"]
            wrong = fixture.root / "wrong.key"; wrong.write_bytes(bytes.fromhex("24" * 32)); os.chmod(wrong, 0o600)
            with self.assertRaises(ElevationError):
                validate_consent(consent, authority_key_path=wrong)

    def test_request_launches_only_reviewed_bootstrapper_and_is_one_shot(self) -> None:
        with InstallerSecurityFixture(elevated=True) as fixture:
            grant = self._grant(fixture)
            calls: list[tuple[Path, list[str], Path]] = []
            def backend(executable: Path, parameters: list[str], cwd: Path) -> int:
                calls.append((executable, parameters, cwd)); return 42
            result = request_elevation(
                grant, fixture.execution_root, fixture.request_root,
                authority_key_path=fixture.authority_key, claim_root=fixture.claim_root,
                request_reference="request.foa-sdk.elevation-0001", requested_at_utc="2026-07-22T12:07:00Z",
                backend=backend,
            )
            self.assertEqual(calls[0][0], fixture.bootstrapper_path)
            self.assertEqual(calls[0][1][-2], "--request")
            self.assertTrue(Path(calls[0][1][-1]).name.endswith(".json"))
            self.assertIn("--authority-key", calls[0][1])
            self.assertTrue(result["controlled_bootstrapper_only"])
            self.assertEqual(validate_elevation_result(result, authority_key_path=fixture.authority_key), result)
            with self.assertRaisesRegex(ElevationError, "already been consumed"):
                request_elevation(
                    grant, fixture.execution_root, fixture.request_root,
                    authority_key_path=fixture.authority_key, claim_root=fixture.claim_root,
                    request_reference="request.foa-sdk.elevation-replay", requested_at_utc="2026-07-22T12:08:00Z",
                    backend=backend,
                )

    def test_controlled_bootstrapper_reverifies_request_and_applies_exact_environment(self) -> None:
        with InstallerSecurityFixture(elevated=True) as fixture:
            grant = self._grant(fixture)
            captured: dict[str, object] = {}
            def backend(executable: Path, parameters: list[str], cwd: Path) -> int:
                from controlled_elevation_bootstrapper import load_request
                request_path = Path(parameters[-1])
                captured["request"] = load_request(request_path, authority_key_path=fixture.authority_key)
                return 42
            request_elevation(
                grant, fixture.execution_root, fixture.request_root,
                authority_key_path=fixture.authority_key, claim_root=fixture.claim_root,
                request_reference="request.foa-sdk.elevation-bootstrap", requested_at_utc="2026-07-22T12:07:00Z",
                backend=backend,
            )
            completion_claims = fixture.root / "completion-claims"; completion_claims.mkdir()
            completion = execute_bootstrap_request(
                captured["request"], fixture.execution_root, authority_key_path=fixture.authority_key,
                claim_root=completion_claims, completed_at_utc="2026-07-22T12:08:00Z",
            )
            self.assertTrue(completion["process_completion_observed"])
            self.assertTrue(completion["exact_environment_applied"])
            self.assertEqual(completion["return_code"], 0)


if __name__ == "__main__":
    unittest.main()
