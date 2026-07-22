#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""State-backed lifecycle-operation admission gate for reviewed installer flows."""
from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path
from typing import Mapping

INSTALLER_ROOT = Path(__file__).resolve().parents[3]
for root in (
    INSTALLER_ROOT / "Bootstrapper" / "InstallationStateRegistry" / "Source",
    INSTALLER_ROOT / "SuiteWizard" / "ViewModel" / "Source",
):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from installation_state_registry import (  # noqa: E402
    InstallationStateRegistryError,
    validate_lifecycle_eligibility,
)
from wizard_view_model import AUTHORITY_FIELDS, canonical_json, sha256  # noqa: E402

ADMISSION_CAPABILITY = "package-engine.admit-lifecycle-operation"
GRANT_SCOPE = "package-lifecycle-operation-admission-grant"
RECEIPT_SCOPE = "package-lifecycle-operation-admission-receipt"
MAX_GRANT_SECONDS = 900
OPERATIONS = ("install", "repair", "upgrade", "rollback", "uninstall")
REFERENCE_RE = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GRANT_STATEMENT = (
    "This grant authorizes one state-backed lifecycle-operation admission decision from one exact "
    "validated installation-state eligibility document. It does not create a lifecycle handoff, "
    "copy payloads, launch processes, request elevation, publish state, mutate products, run runtime "
    "code, sign artifacts, mutate catalogs, mutate saves, or promote evidence."
)
RECEIPT_STATEMENT = (
    "This receipt records admission of one lifecycle operation after state-backed eligibility "
    "verification. It is not a lifecycle handoff or package-engine session and grants no later "
    "execution authority by itself."
)


class LifecycleOperationAdmissionError(RuntimeError):
    pass


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise LifecycleOperationAdmissionError(f"{label} must be an object.")
    return value


