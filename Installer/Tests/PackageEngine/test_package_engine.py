# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import copy
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
for root in (
    REPO_ROOT / "Installer/Bootstrapper/PackageEngine/Source",
    REPO_ROOT / "Installer/Tests/Security",
):
    sys.path.insert(0, str(root))

from package_engine import PackageEngineError, build_engine_session, validate_capability_token, validate_engine_session  # noqa: E402
from security_test_support import InstallerSecurityFixture  # noqa: E402


class PackageEngineCapabilityTests(unittest.TestCase):
    def test_session_is_authenticated_plan_bound_and_token_consumed_once(self) -> None:
        with InstallerSecurityFixture() as fixture:
            self.assertEqual(validate_capability_token(fixture.token, authority_key_path=fixture.authority_key), fixture.token)
            self.assertEqual(validate_engine_session(fixture.session, authority_key_path=fixture.authority_key), fixture.session)
            self.assertEqual(fixture.session["operation_plan_sha256"], fixture.operation_plan["operation_plan_sha256"])
            self.assertIn("package-engine.copy-payload", fixture.session["authorized_capabilities"])
            self.assertIn("package-engine.launch-process", fixture.session["authorized_capabilities"])
            with self.assertRaisesRegex(PackageEngineError, "already been consumed"):
                build_engine_session(
                    fixture.handoff, fixture.token, authority_key_path=fixture.authority_key,
                    claim_root=fixture.claim_root, session_reference="session.foa-sdk.replay",
                    accepted_by="replay", accepted_at_utc="2026-07-22T12:04:00Z",
                )

    def test_wrong_authority_key_and_rehashed_tamper_fail(self) -> None:
        with InstallerSecurityFixture() as fixture:
            wrong = fixture.root / "wrong.key"; wrong.write_bytes(bytes.fromhex("24" * 32)); os.chmod(wrong, 0o600)
            with self.assertRaises(PackageEngineError):
                validate_capability_token(fixture.token, authority_key_path=wrong)
            tampered = copy.deepcopy(fixture.token)
            tampered["granted_capabilities"].append("package-engine.elevation")
            from execution_security import sha256
            unsigned = {key: value for key, value in tampered.items() if key != "token_sha256"}
            tampered["token_sha256"] = sha256(unsigned)
            with self.assertRaises(PackageEngineError):
                validate_capability_token(tampered, authority_key_path=fixture.authority_key)


if __name__ == "__main__":
    unittest.main()
