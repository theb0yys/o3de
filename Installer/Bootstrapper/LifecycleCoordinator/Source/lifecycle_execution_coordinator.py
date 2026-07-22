#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Authenticated lifecycle coordinator for reviewed lower-level execution evidence."""
from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path
from typing import Mapping

INSTALLER_ROOT = Path(__file__).resolve().parents[3]
for root in (
    INSTALLER_ROOT / "Bootstrapper" / "PackageEngine" / "Source",
    INSTALLER_ROOT / "Bootstrapper" / "PackageCopier" / "Source",
    INSTALLER_ROOT / "Bootstrapper" / "ProcessLauncher" / "Source",
    INSTALLER_ROOT / "Bootstrapper" / "ElevationHelper" / "Source",
    INSTALLER_ROOT / "Bootstrapper" / "ElevatedCompletionReceipt" / "Source",
    INSTALLER_ROOT / "Bootstrapper" / "Security" / "Source",
    INSTALLER_ROOT / "SuiteWizard" / "ViewModel" / "Source",
):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from capability_elevation_helper import ElevationError, validate_elevation_result  # noqa: E402
from capability_process_launcher import ProcessLaunchError, validate_launch_result  # noqa: E402
from elevated_completion_receipt import (  # noqa: E402
    ElevatedCompletionReceiptError,
    validate_elevated_completion_observation,
)
from execution_security import (  # noqa: E402
    ExecutionSecurityError,
    seal_authenticated_record,
    sha256,
    utc_datetime,
    verify_sealed_record,
)
from package_engine import PackageEngineError, validate_engine_session  # noqa: E402
from package_payload_copier import PackageCopyError, validate_copy_receipt  # noqa: E402
from wizard_view_model import AUTHORITY_FIELDS  # noqa: E402

OPERATIONS = ("install", "repair", "upgrade", "rollback", "uninstall")
REQUIRES_COPY_RECEIPT = frozenset(("install", "repair", "upgrade"))
GRANT_SCOPE = "package-lifecycle-operation-grant"
RESULT_SCOPE = "package-lifecycle-operation-result"
MAX_GRANT_SECONDS = 900
REFERENCE_RE = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GRANT_STATEMENT = "This grant coordinates one authenticated lifecycle operation from exact lower-level evidence only."
RESULT_STATEMENT = "This result records lifecycle coordination and grants no installation-state publication authority."


class LifecycleCoordinatorError(RuntimeError):
    pass


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise LifecycleCoordinatorError(f"{label} must be an object.")
    return value


