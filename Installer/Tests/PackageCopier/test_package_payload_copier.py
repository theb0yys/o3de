# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
for root in (
    REPO_ROOT / "Installer/Bootstrapper/PackageCopier/Source",
    REPO_ROOT / "Installer/Tests/Security",
):
    sys.path.insert(0, str(root))

from package_payload_copier import PackageCopyError, build_copy_grant, stage_payload, validate_copy_receipt  # noqa: E402
from security_test_support import InstallerSecurityFixture  # noqa: E402


class PackagePayloadCopierTests(unittest.TestCase):
    def test_stages_authenticated_inventory_with_no_replace_and_one_shot(self) -> None:
        with InstallerSecurityFixture() as fixture:
            grant = build_copy_grant(
                fixture.session, authority_key_path=fixture.authority_key,
                issuer="FOA-SDK copy broker", issued_at_utc="2026-07-22T12:04:00Z",
                expires_at_utc="2026-07-22T12:10:00Z", nonce="grant.foa-sdk.copy-0001",
            )
            target = fixture.root / "staging"
            receipt = stage_payload(
                grant, REPO_ROOT, target, authority_key_path=fixture.authority_key,
                claim_root=fixture.claim_root, copied_at_utc="2026-07-22T12:05:00Z",
            )
            self.assertTrue(target.is_dir())
            self.assertEqual(validate_copy_receipt(receipt, authority_key_path=fixture.authority_key), receipt)
            self.assertTrue(receipt["copy_performed"])
            self.assertIn("claim_sha256", receipt)
            with self.assertRaisesRegex(PackageCopyError, "already been consumed"):
                stage_payload(
                    grant, REPO_ROOT, fixture.root / "staging-replay", authority_key_path=fixture.authority_key,
                    claim_root=fixture.claim_root, copied_at_utc="2026-07-22T12:06:00Z",
                )

    def test_existing_destination_is_preserved(self) -> None:
        with InstallerSecurityFixture() as fixture:
            grant = build_copy_grant(
                fixture.session, authority_key_path=fixture.authority_key,
                issuer="FOA-SDK copy broker", issued_at_utc="2026-07-22T12:04:00Z",
                expires_at_utc="2026-07-22T12:10:00Z", nonce="grant.foa-sdk.copy-existing",
            )
            target = fixture.root / "existing"; target.mkdir(); marker = target / "keep"; marker.write_text("keep")
            with self.assertRaisesRegex(PackageCopyError, "must not already exist"):
                stage_payload(
                    grant, REPO_ROOT, target, authority_key_path=fixture.authority_key,
                    claim_root=fixture.claim_root, copied_at_utc="2026-07-22T12:05:00Z",
                )
            self.assertEqual(marker.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
