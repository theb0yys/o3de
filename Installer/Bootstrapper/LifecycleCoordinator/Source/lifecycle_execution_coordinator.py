#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Operation-level lifecycle coordinator for reviewed installer execution receipts."""
from __future__ import annotations

import datetime as dt
import re
import sys
from typing import Mapping

from pathlib import Path

INSTALLER_ROOT = Path(__file__).resolve().parents[3]
for root in (
    INSTALLER_ROOT / "Bootstrapper" / "PackageEngine" / "Source",
    INSTALLER_ROOT / "Bootstrapper" / "ProcessLauncher" / "Source",
    INSTALLER_ROOT / "SuiteWizard" / "ViewModel" / "Source",
):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from capability_process_launcher import ProcessLaunchError, validate_launch_result  # noqa: E402
from package_engine import PackageEngineError, validate_engine_session  # noqa: E402
from wizard_view_model import AUTHORITY_FIELDS, canonical_json, sha256  # noqa: E402

OPERATIONS = ("install", "repair", "upgrade", "rollback", "uninstall")
REQUIRES_COPY_RECEIPT = frozenset(("install", "repair", "upgrade"))
GRANT_SCOPE = "package-lifecycle-operation-grant"
RESULT_SCOPE = "package-lifecycle-operation-result"
MAX_GRANT_SECONDS = 900
REFERENCE_RE = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GRANT_STATEMENT = (
    "This grant authorizes lifecycle coordination for one exact package-engine operation. "
    "It can only consume already-verified copy, process-launch, or elevation evidence and "
    "does not create a new copy, process, elevation, runtime, signing, publication, catalog, "
    "save-mutation, or evidence-promotion path."
)
RESULT_STATEMENT = (
    "This result records the coordinator decision for one package lifecycle operation based "
    "only on lower-level reviewed receipts. It does not mutate product or game directories, "
    "publish installation state, execute runtime adapters, sign artifacts, or promote evidence."
)


class LifecycleCoordinatorError(RuntimeError):
    pass


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise LifecycleCoordinatorError(f"{label} must be an object.")
    return value


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise LifecycleCoordinatorError(f"{label} must be an array.")
    return value


