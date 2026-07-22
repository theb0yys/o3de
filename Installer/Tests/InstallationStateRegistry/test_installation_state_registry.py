# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
for root in (
    REPO_ROOT / "Installer/Bootstrapper/InstallationStateRegistry/Source",
    REPO_ROOT / "Installer/Bootstrapper/InstallationStatePublisher/Source",
    REPO_ROOT / "Installer/SuiteWizard/ViewModel/Source",
):
    sys.path.insert(0, str(root))

PUBLISHER_TESTS = REPO_ROOT / "Installer/Tests/InstallationStatePublisher/test_installation_state_publisher.py"
PUBLISHER_SPEC = importlib.util.spec_from_file_location("foa_installation_state_publisher_helpers", PUBLISHER_TESTS)
if PUBLISHER_SPEC is None or PUBLISHER_SPEC.loader is None:
    raise RuntimeError(f"Unable to load publisher helper tests: {PUBLISHER_TESTS}")
PUBLISHER_MODULE = importlib.util.module_from_spec(PUBLISHER_SPEC)
sys.modules[PUBLISHER_SPEC.name] = PUBLISHER_MODULE
PUBLISHER_SPEC.loader.exec_module(PUBLISHER_MODULE)

from installation_state_publisher import publish_state_record  # noqa: E402
from installation_state_registry import (  # noqa: E402
    OPERATIONS,
    InstallationStateRegistryError,
    build_lifecycle_eligibility,
    query_state_registry,
    validate_lifecycle_eligibility,
    validate_registry_snapshot,
)


class InstallationStateRegistryTests(unittest.TestCase):
    def helper(self):
        return PUBLISHER_MODULE.InstallationStatePublisherTests(
            methodName="test_publication_grant_is_deterministic_and_bound_to_completed_lifecycle"
        )

    def publish_state(
        self,
        root: Path,
        operation: str = "install",
        *,
        expected_previous_state_sha256: str | None = None,
        published_at_utc: str = "2026-07-22T12:16:00Z",
        nonce: str | None = None,
    ) -> dict[str, object]:
        helper = self.helper()
        session = helper.session(operation)
        lifecycle = helper.lifecycle_result(session)
        grant = helper.publication_grant(
            session,
            lifecycle,
            expected_previous_state_sha256=expected_previous_state_sha256,
            nonce=nonce or f"grant.foa-sdk.registry-publication-{operation}",
        )
        return publish_state_record(grant, root, published_at_utc=published_at_utc)

    def snapshot(self, root: Path) -> dict[str, object]:
        return query_state_registry(
            root,
            state_root_reference="state-root.foa-sdk.registry",
            observed_at_utc="2026-07-22T13:00:00Z",
        )

    def eligibility(self, snapshot: dict[str, object], operation: str) -> dict[str, object]:
        result = build_lifecycle_eligibility(
            snapshot,
            operation=operation,
            target_reference="installation.foa-sdk.default",
            decided_at_utc="2026-07-22T13:01:00Z",
        )
        self.assertEqual(validate_lifecycle_eligibility(result), result)
        return result

    def test_empty_registry_allows_install_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = self.snapshot(Path(temporary).resolve())
        self.assertEqual(validate_registry_snapshot(snapshot), snapshot)
        self.assertEqual(snapshot["record_count"], 0)
        self.assertEqual(set(OPERATIONS), {"install", "repair", "upgrade", "rollback", "uninstall"})
        self.assertTrue(self.eligibility(snapshot, "install")["eligible"])
        for operation in ("repair", "upgrade", "rollback", "uninstall"):
            decision = self.eligibility(snapshot, operation)
            self.assertFalse(decision["eligible"])
            self.assertEqual(decision["reason"], "blocked-no-current-installation-state")

    def test_active_state_unlocks_maintenance_and_blocks_duplicate_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self.publish_state(root, "install")
            snapshot = self.snapshot(root)
        self.assertEqual(snapshot["record_count"], 1)
        self.assertEqual(snapshot["active_count"], 1)
        self.assertFalse(self.eligibility(snapshot, "install")["eligible"])
        for operation in ("repair", "upgrade", "uninstall"):
            decision = self.eligibility(snapshot, operation)
            self.assertTrue(decision["eligible"])
            self.assertEqual(decision["recommended_prior_installation_reference"], "installation.foa-sdk.default")
        rollback = self.eligibility(snapshot, "rollback")
        self.assertFalse(rollback["eligible"])
        self.assertEqual(rollback["reason"], "blocked-no-rollback-base")

    def test_removed_state_allows_reinstall_and_blocks_maintenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            first = self.publish_state(root, "install")
            self.publish_state(
                root,
                "uninstall",
                expected_previous_state_sha256=str(first["state_file_sha256"]),
                published_at_utc="2026-07-22T12:17:00Z",
                nonce="grant.foa-sdk.registry-publication-uninstall",
            )
            snapshot = self.snapshot(root)
        self.assertEqual(snapshot["removed_count"], 1)
        self.assertTrue(self.eligibility(snapshot, "install")["eligible"])
        for operation in ("repair", "upgrade", "rollback", "uninstall"):
            decision = self.eligibility(snapshot, operation)
            self.assertFalse(decision["eligible"])
            self.assertEqual(decision["reason"], "blocked-current-state-removed")

    def test_noncanonical_or_tampered_state_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self.publish_state(root, "install")
            state_file = root / "installation.foa-sdk.default.json"
            state_file.write_text(
                json.dumps(json.loads(state_file.read_text(encoding="utf-8")), indent=2),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(InstallationStateRegistryError, "not canonical JSON"):
                self.snapshot(root)
            state_file.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(InstallationStateRegistryError, "failed validation"):
                self.snapshot(root)

    def test_source_does_not_reintroduce_mutating_or_runtime_surfaces(self) -> None:
        source = (
            REPO_ROOT / "Installer/Bootstrapper/InstallationStateRegistry/Source/installation_state_registry.py"
        ).read_text(encoding="utf-8")
        for forbidden in (
            "subprocess", "ShellExecute", "ctypes", "launch_process(", "request_elevation(",
            "stage_payload(", "os.", "os.replace", "write_text", "write_bytes", "unlink(",
            "mkdir(", "socket", "requests", "password", "credential",
        ):
            self.assertNotIn(forbidden, source)
        for required in (
            "package-engine.query-installation-state", "read_bytes", "validate_state_record",
            "build_lifecycle_eligibility", "lifecycle_handoff_created", "state_published",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
