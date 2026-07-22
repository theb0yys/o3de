# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
for root in (
    REPO_ROOT / "Installer/Bootstrapper/LifecycleOperationAdmission/Source",
    REPO_ROOT / "Installer/Bootstrapper/InstallationStateRegistry/Source",
    REPO_ROOT / "Installer/SuiteWizard/ViewModel/Source",
):
    sys.path.insert(0, str(root))

REGISTRY_TESTS = REPO_ROOT / "Installer/Tests/InstallationStateRegistry/test_installation_state_registry.py"
REGISTRY_SPEC = importlib.util.spec_from_file_location("foa_installation_state_registry_helpers", REGISTRY_TESTS)
if REGISTRY_SPEC is None or REGISTRY_SPEC.loader is None:
    raise RuntimeError(f"Unable to load registry helper tests: {REGISTRY_TESTS}")
REGISTRY_MODULE = importlib.util.module_from_spec(REGISTRY_SPEC)
sys.modules[REGISTRY_SPEC.name] = REGISTRY_MODULE
REGISTRY_SPEC.loader.exec_module(REGISTRY_MODULE)

from lifecycle_operation_admission import (  # noqa: E402
    ADMISSION_CAPABILITY,
    LifecycleOperationAdmissionError,
    admit_lifecycle_operation,
    build_admission_grant,
    validate_admission_grant,
    validate_admission_receipt,
)


class LifecycleOperationAdmissionTests(unittest.TestCase):
    def helper(self):
        return REGISTRY_MODULE.InstallationStateRegistryTests(methodName="test_empty_registry_allows_install_only")

    def admission_grant(self, eligibility: dict[str, object], *, nonce: str = "grant.foa-sdk.admission") -> dict[str, object]:
        return build_admission_grant(
            eligibility,
            issuer="FOA-SDK lifecycle admission reviewer",
            issued_at_utc="2026-07-22T13:02:00Z",
            expires_at_utc="2026-07-22T13:12:00Z",
            nonce=nonce,
        )

    def test_empty_registry_install_admission_is_deterministic_and_side_effect_free(self) -> None:
        helper = self.helper()
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = helper.snapshot(Path(temporary).resolve())
        eligibility = helper.eligibility(snapshot, "install")
        first = self.admission_grant(eligibility)
        second = self.admission_grant(eligibility)
        self.assertEqual(first, second)
        self.assertEqual(first["capability"], ADMISSION_CAPABILITY)
        self.assertEqual(first["operation"], "install")
        self.assertEqual(first["eligibility_sha256"], eligibility["eligibility_sha256"])
        self.assertTrue(all(value is False for value in first["authority"].values()))
        self.assertEqual(validate_admission_grant(first), first)
        receipt = admit_lifecycle_operation(first, admitted_at_utc="2026-07-22T13:03:00Z")
        self.assertEqual(validate_admission_receipt(receipt), receipt)
        self.assertTrue(receipt["admitted"])
        for field in (
            "lifecycle_handoff_created", "package_engine_session_created", "copy_performed",
            "process_launched", "elevation_requested", "state_published", "product_or_game_directory_mutated",
            "runtime_executed", "save_mutated", "signing_performed", "network_publication_performed",
            "catalog_mutated", "evidence_promoted",
        ):
            self.assertFalse(receipt[field])

    def test_active_state_admits_maintenance_operations(self) -> None:
        helper = self.helper()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            helper.publish_state(root, "install")
            snapshot = helper.snapshot(root)
        for operation in ("repair", "upgrade", "uninstall"):
            eligibility = helper.eligibility(snapshot, operation)
            grant = self.admission_grant(eligibility, nonce=f"grant.foa-sdk.admission-{operation}")
            receipt = admit_lifecycle_operation(grant, admitted_at_utc="2026-07-22T13:03:00Z")
            self.assertEqual(receipt["operation"], operation)
            self.assertEqual(receipt["current_state_reference"], "installation.foa-sdk.default")
            self.assertEqual(receipt["recommended_prior_installation_reference"], "installation.foa-sdk.default")
            self.assertTrue(receipt["admitted"])

    def test_blocked_eligibility_never_becomes_admission(self) -> None:
        helper = self.helper()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            helper.publish_state(root, "install")
            snapshot = helper.snapshot(root)
        blocked = helper.eligibility(snapshot, "install")
        self.assertFalse(blocked["eligible"])
        with self.assertRaisesRegex(LifecycleOperationAdmissionError, "Only eligible"):
            self.admission_grant(blocked)

    def test_tampered_eligibility_and_grant_fail_closed(self) -> None:
        helper = self.helper()
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = helper.snapshot(Path(temporary).resolve())
        eligibility = helper.eligibility(snapshot, "install")
        tampered_eligibility = copy.deepcopy(eligibility)
        tampered_eligibility["target_reference"] = "installation.foa-sdk.other"
        with self.assertRaises(LifecycleOperationAdmissionError):
            self.admission_grant(tampered_eligibility)
        grant = self.admission_grant(eligibility)
        tampered_grant = copy.deepcopy(grant)
        tampered_grant["operation"] = "repair"
        with self.assertRaises(LifecycleOperationAdmissionError):
            validate_admission_grant(tampered_grant)

    def test_temporal_bounds_fail_closed(self) -> None:
        helper = self.helper()
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = helper.snapshot(Path(temporary).resolve())
        eligibility = helper.eligibility(snapshot, "install")
        with self.assertRaisesRegex(LifecycleOperationAdmissionError, "must not precede"):
            build_admission_grant(
                eligibility,
                issuer="FOA-SDK lifecycle admission reviewer",
                issued_at_utc="2026-07-22T13:00:00Z",
                expires_at_utc="2026-07-22T13:05:00Z",
                nonce="grant.foa-sdk.admission-too-early",
            )
        grant = build_admission_grant(
            eligibility,
            issuer="FOA-SDK lifecycle admission reviewer",
            issued_at_utc="2026-07-22T13:02:00Z",
            expires_at_utc="2026-07-22T13:03:00Z",
            nonce="grant.foa-sdk.admission-expiry",
        )
        with self.assertRaisesRegex(LifecycleOperationAdmissionError, "expired"):
            admit_lifecycle_operation(grant, admitted_at_utc="2026-07-22T13:04:00Z")

    def test_source_does_not_reintroduce_mutating_or_runtime_surfaces(self) -> None:
        source = (
            REPO_ROOT / "Installer/Bootstrapper/LifecycleOperationAdmission/Source/lifecycle_operation_admission.py"
        ).read_text(encoding="utf-8")
        for forbidden in (
            "subprocess", "ShellExecute", "ctypes", "launch_process(", "request_elevation(",
            "stage_payload(", "publish_state_record(", "query_state_registry(", "os.", "read_bytes",
            "write_text", "write_bytes", "unlink(", "mkdir(", "socket", "requests", "password", "credential",
        ):
            self.assertNotIn(forbidden, source)
        for required in (
            "package-engine.admit-lifecycle-operation", "validate_lifecycle_eligibility",
            "Only eligible lifecycle operations", "lifecycle_handoff_created", "package_engine_session_created",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