def _text(value: object, label: str, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise LifecycleCoordinatorError(f"{label} must be non-empty trimmed text of at most {maximum} characters.")
    return value


def _reference(value: object, label: str) -> str:
    result = _text(value, label, 128)
    if REFERENCE_RE.fullmatch(result) is None:
        raise LifecycleCoordinatorError(f"{label} must be a stable namespaced logical ID.")
    return result


def _hash(value: object, label: str) -> str:
    result = _text(value, label, 64)
    if SHA256_RE.fullmatch(result) is None:
        raise LifecycleCoordinatorError(f"{label} must be a lowercase SHA-256 value.")
    return result


def _utc(value: object, label: str) -> str:
    try:
        utc_datetime(value, label)
    except ExecutionSecurityError as exc:
        raise LifecycleCoordinatorError(str(exc)) from exc
    return str(value)


def _operation(value: object) -> str:
    result = _text(value, "operation", 32)
    if result not in OPERATIONS:
        raise LifecycleCoordinatorError("operation must be one of: " + ", ".join(OPERATIONS) + ".")
    return result


def _authority() -> dict[str, bool]:
    return {field: False for field in AUTHORITY_FIELDS}


def _bool(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise LifecycleCoordinatorError(f"{label} must be a boolean.")
    return bool(value)


def _optional_hash(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _hash(value, label)


def build_lifecycle_grant(
    session: Mapping[str, object], *, authority_key_path: Path, operation: str, issuer: str,
    issued_at_utc: str, expires_at_utc: str, nonce: str, allow_elevation_result: bool = False,
) -> dict[str, object]:
    try:
        checked = validate_engine_session(session, authority_key_path=authority_key_path)
    except PackageEngineError as exc:
        raise LifecycleCoordinatorError(f"Package-engine session verification failed: {exc}") from exc
    checked_operation = _operation(operation)
    if checked.get("operation") != checked_operation:
        raise LifecycleCoordinatorError("Lifecycle operation must match the authenticated session operation.")
    capability = f"package-engine.execute.{checked_operation}"
    capabilities = checked.get("authorized_capabilities")
    if not isinstance(capabilities, list) or capability not in capabilities:
        raise LifecycleCoordinatorError("Authenticated session does not grant the requested lifecycle capability.")
    if allow_elevation_result and "package-engine.elevation" not in capabilities:
        raise LifecycleCoordinatorError("Elevation evidence requires package-engine.elevation.")
    issued = utc_datetime(issued_at_utc, "issued_at_utc"); expires = utc_datetime(expires_at_utc, "expires_at_utc")
    accepted = utc_datetime(checked["accepted_at_utc"], "session.accepted_at_utc")
    if issued < accepted or expires <= issued or expires - issued > dt.timedelta(seconds=MAX_GRANT_SECONDS):
        raise LifecycleCoordinatorError("Lifecycle grant must follow session acceptance and expire within 15 minutes.")
    base = {
        "schema_version": 2, "grant_scope": GRANT_SCOPE, "session_sha256": checked["session_sha256"],
        "operation": checked_operation, "capability": capability,
        "requires_copy_receipt": checked_operation in REQUIRES_COPY_RECEIPT,
        "requires_execution_evidence": True, "allow_elevation_result": bool(allow_elevation_result),
        "issuer": _text(issuer, "issuer", 160), "issued_at_utc": _utc(issued_at_utc, "issued_at_utc"),
        "expires_at_utc": _utc(expires_at_utc, "expires_at_utc"), "nonce": _reference(nonce, "nonce"),
        "session": checked, "statement": GRANT_STATEMENT, "authority": _authority(),
    }
    try:
        return seal_authenticated_record(
            base, authority_key_path=authority_key_path, digest_field="grant_sha256"
        )
    except ExecutionSecurityError as exc:
        raise LifecycleCoordinatorError(f"Lifecycle grant authentication failed: {exc}") from exc


def validate_lifecycle_grant(grant: Mapping[str, object], *, authority_key_path: Path) -> dict[str, object]:
    document = dict(grant)
    if document.get("schema_version") != 2 or document.get("grant_scope") != GRANT_SCOPE or document.get("statement") != GRANT_STATEMENT or document.get("authority") != _authority():
        raise LifecycleCoordinatorError("Lifecycle grant contract is invalid.")
    try:
        verify_sealed_record(
            document, authority_key_path=authority_key_path, digest_field="grant_sha256"
        )
    except ExecutionSecurityError as exc:
        raise LifecycleCoordinatorError(f"Lifecycle grant authentication failed: {exc}") from exc
    expected = build_lifecycle_grant(
        _object(document.get("session"), "grant.session"), authority_key_path=authority_key_path,
        operation=_operation(document.get("operation")), issuer=_text(document.get("issuer"), "issuer", 160),
        issued_at_utc=_utc(document.get("issued_at_utc"), "issued_at_utc"),
        expires_at_utc=_utc(document.get("expires_at_utc"), "expires_at_utc"),
        nonce=_reference(document.get("nonce"), "nonce"), allow_elevation_result=bool(document.get("allow_elevation_result")),
    )
    if document != expected:
        raise LifecycleCoordinatorError("Lifecycle grant is stale, altered, or not canonically derived.")
    return document


def coordinate_lifecycle(
    grant: Mapping[str, object], *, authority_key_path: Path, completed_at_utc: str,
    copy_receipt: Mapping[str, object] | None = None,
    launch_result: Mapping[str, object] | None = None,
    elevation_result: Mapping[str, object] | None = None,
    elevated_completion_observation: Mapping[str, object] | None = None,
) -> dict[str, object]:
    checked = validate_lifecycle_grant(grant, authority_key_path=authority_key_path)
    completed = utc_datetime(completed_at_utc, "completed_at_utc")
    if completed < utc_datetime(checked["issued_at_utc"], "issued_at_utc") or completed > utc_datetime(checked["expires_at_utc"], "expires_at_utc"):
        raise LifecycleCoordinatorError("Lifecycle grant is not valid at coordination time.")
    try:
        copy = validate_copy_receipt(copy_receipt, authority_key_path=authority_key_path) if copy_receipt is not None else None
        launch = validate_launch_result(launch_result, authority_key_path=authority_key_path) if launch_result is not None else None
        elevation = validate_elevation_result(elevation_result, authority_key_path=authority_key_path) if elevation_result is not None else None
        elevated_completion = validate_elevated_completion_observation(
            elevated_completion_observation,
            authority_key_path=authority_key_path,
        ) if elevated_completion_observation is not None else None
    except (PackageCopyError, ProcessLaunchError, ElevationError, ElevatedCompletionReceiptError) as exc:
        raise LifecycleCoordinatorError(f"Lower-level evidence verification failed: {exc}") from exc
    if checked["requires_copy_receipt"] and copy is None:
        raise LifecycleCoordinatorError("This lifecycle operation requires an authenticated package copy receipt.")
    execution_evidence_count = sum(item is not None for item in (launch, elevation, elevated_completion))
    if execution_evidence_count != 1:
        raise LifecycleCoordinatorError(
            "Provide exactly one authenticated launch, elevation result, or elevated completion observation."
        )
    session_sha = checked["session_sha256"]
    for label, evidence in (
        ("copy", copy),
        ("launch", launch),
        ("elevation", elevation),
        ("elevated completion", elevated_completion),
    ):
        if evidence is not None and evidence.get("session_sha256") != session_sha:
            raise LifecycleCoordinatorError(f"{label} evidence is not bound to the lifecycle session.")
    if (elevation is not None or elevated_completion is not None) and checked.get("allow_elevation_result") is not True:
        raise LifecycleCoordinatorError("Lifecycle grant does not allow elevation result evidence.")
    if elevated_completion is not None and elevated_completion.get("operation") != checked["operation"]:
        raise LifecycleCoordinatorError("Elevated completion observation operation does not match the lifecycle grant.")
    if elevated_completion is not None:
        status = _text(elevated_completion.get("status"), "elevated_completion.status", 64)
        completed_ok = _bool(elevated_completion.get("completed"), "elevated_completion.completed")
    elif elevation is not None:
        status = "elevation-requested-pending-completion-receipt"; completed_ok = False
    elif launch.get("timed_out") is True:
        status = "blocked-timeout"; completed_ok = False
    elif launch.get("output_limit_exceeded") is True:
        status = "blocked-output-limit"; completed_ok = False
    elif launch.get("return_code") != 0:
        status = "blocked-nonzero-return"; completed_ok = False
    else:
        status = "completed"; completed_ok = True
    base = {
        "schema_version": 2, "result_scope": RESULT_SCOPE, "grant_sha256": checked["grant_sha256"],
        "session_sha256": session_sha, "operation": checked["operation"], "status": status,
        "completed": completed_ok, "lifecycle_completed": completed_ok,
        "elevation_request_confirmed": elevation is not None or elevated_completion is not None,
        "elevated_completion_observed": elevated_completion is not None,
        "completed_at_utc": _utc(completed_at_utc, "completed_at_utc"),
        "copy_receipt_sha256": copy["copy_receipt_sha256"] if copy else None,
        "launch_result_sha256": launch["result_sha256"] if launch else None,
        "elevation_result_sha256": (
            elevation["result_sha256"] if elevation else (
                elevated_completion["elevation_result_sha256"] if elevated_completion else None
            )
        ),
        "elevated_completion_observation_sha256": (
            elevated_completion["observation_sha256"] if elevated_completion else None
        ),
        "product_directory_mutated": False, "game_directory_mutated": False, "runtime_executed": False,
        "save_mutated": False, "signing_performed": False, "publication_performed": False,
        "catalog_mutated": False, "evidence_promoted": False, "statement": RESULT_STATEMENT,
        "authority": _authority(), "lifecycle_grant": checked,
    }
    try:
        return seal_authenticated_record(
            base, authority_key_path=authority_key_path, digest_field="result_sha256"
        )
    except ExecutionSecurityError as exc:
        raise LifecycleCoordinatorError(f"Lifecycle result authentication failed: {exc}") from exc


def validate_lifecycle_result(
    result: Mapping[str, object], *, authority_key_path: Path
) -> dict[str, object]:
    document = dict(result)
    if (
        document.get("schema_version") != 2
        or document.get("result_scope") != RESULT_SCOPE
        or document.get("statement") != RESULT_STATEMENT
        or document.get("authority") != _authority()
    ):
        raise LifecycleCoordinatorError("Lifecycle result contract is invalid.")
    try:
        verify_sealed_record(
            document, authority_key_path=authority_key_path, digest_field="result_sha256"
        )
    except ExecutionSecurityError as exc:
        raise LifecycleCoordinatorError(f"Lifecycle result authentication failed: {exc}") from exc
    checked_grant = validate_lifecycle_grant(
        _object(document.get("lifecycle_grant"), "result.lifecycle_grant"),
        authority_key_path=authority_key_path,
    )
    if (
        document.get("grant_sha256") != checked_grant["grant_sha256"]
        or document.get("session_sha256") != checked_grant["session_sha256"]
        or document.get("operation") != checked_grant["operation"]
    ):
        raise LifecycleCoordinatorError("Lifecycle result is not bound to its authenticated grant.")
    completed = document.get("status") == "completed"
    elevated = document.get("elevation_result_sha256") is not None
    elevated_completion = document.get("elevated_completion_observation_sha256") is not None
    if (
        document.get("completed") is not completed
        or document.get("lifecycle_completed") is not completed
        or document.get("elevation_request_confirmed") is not elevated
        or document.get("elevated_completion_observed") is not elevated_completion
    ):
        raise LifecycleCoordinatorError("Lifecycle result completion flags are inconsistent.")
    _optional_hash(document.get("elevated_completion_observation_sha256"), "result.elevated_completion_observation_sha256")
    return document


__all__ = ["LifecycleCoordinatorError", "build_lifecycle_grant", "coordinate_lifecycle", "validate_lifecycle_grant", "validate_lifecycle_result"]