def _text(value: object, label: str, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise LifecycleOperationAdmissionError(f"{label} must be a non-empty trimmed string of at most {maximum} characters.")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise LifecycleOperationAdmissionError(f"{label} contains a forbidden control character.")
    return value


def _reference(value: object, label: str) -> str:
    result = _text(value, label, 128)
    if REFERENCE_RE.fullmatch(result) is None:
        raise LifecycleOperationAdmissionError(f"{label} must be a stable namespaced logical ID.")
    return result


def _optional_reference(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _reference(value, label)


def _hash(value: object, label: str) -> str:
    result = _text(value, label, 64)
    if SHA256_RE.fullmatch(result) is None:
        raise LifecycleOperationAdmissionError(f"{label} must be a lowercase SHA-256 value.")
    return result


def _utc(value: object, label: str) -> str:
    result = _text(value, label, 64)
    if not result.endswith("Z") or "T" not in result:
        raise LifecycleOperationAdmissionError(f"{label} must be an ISO-8601 UTC timestamp ending in Z.")
    try:
        parsed = dt.datetime.fromisoformat(result[:-1] + "+00:00")
    except ValueError as exc:
        raise LifecycleOperationAdmissionError(f"{label} is not a valid ISO-8601 timestamp.") from exc
    if parsed.utcoffset() != dt.timedelta(0):
        raise LifecycleOperationAdmissionError(f"{label} must use UTC.")
    return result


def _utc_dt(value: object, label: str) -> dt.datetime:
    return dt.datetime.fromisoformat(_utc(value, label)[:-1] + "+00:00")


def _operation(value: object, label: str = "operation") -> str:
    result = _text(value, label, 32)
    if result not in OPERATIONS:
        raise LifecycleOperationAdmissionError("operation must be one of: " + ", ".join(OPERATIONS) + ".")
    return result


def _authority() -> dict[str, bool]:
    return {field: False for field in AUTHORITY_FIELDS}


def _validate_authority(value: object, label: str) -> None:
    authority = _object(value, label)
    if authority != _authority():
        raise LifecycleOperationAdmissionError(f"{label} must contain the exact all-false authority record.")


def _checked_eligibility(eligibility: Mapping[str, object]) -> dict[str, object]:
    try:
        checked = validate_lifecycle_eligibility(eligibility)
    except InstallationStateRegistryError as exc:
        raise LifecycleOperationAdmissionError(f"Lifecycle eligibility verification failed: {exc}") from exc
    if checked.get("eligible") is not True:
        raise LifecycleOperationAdmissionError("Only eligible lifecycle operations can receive admission.")
    return checked


def build_admission_grant(
    eligibility: Mapping[str, object], *, issuer: str, issued_at_utc: str, expires_at_utc: str, nonce: str,
) -> dict[str, object]:
    checked = _checked_eligibility(eligibility)
    issued = _utc_dt(issued_at_utc, "issued_at_utc")
    expires = _utc_dt(expires_at_utc, "expires_at_utc")
    decided = _utc_dt(checked["decided_at_utc"], "eligibility.decided_at_utc")
    if issued < decided:
        raise LifecycleOperationAdmissionError("issued_at_utc must not precede eligibility decision time.")
    if expires <= issued or expires - issued > dt.timedelta(seconds=MAX_GRANT_SECONDS):
        raise LifecycleOperationAdmissionError("Admission grant expiry must be after issuance and within 15 minutes.")
    operation = _operation(checked.get("operation"), "eligibility.operation")
    target = _reference(checked.get("target_reference"), "eligibility.target_reference")
    base = {
        "schema_version": 1,
        "grant_scope": GRANT_SCOPE,
        "capability": ADMISSION_CAPABILITY,
        "eligibility_sha256": _hash(checked.get("eligibility_sha256"), "eligibility.eligibility_sha256"),
        "snapshot_sha256": _hash(checked.get("snapshot_sha256"), "eligibility.snapshot_sha256"),
        "operation": operation,
        "target_reference": target,
        "current_state_reference": _optional_reference(
            checked.get("current_state_reference"),
            "eligibility.current_state_reference",
        ),
        "recommended_prior_installation_reference": _optional_reference(
            checked.get("recommended_prior_installation_reference"),
            "eligibility.recommended_prior_installation_reference",
        ),
        "current_state_status": checked.get("current_state_status"),
        "current_state_file_sha256": None if checked.get("current_state_file_sha256") is None else _hash(
            checked.get("current_state_file_sha256"),
            "eligibility.current_state_file_sha256",
        ),
        "eligibility_reason": _text(checked.get("reason"), "eligibility.reason", 128),
        "issuer": _text(issuer, "issuer", 160),
        "issued_at_utc": _utc(issued_at_utc, "issued_at_utc"),
        "expires_at_utc": _utc(expires_at_utc, "expires_at_utc"),
        "nonce": _reference(nonce, "nonce"),
        "eligibility": checked,
        "statement": GRANT_STATEMENT,
        "authority": _authority(),
    }
    return {**base, "grant_sha256": sha256(base)}


def validate_admission_grant(grant: Mapping[str, object]) -> dict[str, object]:
    document = dict(grant)
    if document.get("schema_version") != 1 or document.get("grant_scope") != GRANT_SCOPE:
        raise LifecycleOperationAdmissionError("Admission grant schema or scope is invalid.")
    if document.get("capability") != ADMISSION_CAPABILITY or document.get("statement") != GRANT_STATEMENT:
        raise LifecycleOperationAdmissionError("Admission grant capability or statement is invalid.")
    _validate_authority(document.get("authority"), "grant.authority")
    declared = _hash(document.get("grant_sha256"), "grant.grant_sha256")
    unsigned = {key: value for key, value in document.items() if key != "grant_sha256"}
    if sha256(unsigned) != declared:
        raise LifecycleOperationAdmissionError("Admission grant fingerprint does not match its content.")
    expected = build_admission_grant(
        _object(document.get("eligibility"), "grant.eligibility"),
        issuer=_text(document.get("issuer"), "grant.issuer", 160),
        issued_at_utc=_utc(document.get("issued_at_utc"), "grant.issued_at_utc"),
        expires_at_utc=_utc(document.get("expires_at_utc"), "grant.expires_at_utc"),
        nonce=_reference(document.get("nonce"), "grant.nonce"),
    )
    if document != expected:
        raise LifecycleOperationAdmissionError("Admission grant is stale, altered, or not canonically derived.")
    return document


def admit_lifecycle_operation(grant: Mapping[str, object], *, admitted_at_utc: str) -> dict[str, object]:
    checked = validate_admission_grant(grant)
    admitted = _utc_dt(admitted_at_utc, "admitted_at_utc")
    if admitted < _utc_dt(checked["issued_at_utc"], "grant.issued_at_utc"):
        raise LifecycleOperationAdmissionError("admitted_at_utc must not precede grant issuance.")
    if admitted > _utc_dt(checked["expires_at_utc"], "grant.expires_at_utc"):
        raise LifecycleOperationAdmissionError("Admission grant expired before operation admission.")
    base = {
        "schema_version": 1,
        "receipt_scope": RECEIPT_SCOPE,
        "capability": ADMISSION_CAPABILITY,
        "grant_sha256": checked["grant_sha256"],
        "eligibility_sha256": checked["eligibility_sha256"],
        "snapshot_sha256": checked["snapshot_sha256"],
        "operation": checked["operation"],
        "target_reference": checked["target_reference"],
        "current_state_reference": checked["current_state_reference"],
        "recommended_prior_installation_reference": checked["recommended_prior_installation_reference"],
        "current_state_status": checked["current_state_status"],
        "current_state_file_sha256": checked["current_state_file_sha256"],
        "eligibility_reason": checked["eligibility_reason"],
        "admitted_at_utc": _utc(admitted_at_utc, "admitted_at_utc"),
        "admitted": True,
        "lifecycle_handoff_created": False,
        "package_engine_session_created": False,
        "copy_performed": False,
        "process_launched": False,
        "elevation_requested": False,
        "state_published": False,
        "product_or_game_directory_mutated": False,
        "runtime_executed": False,
        "save_mutated": False,
        "signing_performed": False,
        "network_publication_performed": False,
        "catalog_mutated": False,
        "evidence_promoted": False,
        "statement": RECEIPT_STATEMENT,
        "authority": _authority(),
    }
    return {**base, "receipt_sha256": sha256(base)}


def validate_admission_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    document = dict(receipt)
    if document.get("schema_version") != 1 or document.get("receipt_scope") != RECEIPT_SCOPE:
        raise LifecycleOperationAdmissionError("Admission receipt schema or scope is invalid.")
    if document.get("capability") != ADMISSION_CAPABILITY or document.get("statement") != RECEIPT_STATEMENT:
        raise LifecycleOperationAdmissionError("Admission receipt capability or statement is invalid.")
    if document.get("admitted") is not True:
        raise LifecycleOperationAdmissionError("Admission receipt must record admitted=true.")
    for field in (
        "lifecycle_handoff_created", "package_engine_session_created", "copy_performed", "process_launched",
        "elevation_requested", "state_published", "product_or_game_directory_mutated", "runtime_executed",
        "save_mutated", "signing_performed", "network_publication_performed", "catalog_mutated", "evidence_promoted",
    ):
        if document.get(field) is not False:
            raise LifecycleOperationAdmissionError(f"Admission receipt forbidden side-effect flag {field} must be false.")
    _validate_authority(document.get("authority"), "receipt.authority")
    _operation(document.get("operation"), "receipt.operation")
    _reference(document.get("target_reference"), "receipt.target_reference")
    _hash(document.get("grant_sha256"), "receipt.grant_sha256")
    _hash(document.get("eligibility_sha256"), "receipt.eligibility_sha256")
    _hash(document.get("snapshot_sha256"), "receipt.snapshot_sha256")
    if document.get("current_state_reference") is not None:
        _reference(document.get("current_state_reference"), "receipt.current_state_reference")
    if document.get("recommended_prior_installation_reference") is not None:
        _reference(
            document.get("recommended_prior_installation_reference"),
            "receipt.recommended_prior_installation_reference",
        )
    if document.get("current_state_file_sha256") is not None:
        _hash(document.get("current_state_file_sha256"), "receipt.current_state_file_sha256")
    declared = _hash(document.get("receipt_sha256"), "receipt.receipt_sha256")
    unsigned = {key: value for key, value in document.items() if key != "receipt_sha256"}
    if sha256(unsigned) != declared:
        raise LifecycleOperationAdmissionError("Admission receipt fingerprint does not match its content.")
    return document


def canonical_grant_bytes(grant: Mapping[str, object]) -> bytes:
    return canonical_json(validate_admission_grant(grant))


def canonical_receipt_bytes(receipt: Mapping[str, object]) -> bytes:
    return canonical_json(validate_admission_receipt(receipt))
