# SPDX-License-Identifier: Apache-2.0 OR MIT
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
for root in (
    REPO_ROOT / "Installer/Bootstrapper/InstallationStatePublisher/Source",
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
from installation_state_publisher import (  # noqa: E402
    InstallationStatePublisherError,
    build_publication_grant,
    publish_state_record,
    validate_publication_grant,
    validate_publication_receipt,
    validate_state_record,
)
from lifecycle_execution_coordinator import build_lifecycle_grant, coordinate_lifecycle  # noqa: E402
from package_engine import build_capability_token, build_engine_session  # noqa: E402
from package_payload_copier import build_copy_grant, stage_payload  # noqa: E402
from receipt_execution_handoff import build_handoff  # noqa: E402
from wizard_confirmation_controller import WizardConfirmationController  # noqa: E402
from wizard_view_model import sha256  # noqa: E402


class InstallationStatePublisherTests(unittest.TestCase):
    def accepted_receipt(self) -> dict[str, object]:
        controller = WizardConfirmationController(REPO_ROOT / "Installer")
        review = controller.resolve_review()
        for row in controller.acknowledgement_choices():
            controller.set_acknowledgement(str(row["acknowledgement_id"]), True)
        controller.create_review_confirmation(
            expected_plan_sha256=str(review["plan_sha256"]),
            expected_view_model_sha256=str(review["view_model_sha256"]),
            confirmed_by="FOA-SDK state publisher tests",
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
            requested_by="FOA-SDK state publisher tests",
            requested_at_utc="2026-07-22T12:00:00Z",
        )
        token = build_capability_token(
            handoff,
            issuer="FOA-SDK package-engine reviewer",
            subject="FOA-SDK state publisher intake",
            issued_at_utc="2026-07-22T12:05:00Z",
            expires_at_utc="2026-07-22T12:30:00Z",
            nonce=f"token.foa-sdk.state-{operation}",
        )
        return build_engine_session(
            handoff,
            token,
            session_reference=f"session.foa-sdk.state-{operation}",
            accepted_by="FOA-SDK state publisher tests",
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
            argv=["-c", f"import os, sys; print(os.environ['FOA_STATE_TEST']); sys.exit({code})"],
            environment={"FOA_STATE_TEST": "ok"},
            timeout_seconds=10,
            output_limit_bytes=4096,
            issuer="FOA-SDK process reviewer",
            issued_at_utc="2026-07-22T12:11:00Z",
            expires_at_utc="2026-07-22T12:20:00Z",
            nonce=f"grant.foa-sdk.state-launch-{code}",
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
            nonce="grant.foa-sdk.state-copy",
        )
        with tempfile.TemporaryDirectory() as temporary:
            return stage_payload(
                grant,
                REPO_ROOT,
                Path(temporary) / "foa-state-staging",
                copied_at_utc="2026-07-22T12:12:00Z",
            )

    def lifecycle_result(self, session: dict[str, object], *, code: int = 0) -> dict[str, object]:
        grant = build_lifecycle_grant(
            session,
            operation=str(session["operation"]),
            issuer="FOA-SDK lifecycle reviewer",
            issued_at_utc="2026-07-22T12:13:00Z",
            expires_at_utc="2026-07-22T12:25:00Z",
            nonce=f"grant.foa-sdk.state-lifecycle-{code}",
        )
        return coordinate_lifecycle(
            grant,
            copy_receipt=self.copy_receipt(session),
            launch_result=self.launch_result(session, code=code),
            completed_at_utc="2026-07-22T12:14:00Z",
        )

    def publication_grant(
        self,
        session: dict[str, object],
        lifecycle: dict[str, object],
        *,
        expected_previous_state_sha256: str | None = None,
        nonce: str = "grant.foa-sdk.state-publication",
    ) -> dict[str, object]:
        return build_publication_grant(
            session,
            lifecycle,
            state_reference="installation.foa-sdk.default",
            expected_previous_state_sha256=expected_previous_state_sha256,
            issuer="FOA-SDK state publisher",
            issued_at_utc="2026-07-22T12:15:00Z",
            expires_at_utc="2026-07-22T12:25:00Z",
            nonce=nonce,
        )

    def test_publication_grant_is_deterministic_and_bound_to_completed_lifecycle(self) -> None:
        session = self.session("install")
        lifecycle = self.lifecycle_result(session)
        first = self.publication_grant(session, lifecycle)
        second = self.publication_grant(session, lifecycle)
        self.assertEqual(first, second)
        self.assertEqual(first["capability"], "package-engine.publish-installation-state")
        self.assertEqual(first["lifecycle_result_sha256"], lifecycle["result_sha256"])
        self.assertTrue(all(value is False for value in first["authority"].values()))
        self.assertEqual(validate_publication_grant(first), first)

    def test_publish_completed_install_state_atomically_without_forbidden_side_effects(self) -> None:
        session = self.session("install")
        lifecycle = self.lifecycle_result(session)
        grant = self.publication_grant(session, lifecycle)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            receipt = publish_state_record(grant, root, published_at_utc="2026-07-22T12:16:00Z")
            self.assertEqual(validate_publication_receipt(receipt), receipt)
            self.assertTrue(receipt["state_file_written"])
            self.assertFalse(receipt["atomic_replace_used"])
            state_file = root / str(receipt["state_file_name"])
            self.assertTrue(state_file.is_file())
            record = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(validate_state_record(record), record)
            self.assertEqual(record["state_status"], "active")
            self.assertEqual(record["operation"], "install")
            self.assertEqual(record["lifecycle_result_sha256"], lifecycle["result_sha256"])
            for field in (
                "product_or_game_directory_mutated", "runtime_executed", "save_mutated",
                "signing_performed", "publication_performed", "catalog_mutated", "evidence_promoted",
            ):
                self.assertFalse(record[field])
            for field in (
                "product_or_game_directory_mutated", "runtime_executed", "save_mutated",
                "signing_performed", "network_publication_performed", "catalog_mutated", "evidence_promoted",
            ):
                self.assertFalse(receipt[field])

    def test_expected_previous_state_hash_controls_replacement(self) -> None:
        session = self.session("install")
        lifecycle = self.lifecycle_result(session)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            first = publish_state_record(
                self.publication_grant(session, lifecycle),
                root,
                published_at_utc="2026-07-22T12:16:00Z",
            )
            second = publish_state_record(
                self.publication_grant(
                    session,
                    lifecycle,
                    expected_previous_state_sha256=str(first["state_file_sha256"]),
                    nonce="grant.foa-sdk.state-publication-replace",
                ),
                root,
                published_at_utc="2026-07-22T12:17:00Z",
            )
            self.assertTrue(second["atomic_replace_used"])
            self.assertEqual(second["previous_state_sha256"], first["state_file_sha256"])

    def test_publication_rejects_blocked_or_elevation_pending_lifecycle_results(self) -> None:
        session = self.session("install")
        blocked = self.lifecycle_result(session, code=7)
        with self.assertRaisesRegex(InstallationStatePublisherError, "completed lifecycle"):
            self.publication_grant(session, blocked)
        pending = copy.deepcopy(self.lifecycle_result(session))
        pending["status"] = "elevation-requested-pending-completion-receipt"
        pending["lifecycle_completed"] = False
        pending["elevation_request_confirmed"] = True
        pending["result_sha256"] = sha256({key: value for key, value in pending.items() if key != "result_sha256"})
        with self.assertRaisesRegex(InstallationStatePublisherError, "completed lifecycle"):
            self.publication_grant(session, pending)

    def test_existing_state_mismatch_and_tampering_fail_closed(self) -> None:
        session = self.session("install")
        lifecycle = self.lifecycle_result(session)
        grant = self.publication_grant(session, lifecycle)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "installation.foa-sdk.default.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(InstallationStatePublisherError, "Existing state hash"):
                publish_state_record(grant, root, published_at_utc="2026-07-22T12:16:00Z")
        tampered = copy.deepcopy(grant)
        tampered["state_reference"] = "installation.foa-sdk.other"
        with self.assertRaises(InstallationStatePublisherError):
            validate_publication_grant(tampered)

    def test_source_does_not_reintroduce_runtime_or_product_mutation_surfaces(self) -> None:
        source = (REPO_ROOT / "Installer/Bootstrapper/InstallationStatePublisher/Source/installation_state_publisher.py").read_text(encoding="utf-8")
        for forbidden in (
            "subprocess", "ShellExecute", "ctypes", "launch_process(", "request_elevation(",
            "stage_payload(", "socket", "requests", "password", "credential",
        ):
            self.assertNotIn(forbidden, source)
        for required in (
            "package-engine.publish-installation-state", "os.replace", "expected_previous_state_sha256",
            "validate_lifecycle_result", "state_file_written", "product_or_game_directory_mutated",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
