# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
for root in (
    REPO_ROOT / "Installer/Bootstrapper/LifecycleCoordinator/Source",
    REPO_ROOT / "Installer/Bootstrapper/PackageCopier/Source",
    REPO_ROOT / "Installer/Bootstrapper/ProcessLauncher/Source",
    REPO_ROOT / "Installer/Bootstrapper/PackageEngine/Source",
    REPO_ROOT / "Installer/Bootstrapper/ExecutionHandoff/Source",
    REPO_ROOT / "Installer/SuiteWizard/Receipt/Source",
    REPO_ROOT / "Installer/SuiteWizard/Host/Source",
    REPO_ROOT / "Installer/SuiteWizard/ViewModel/Source",
):
    sys.path.insert(0, str(root))

from capability_process_launcher import build_launch_grant, launch_process  # noqa: E402
from confirmation_receipt import build_receipt  # noqa: E402
from lifecycle_execution_coordinator import (  # noqa: E402
    OPERATIONS,
    LifecycleCoordinatorError,
    build_lifecycle_grant,
    coordinate_lifecycle,
    validate_lifecycle_grant,
    validate_lifecycle_result,
)
from package_engine import build_capability_token, build_engine_session  # noqa: E402
from package_payload_copier import build_copy_grant, stage_payload  # noqa: E402
from receipt_execution_handoff import build_handoff  # noqa: E402
from wizard_confirmation_controller import WizardConfirmationController  # noqa: E402


