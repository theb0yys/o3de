#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#

from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import developer_preview_installer as installer


class InstallerReviewMetadataTests(unittest.TestCase):
    def test_review_time_requires_exact_valid_utc_seconds(self) -> None:
        self.assertEqual(
            installer.require_utc_seconds("2026-07-23T03:30:00Z"),
            "2026-07-23T03:30:00Z",
        )
        for invalid in (
            "2026-07-23T03:30Z",
            "2026-07-23T03:30:00.000Z",
            "2026-07-23T04:30:00+01:00",
            "2026-02-30T03:30:00Z",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(installer.InstallerError):
                    installer.require_utc_seconds(invalid)

    def test_reviewer_and_evidence_must_be_named_printable_text(self) -> None:
        self.assertEqual(installer.require_plain_text("Named Reviewer", "Reviewer"), "Named Reviewer")
        self.assertEqual(
            installer.require_plain_text("review-record:123", "Evidence"),
            "review-record:123",
        )
        for invalid in ("", "   ", "reviewer\nforged"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(installer.InstallerError):
                    installer.require_plain_text(invalid, "Review field")

    def test_inventory_fingerprint_must_be_a_complete_sha256(self) -> None:
        fingerprint = "a" * 64
        self.assertEqual(installer.require_sha256(fingerprint, "Inventory fingerprint"), fingerprint)
        for invalid in ("a" * 63, "g" * 64, "sha256:" + fingerprint):
            with self.subTest(invalid=invalid):
                with self.assertRaises(installer.InstallerError):
                    installer.require_sha256(invalid, "Inventory fingerprint")


if __name__ == "__main__":
    unittest.main()