def _text(value: object, label: str, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise LifecycleCoordinatorError(f"{label} must be a non-empty trimmed string of at most {maximum} characters.")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise LifecycleCoordinatorError(f"{label} contains a forbidden control character.")
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
    result = _text(value, label, 64)
    if not result.endswith("Z") or "T" not in result:
        raise LifecycleCoordinatorError(f"{label} must be an ISO-8601 UTC timestamp ending in Z.")
    try:
        parsed = dt.datetime.fromisoformat(result[:-1] + "+00:00")
    except ValueError as exc:
        raise LifecycleCoordinatorError(f"{label} is not a valid ISO-8601 timestamp.") from exc
    if parsed.utcoffset() != dt.timedelta(0):
        raise LifecycleCoordinatorError(f"{label} must use UTC.")
    return result


def _utc_dt(value: object, label: str) -> dt.datetime:
    return dt.datetime.fromisoformat(_utc(value, label)[:-1] + "+00:00")


def _operation(value: object) -> str:
    result = _text(value, "operation", 32)
    if result not in OPERATIONS:
        raise LifecycleCoordinatorError("operation must be one of: " + ", ".join(OPERATIONS) + ".")
    return result


def _authority() -> dict[str, bool]:
    return {field: False for field in AUTHORITY_FIELDS}


def _validate_authority(value: object, label: str) -> None:
    authority = _object(value, label)
    if authority != _authority():
        raise LifecycleCoordinatorError(f"{label} must contain the exact all-false authority record.")


def _operation_capability(operation: str) -> str:
    return f"package-engine.execute.{operation}"


def _checked_session(session: Mapping[str, object]) -> dict[str, object]:
    try:
        return validate_engine_session(session)
    except PackageEngineError as exc:
        raise LifecycleCoordinatorError(f"Package-engine session verification failed: {exc}") from exc


def build_lifecycle_grant(
    session: Mapping[str, object], *, operation: str, issuer: str,
    issued_at_utc: str, expires_at_utc: str, nonce: str, allow_elevation_result: bool = False,
) -> dict[str, object]:
    checked = _checked_session(session)
    checked_operation = _operation(operation)
    if checked.get("operation") != checked_operation:
        raise LifecycleCoordinatorError("Lifecycle operation must match the verified package-engine session operation.")
    capabilities = checked.get("authorized_capabilities")
    if not isinstance(capabilities, list) or _operation_capability(checked_operation) not in capabilities:
        raise LifecycleCoordinatorError("Verified session does not grant the requested lifecycle operation capability.")
    if allow_elevation_result and "package-engine.elevation" not in capabilities:
        raise LifecycleCoordinatorError("Elevation result allowance requires package-engine.elevation in the verified session.")
    issued = _utc_dt(issued_at_utc, "issued_at_utc")
    expires = _utc_dt(expires_at_utc, "expires_at_utc")
    accepted = _utc_dt(checked["accepted_at_utc"], "session.accepted_at_utc")
    if issued < accepted:
        raise LifecycleCoordinatorError("issued_at_utc must not precede session acceptance.")
    if expires <= issued or expires - issued > dt.timedelta(seconds=MAX_GRANT_SECONDS):
        raise LifecycleCoordinatorError("Lifecycle grant expiry must be after issuance and within 15 minutes.")
    requires_copy = checked_operation in REQUIRES_COPY_RECEIPT
    base = {
        "schema_version": 1,
        "grant_scope": GRANT_SCOPE,
        "session_sha256": checked["session_sha256"],
        "operation": checked_operation,
        "capability": _operation_capability(checked_operation),
        "requires_copy_receipt": requires_copy,
        "requires_execution_evidence": True,
        "allow_elevation_result": bool(allow_elevation_result),
        "issuer": _text(issuer, "issuer", 160),
        "issued_at_utc": _utc(issued_at_utc, "issued_at_utc"),
        "expires_at_utc": _utc(expires_at_utc, "expires_at_utc"),
        "nonce": _reference(nonce, "nonce"),
        "session": checked,
        "statement": GRANT_STATEMENT,
        "authority": _authority(),
    }
    return {**base, "grant_sha256": sha256(base)}


def validate_lifecycle_grant(grant: Mapping[str, object]) -> dict[str, object]:
    document = dict(grant)
    if document.get("schema_version") != 1 or document.get("grant_scope") != GRANT_SCOPE:
        raise LifecycleCoordinatorError("Lifecycle grant schema or scope is invalid.")
    if document.get("statement") != GRANT_STATEMENT:
        raise LifecycleCoordinatorError("Lifecycle grant statement was altered.")
    _validate_authority(document.get("authority"), "grant.authority")
    declared = _hash(document.get("grant_sha256"), "grant.grant_sha256")
    unsigned = {key: value for key, value in document.items() if key != "grant_sha256"}
    if sha256(unsigned) != declared:
        raise LifecycleCoordinatorError("Lifecycle grant fingerprint does not match its content.")
    expected = build_lifecycle_grant(
        _object(document.get("session"), "grant.session"),
        operation=_operation(document.get("operation")),
        issuer=_text(document.get("issuer"), "grant.issuer", 160),
        issued_at_utc=_utc(document.get("issued_at_utc"), "grant.issued_at_utc"),
        expires_at_utc=_utc(document.get("expires_at_utc"), "grant.expires_at_utc"),
        nonce=_reference(document.get("nonce"), "grant.nonce"),
        allow_elevation_result=bool(document.get("allow_elevation_result")),
    )
    if document != expected:
        raise LifecycleCoordinatorError("Lifecycle grant is stale, altered, or not canonically derived.")
    return document


def validate_copy_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    document = dict(receipt)
    if document.get("schema_version") != 1 or document.get("receipt_scope") != "package-payload-copy-receipt":
        raise LifecycleCoordinatorError("Copy receipt schema or scope is invalid.")
    for field, expected in (
        ("copy_performed", True),
        ("process_launched", False),
        ("elevation_requested", False),
        ("installation_finalized", False),
    ):
        if document.get(field) is not expected:
            raise LifecycleCoordinatorError(f"Copy receipt flag {field} is invalid.")
    _validate_authority(document.get("authority"), "copy_receipt.authority")
    files = _array(document.get("files"), "copy_receipt.files")
    if document.get("file_count") != len(files):
        raise LifecycleCoordinatorError("Copy receipt file_count does not match files.")
    if document.get("size_bytes") != sum(int(_object(row, "copy_receipt.files[]").get("size_bytes")) for row in files):
        raise LifecycleCoordinatorError("Copy receipt size_bytes does not match files.")
    declared = _hash(document.get("copy_receipt_sha256"), "copy_receipt.copy_receipt_sha256")
    unsigned = {key: value for key, value in document.items() if key != "copy_receipt_sha256"}
    if sha256(unsigned) != declared:
        raise LifecycleCoordinatorError("Copy receipt fingerprint does not match its content.")
    return document


def validate_elevation_result(result: Mapping[str, object]) -> dict[str, object]:
    document = dict(result)
    if document.get("schema_version") != 1 or document.get("result_scope") != "package-elevation-result":
        raise LifecycleCoordinatorError("Elevation result schema or scope is invalid.")
    for field, expected in (
        ("elevation_requested", True),
        ("consent_ui_suppressed", False),
        ("credentials_collected", False),
        ("process_completion_observed", False),
    ):
        if document.get(field) is not expected:
            raise LifecycleCoordinatorError(f"Elevation result flag {field} is invalid.")
    authority = _object(document.get("authority"), "elevation_result.authority")
    expected_authority = {field: field == "elevation" for field in AUTHORITY_FIELDS}
    if authority != expected_authority:
        raise LifecycleCoordinatorError("Elevation result must grant only the elevation authority field.")
    declared = _hash(document.get("result_sha256"), "elevation_result.result_sha256")
    unsigned = {key: value for key, value in document.items() if key != "result_sha256"}
    if sha256(unsigned) != declared:
        raise LifecycleCoordinatorError("Elevation result fingerprint does not match its content.")
    return document


def coordinate_lifecycle(
    grant: Mapping[str, object], *, completed_at_utc: str,
    copy_receipt: Mapping[str, object] | None = None,
    launch_result: Mapping[str, object] | None = None,
    elevation_result: Mapping[str, object] | None = None,
) -> dict[str, object]:
    checked = validate_lifecycle_grant(grant)
    completed = _utc_dt(completed_at_utc, "completed_at_utc")
    if completed < _utc_dt(checked["issued_at_utc"], "grant.issued_at_utc"):
        raise LifecycleCoordinatorError("completed_at_utc must not precede lifecycle grant issuance.")
    if completed > _utc_dt(checked["expires_at_utc"], "grant.expires_at_utc"):
        raise LifecycleCoordinatorError("Lifecycle grant expired before coordination completed.")
    copy = validate_copy_receipt(copy_receipt) if copy_receipt is not None else None
    launch = None
    if launch_result is not None:
        try:
            launch = validate_launch_result(launch_result)
        except ProcessLaunchError as exc:
            raise LifecycleCoordinatorError(f"Process-launch result verification failed: {exc}") from exc
    elevation = validate_elevation_result(elevation_result) if elevation_result is not None else None
    if checked["requires_copy_receipt"] and copy is None:
        raise LifecycleCoordinatorError("This lifecycle operation requires a verified package copy receipt.")
    if launch is None and elevation is None:
        raise LifecycleCoordinatorError("Lifecycle coordination requires process-launch or elevation evidence.")
    session_sha = checked["session_sha256"]
    for label, evidence in (("copy", copy), ("launch", launch), ("elevation", elevation)):
        if evidence is not None and evidence.get("session_sha256") != session_sha:
            raise LifecycleCoordinatorError(f"{label} evidence is not bound to the lifecycle session.")
    if elevation is not None and checked.get("allow_elevation_result") is not True:
        raise LifecycleCoordinatorError("Lifecycle grant does not allow elevation result evidence.")
    if launch is not None and elevation is not None:
        raise LifecycleCoordinatorError("Lifecycle coordination accepts either direct launch evidence or elevation evidence, not both.")
    status: str
    completed_ok = False
    if elevation is not None:
        status = "elevation-requested-pending-completion-receipt"
    elif launch is not None and launch.get("timed_out") is True:
        status = "blocked-timeout"
    elif launch is not None and launch.get("return_code") != 0:
        status = "blocked-nonzero-return"
    else:
        status = "completed"
        completed_ok = True
    base = {
        "schema_version": 1,
        "result_scope": RESULT_SCOPE,
        "session_sha256": session_sha,
        "lifecycle_grant_sha256": checked["grant_sha256"],
        "operation": checked["operation"],
        "copy_receipt_sha256": None if copy is None else copy["copy_receipt_sha256"],
        "launch_result_sha256": None if launch is None else launch["result_sha256"],
        "elevation_result_sha256": None if elevation is None else elevation["result_sha256"],
        "completed_at_utc": _utc(completed_at_utc, "completed_at_utc"),
        "status": status,
        "copy_confirmed": copy is not None,
        "process_launch_confirmed": launch is not None,
        "elevation_request_confirmed": elevation is not None,
        "non_elevated_return_code": None if launch is None else launch["return_code"],
        "timed_out": False if launch is None else bool(launch["timed_out"]),
        "lifecycle_completed": completed_ok,
        "product_or_game_directory_mutated": False,
        "runtime_executed": False,
        "save_mutated": False,
        "signing_performed": False,
        "publication_performed": False,
        "catalog_mutated": False,
        "evidence_promoted": False,
        "statement": RESULT_STATEMENT,
        "authority": _authority(),
    }
    return {**base, "result_sha256": sha256(base)}


def validate_lifecycle_result(result: Mapping[str, object]) -> dict[str, object]:
    document = dict(result)
    if document.get("schema_version") != 1 or document.get("result_scope") != RESULT_SCOPE:
        raise LifecycleCoordinatorError("Lifecycle result schema or scope is invalid.")
    if document.get("statement") != RESULT_STATEMENT:
        raise LifecycleCoordinatorError("Lifecycle result statement was altered.")
    for field in (
        "product_or_game_directory_mutated", "runtime_executed", "save_mutated", "signing_performed",
        "publication_performed", "catalog_mutated", "evidence_promoted",
    ):
        if document.get(field) is not False:
            raise LifecycleCoordinatorError(f"Lifecycle result forbidden side-effect flag {field} must be false.")
    _validate_authority(document.get("authority"), "result.authority")
    declared = _hash(document.get("result_sha256"), "result.result_sha256")
    unsigned = {key: value for key, value in document.items() if key != "result_sha256"}
    if sha256(unsigned) != declared:
        raise LifecycleCoordinatorError("Lifecycle result fingerprint does not match its content.")
    return document


def canonical_grant_bytes(grant: Mapping[str, object]) -> bytes:
    return canonical_json(validate_lifecycle_grant(grant))


def canonical_result_bytes(result: Mapping[str, object]) -> bytes:
    return canonical_json(validate_lifecycle_result(result))