class LifecycleExecutionCoordinatorTests(unittest.TestCase):
    def accepted_receipt(self) -> dict[str, object]:
        controller = WizardConfirmationController(REPO_ROOT / "Installer")
        review = controller.resolve_review()
        for row in controller.acknowledgement_choices():
            controller.set_acknowledgement(str(row["acknowledgement_id"]), True)
        controller.create_review_confirmation(
            expected_plan_sha256=str(review["plan_sha256"]),
            expected_view_model_sha256=str(review["view_model_sha256"]),
            confirmed_by="FOA-SDK lifecycle tests",
            confirmed_at_utc="2026-07-22T11:00:00Z",
        )
        result = controller.review_result
        confirmation = controller.confirmation_result
        assert isinstance(result, dict) and isinstance(confirmation, dict)
        return build_receipt(dict(result["plan"]), dict(result["view_model"]), dict(confirmation))

    def session(self, operation: str = "install") -> dict[str, object]:
        handoff = build_handoff(
            self.accepted_receipt(),
            operation=operation,
            target_reference="installation.foa-sdk.default",
            prior_installation_reference=None if operation == "install" else "installation.foa-sdk.previous",
            requested_by="FOA-SDK lifecycle tests",
            requested_at_utc="2026-07-22T12:00:00Z",
        )
        token = build_capability_token(
            handoff,
            issuer="FOA-SDK package-engine reviewer",
            subject="FOA-SDK lifecycle intake",
            issued_at_utc="2026-07-22T12:05:00Z",
            expires_at_utc="2026-07-22T12:30:00Z",
            nonce=f"token.foa-sdk.lifecycle-{operation}",
        )
        return build_engine_session(
            handoff,
            token,
            session_reference=f"session.foa-sdk.lifecycle-{operation}",
            accepted_by="FOA-SDK lifecycle tests",
            accepted_at_utc="2026-07-22T12:10:00Z",
        )

    def executable_sha256(self) -> str:
        digest = hashlib.sha256()
        with Path(sys.executable).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def launch_result(self, session: dict[str, object], *, code: int = 0) -> dict[str, object]:
        grant = build_launch_grant(
            session,
            executable_reference="executable.foa-sdk.python",
            executable_sha256=self.executable_sha256(),
            argv=["-c", f"import os, sys; print(os.environ['FOA_LIFECYCLE_TEST']); sys.exit({code})"],
            environment={"FOA_LIFECYCLE_TEST": "ok"},
            timeout_seconds=10,
            output_limit_bytes=4096,
            issuer="FOA-SDK process reviewer",
            issued_at_utc="2026-07-22T12:11:00Z",
            expires_at_utc="2026-07-22T12:20:00Z",
            nonce=f"grant.foa-sdk.launch-{code}",
        )
        return launch_process(
            grant,
            Path(sys.executable).resolve(),
            REPO_ROOT.resolve(),
            launched_at_utc="2026-07-22T12:12:00Z",
        )

    def copy_receipt(self, session: dict[str, object]) -> dict[str, object]:
        grant = build_copy_grant(
            session,
            issuer="FOA-SDK copy reviewer",
            issued_at_utc="2026-07-22T12:11:00Z",
            expires_at_utc="2026-07-22T12:25:00Z",
            nonce="grant.foa-sdk.copy-lifecycle",
        )
        with tempfile.TemporaryDirectory() as temporary:
            return stage_payload(
                grant,
                REPO_ROOT,
                Path(temporary) / "foa-lifecycle-staging",
                copied_at_utc="2026-07-22T12:12:00Z",
            )

    def lifecycle_grant(self, session: dict[str, object]) -> dict[str, object]:
        return build_lifecycle_grant(
            session,
            operation=str(session["operation"]),
            issuer="FOA-SDK lifecycle reviewer",
            issued_at_utc="2026-07-22T12:13:00Z",
            expires_at_utc="2026-07-22T12:25:00Z",
            nonce="grant.foa-sdk.lifecycle",
        )

    def test_grant_is_deterministic_and_operation_bound(self) -> None:
        session = self.session("install")
        first = self.lifecycle_grant(session)
        second = self.lifecycle_grant(session)
        self.assertEqual(first, second)
        self.assertEqual(first["capability"], "package-engine.execute.install")
        self.assertEqual(first["requires_copy_receipt"], True)
        self.assertTrue(all(value is False for value in first["authority"].values()))
        self.assertEqual(validate_lifecycle_grant(first), first)
        with self.assertRaisesRegex(LifecycleCoordinatorError, "must match"):
            build_lifecycle_grant(
                session,
                operation="uninstall",
                issuer="FOA-SDK lifecycle reviewer",
                issued_at_utc="2026-07-22T12:13:00Z",
                expires_at_utc="2026-07-22T12:25:00Z",
                nonce="grant.foa-sdk.lifecycle-wrong",
            )

    def test_lifecycle_operation_vocab_covers_all_documented_operations(self) -> None:
        self.assertEqual(set(OPERATIONS), {"install", "repair", "upgrade", "rollback", "uninstall"})

    def test_install_coordinates_copy_and_process_success_without_forbidden_mutations(self) -> None:
        session = self.session("install")
        result = coordinate_lifecycle(
            self.lifecycle_grant(session),
            copy_receipt=self.copy_receipt(session),
            launch_result=self.launch_result(session),
            completed_at_utc="2026-07-22T12:14:00Z",
        )
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["copy_confirmed"])
        self.assertTrue(result["process_launch_confirmed"])
        self.assertFalse(result["elevation_request_confirmed"])
        self.assertTrue(result["lifecycle_completed"])
        self.assertFalse(result["product_or_game_directory_mutated"])
        self.assertFalse(result["runtime_executed"])
        self.assertFalse(result["save_mutated"])
        self.assertFalse(result["signing_performed"])
        self.assertFalse(result["publication_performed"])
        self.assertFalse(result["catalog_mutated"])
        self.assertFalse(result["evidence_promoted"])
        self.assertEqual(validate_lifecycle_result(result), result)

    def test_install_requires_copy_evidence(self) -> None:
        session = self.session("install")
        with self.assertRaisesRegex(LifecycleCoordinatorError, "requires a verified package copy receipt"):
            coordinate_lifecycle(
                self.lifecycle_grant(session),
                launch_result=self.launch_result(session),
                completed_at_utc="2026-07-22T12:14:00Z",
            )

    def test_nonzero_launch_blocks_lifecycle_completion(self) -> None:
        session = self.session("install")
        result = coordinate_lifecycle(
            self.lifecycle_grant(session),
            copy_receipt=self.copy_receipt(session),
            launch_result=self.launch_result(session, code=7),
            completed_at_utc="2026-07-22T12:14:00Z",
        )
        self.assertEqual(result["status"], "blocked-nonzero-return")
        self.assertEqual(result["non_elevated_return_code"], 7)
        self.assertFalse(result["lifecycle_completed"])

    def test_tampered_grant_and_cross_session_evidence_fail_closed(self) -> None:
        session = self.session("install")
        grant = copy.deepcopy(self.lifecycle_grant(session))
        grant["operation"] = "repair"
        with self.assertRaises(LifecycleCoordinatorError):
            validate_lifecycle_grant(grant)

        launch = copy.deepcopy(self.launch_result(session))
        launch["session_sha256"] = "0" * 64
        with self.assertRaises(LifecycleCoordinatorError):
            coordinate_lifecycle(
                self.lifecycle_grant(session),
                copy_receipt=self.copy_receipt(session),
                launch_result=launch,
                completed_at_utc="2026-07-22T12:14:00Z",
            )

    def test_elevation_result_requires_explicit_lifecycle_allowance(self) -> None:
        session = self.session("install")
        fake_elevation = {
            "schema_version": 1,
            "result_scope": "package-elevation-result",
            "session_sha256": session["session_sha256"],
            "launch_grant_sha256": "1" * 64,
            "elevation_grant_sha256": "2" * 64,
            "consent_sha256": "3" * 64,
            "executable_reference": "executable.foa-sdk.python",
            "executable_sha256": self.executable_sha256(),
            "executable_size_bytes": 1,
            "argv_sha256": "4" * 64,
            "environment_sha256": "5" * 64,
            "requested_at_utc": "2026-07-22T12:12:00Z",
            "backend_code": 42,
            "elevation_requested": True,
            "consent_ui_suppressed": False,
            "credentials_collected": False,
            "process_completion_observed": False,
            "statement": "fake elevation receipt for lifecycle rejection test",
            "authority": {field: field == "elevation" for field in ("acquisition", "installation", "elevation", "game_launch", "runtime_execution", "deployment", "save_mutation", "signing", "publication", "catalog_mutation", "evidence_promotion")},
        }
        from wizard_view_model import sha256  # noqa: E402
        fake_elevation["result_sha256"] = sha256(fake_elevation)
        with self.assertRaisesRegex(LifecycleCoordinatorError, "does not allow elevation"):
            coordinate_lifecycle(
                self.lifecycle_grant(session),
                copy_receipt=self.copy_receipt(session),
                elevation_result=fake_elevation,
                completed_at_utc="2026-07-22T12:14:00Z",
            )

    def test_source_does_not_reintroduce_lower_level_execution_surfaces(self) -> None:
        source = (REPO_ROOT / "Installer/Bootstrapper/LifecycleCoordinator/Source/lifecycle_execution_coordinator.py").read_text(encoding="utf-8")
        for forbidden in (
            "subprocess", "ShellExecute", "ctypes", "stage_payload(", "launch_process(", "request_elevation(",
            "os.open", "os.rename", "socket", "requests", "password",
        ):
            self.assertNotIn(forbidden, source)
        for required in ("credentials_collected", "package-engine.execute.", "validate_launch_result", "package-payload-copy-receipt", "package-elevation-result"):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
