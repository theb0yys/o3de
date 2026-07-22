#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Capability-gated SDK-owned installation-state publication."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Mapping

INSTALLER_ROOT = Path(__file__).resolve().parents[3]
for root in (
    INSTALLER_ROOT / "Bootstrapper" / "PackageEngine" / "Source",
    INSTALLER_ROOT / "Bootstrapper" / "LifecycleCoordinator" / "Source",
    INSTALLER_ROOT / "SuiteWizard" / "ViewModel" / "Source",
):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from lifecycle_execution_coordinator import (  # noqa: E402
    LifecycleCoordinatorError,
    validate_lifecycle_result,
)
from package_engine import PackageEngineError, validate_engine_session  # noqa: E402
from wizard_view_model import AUTHORITY_FIELDS, canonical_json, sha256  # noqa: E402

PUBLICATION_CAPABILITY = "package-engine.publish-installation-state"
GRANT_SCOPE = "package-installation-state-publication-grant"
RECORD_SCOPE = "package-installation-state-record"
RECEIPT_SCOPE = "package-installation-state-publication-receipt"
MAX_GRANT_SECONDS = 900
REFERENCE_RE = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GRANT_STATEMENT = (
    "This grant authorizes one atomic publication of SDK-owned installation state for one exact "
    "completed package lifecycle result. It grants no product or game directory mutation, runtime "
    "execution, process launch, elevation, signing, network publication, catalog mutation, save "
    "mutation, or evidence promotion authority."
)
RECORD_STATEMENT = (
    "This record describes SDK-owned installer state after a completed reviewed lifecycle result. "
    "It is not proof of product or game directory mutation and grants no later authority."
)
RECEIPT_STATEMENT = (
    "This receipt records atomic publication of one SDK-owned installation-state record. It does "
    "not execute runtime code, mutate product or game directories, sign artifacts, publish releases, "
    "mutate catalogs, mutate saves, or promote evidence."
)


class InstallationStatePublisherError(RuntimeError):
    pass


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise InstallationStatePublisherError(f"{label} must be an object.")
    return value


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise InstallationStatePublisherError(f"{label} must be an array.")
    return value


def _text(value: object, label: str, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise InstallationStatePublisherError(f"{label} must be a non-empty trimmed string of at most {maximum} characters.")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise InstallationStatePublisherError(f"{label} contains a forbidden control character.")
    return value


def _reference(value: object, label: str) -> str:
    result = _text(value, label, 128)
    if REFERENCE_RE.fullmatch(result) is None:
        raise InstallationStatePublisherError(f"{label} must be a stable namespaced logical ID.")
    return result


def _hash(value: object, label: str) -> str:
    result = _text(value, label, 64)
    if SHA256_RE.fullmatch(result) is None:
        raise InstallationStatePublisherError(f"{label} must be a lowercase SHA-256 value.")
    return result


def _optional_hash(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _hash(value, label)


def _utc(value: object, label: str) -> str:
    result = _text(value, label, 64)
    if not result.endswith("Z") or "T" not in result:
        raise InstallationStatePublisherError(f"{label} must be an ISO-8601 UTC timestamp ending in Z.")
    try:
        parsed = dt.datetime.fromisoformat(result[:-1] + "+00:00")
    except ValueError as exc:
        raise InstallationStatePublisherError(f"{label} is not a valid ISO-8601 timestamp.") from exc
    if parsed.utcoffset() != dt.timedelta(0):
        raise InstallationStatePublisherError(f"{label} must use UTC.")
    return result


def _utc_dt(value: object, label: str) -> dt.datetime:
    return dt.datetime.fromisoformat(_utc(value, label)[:-1] + "+00:00")


def _authority() -> dict[str, bool]:
    return {field: False for field in AUTHORITY_FIELDS}


def _validate_authority(value: object, label: str) -> None:
    authority = _object(value, label)
    if authority != _authority():
        raise InstallationStatePublisherError(f"{label} must contain the exact all-false authority record.")


def _checked_session(session: Mapping[str, object]) -> dict[str, object]:
    try:
        return validate_engine_session(session)
    except PackageEngineError as exc:
        raise InstallationStatePublisherError(f"Package-engine session verification failed: {exc}") from exc


def _checked_lifecycle(result: Mapping[str, object]) -> dict[str, object]:
    try:
        checked = validate_lifecycle_result(result)
    except LifecycleCoordinatorError as exc:
        raise InstallationStatePublisherError(f"Lifecycle result verification failed: {exc}") from exc
    if checked.get("status") != "completed" or checked.get("lifecycle_completed") is not True:
        raise InstallationStatePublisherError("Installation state can only be published from a completed lifecycle result.")
    if checked.get("elevation_request_confirmed") is not False:
        raise InstallationStatePublisherError("Elevation-pending lifecycle results require a later completion receipt before state publication.")
    return checked


def _session_handoff(session: Mapping[str, object]) -> dict[str, object]:
    return _object(session.get("handoff"), "session.handoff")


def _state_status(operation: str) -> str:
    if operation == "uninstall":
        return "removed"
    if operation == "rollback":
        return "rolled-back"
    return "active"


def _state_file_name(state_reference: str) -> str:
    return f"{state_reference}.json"


def _reject_symlink_components(path: Path, label: str) -> None:
    current = path
    while True:
        if current.is_symlink():
            raise InstallationStatePublisherError(f"{label} contains a symbolic link: {current}")
        if current.parent == current:
            break
        current = current.parent


def _read_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise InstallationStatePublisherError("Existing state path is not a regular non-symlink file.")
    digest = hashlib.sha256()
    flags = os.O_RDONLY | (os.O_NOFOLLOW if hasattr(os, "O_NOFOLLOW") else 0)
    descriptor = os.open(path, flags)
    try:
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        os.close(descriptor)
    return digest.hexdigest()


def _write_atomic(target: Path, content: bytes, grant_sha256: str) -> bool:
    temp = target.parent / f".{target.name}.{grant_sha256}.tmp"
    if temp.exists() or temp.is_symlink():
        raise InstallationStatePublisherError("Deterministic temporary state file already exists.")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | (os.O_NOFOLLOW if hasattr(os, "O_NOFOLLOW") else 0)
    descriptor = os.open(temp, flags, 0o600)
    try:
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise InstallationStatePublisherError("State publication made no forward progress.")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    replaced = target.exists()
    try:
        os.replace(temp, target)
        directory = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except Exception:
        if temp.exists() and not temp.is_symlink():
            temp.unlink()
        raise
    return replaced


def build_publication_grant(
    session: Mapping[str, object], lifecycle_result: Mapping[str, object], *, state_reference: str,
    expected_previous_state_sha256: str | None, issuer: str, issued_at_utc: str, expires_at_utc: str, nonce: str,
) -> dict[str, object]:
    checked_session = _checked_session(session)
    checked_lifecycle = _checked_lifecycle(lifecycle_result)
    if checked_lifecycle["session_sha256"] != checked_session["session_sha256"]:
        raise InstallationStatePublisherError("Lifecycle result is not bound to the exact package-engine session.")
    if checked_lifecycle["operation"] != checked_session["operation"]:
        raise InstallationStatePublisherError("Lifecycle result operation does not match the package-engine session.")
    issued = _utc_dt(issued_at_utc, "issued_at_utc")
    expires = _utc_dt(expires_at_utc, "expires_at_utc")
    completed = _utc_dt(checked_lifecycle["completed_at_utc"], "lifecycle.completed_at_utc")
    if issued < completed:
        raise InstallationStatePublisherError("issued_at_utc must not precede lifecycle completion.")
    if expires <= issued or expires - issued > dt.timedelta(seconds=MAX_GRANT_SECONDS):
        raise InstallationStatePublisherError("Publication grant expiry must be after issuance and within 15 minutes.")
    base = {
        "schema_version": 1,
        "grant_scope": GRANT_SCOPE,
        "capability": PUBLICATION_CAPABILITY,
        "session_sha256": checked_session["session_sha256"],
        "lifecycle_result_sha256": checked_lifecycle["result_sha256"],
        "operation": checked_lifecycle["operation"],
        "state_reference": _reference(state_reference, "state_reference"),
        "expected_previous_state_sha256": _optional_hash(expected_previous_state_sha256, "expected_previous_state_sha256"),
        "issuer": _text(issuer, "issuer", 160),
        "issued_at_utc": _utc(issued_at_utc, "issued_at_utc"),
        "expires_at_utc": _utc(expires_at_utc, "expires_at_utc"),
        "nonce": _reference(nonce, "nonce"),
        "session": checked_session,
        "lifecycle_result": checked_lifecycle,
        "statement": GRANT_STATEMENT,
        "authority": _authority(),
    }
    return {**base, "grant_sha256": sha256(base)}


def validate_publication_grant(grant: Mapping[str, object]) -> dict[str, object]:
    document = dict(grant)
    if document.get("schema_version") != 1 or document.get("grant_scope") != GRANT_SCOPE:
        raise InstallationStatePublisherError("Publication grant schema or scope is invalid.")
    if document.get("capability") != PUBLICATION_CAPABILITY or document.get("statement") != GRANT_STATEMENT:
        raise InstallationStatePublisherError("Publication grant capability or statement is invalid.")
    _validate_authority(document.get("authority"), "grant.authority")
    declared = _hash(document.get("grant_sha256"), "grant.grant_sha256")
    unsigned = {key: value for key, value in document.items() if key != "grant_sha256"}
    if sha256(unsigned) != declared:
        raise InstallationStatePublisherError("Publication grant fingerprint does not match its content.")
    expected = build_publication_grant(
        _object(document.get("session"), "grant.session"),
        _object(document.get("lifecycle_result"), "grant.lifecycle_result"),
        state_reference=_reference(document.get("state_reference"), "grant.state_reference"),
        expected_previous_state_sha256=_optional_hash(document.get("expected_previous_state_sha256"), "grant.expected_previous_state_sha256"),
        issuer=_text(document.get("issuer"), "grant.issuer", 160),
        issued_at_utc=_utc(document.get("issued_at_utc"), "grant.issued_at_utc"),
        expires_at_utc=_utc(document.get("expires_at_utc"), "grant.expires_at_utc"),
        nonce=_reference(document.get("nonce"), "grant.nonce"),
    )
    if document != expected:
        raise InstallationStatePublisherError("Publication grant is stale, altered, or not canonically derived.")
    return document


def build_state_record(grant: Mapping[str, object], *, published_at_utc: str) -> dict[str, object]:
    checked = validate_publication_grant(grant)
    published = _utc_dt(published_at_utc, "published_at_utc")
    if published < _utc_dt(checked["issued_at_utc"], "grant.issued_at_utc"):
        raise InstallationStatePublisherError("published_at_utc must not precede grant issuance.")
    if published > _utc_dt(checked["expires_at_utc"], "grant.expires_at_utc"):
        raise InstallationStatePublisherError("Publication grant expired before state publication.")
    session = _object(checked["session"], "grant.session")
    handoff = _session_handoff(session)
    lifecycle = _object(checked["lifecycle_result"], "grant.lifecycle_result")
    operation = _text(checked["operation"], "grant.operation", 32)
    base = {
        "schema_version": 1,
        "record_scope": RECORD_SCOPE,
        "state_reference": checked["state_reference"],
        "state_status": _state_status(operation),
        "operation": operation,
        "target_reference": _reference(handoff.get("target_reference"), "session.handoff.target_reference"),
        "prior_installation_reference": handoff.get("prior_installation_reference"),
        "session_sha256": checked["session_sha256"],
        "handoff_sha256": handoff["handoff_sha256"],
        "receipt_sha256": handoff["receipt_sha256"],
        "plan_sha256": handoff["plan_sha256"],
        "lifecycle_result_sha256": checked["lifecycle_result_sha256"],
        "copy_receipt_sha256": lifecycle.get("copy_receipt_sha256"),
        "launch_result_sha256": lifecycle.get("launch_result_sha256"),
        "published_at_utc": _utc(published_at_utc, "published_at_utc"),
        "package_order": [_reference(item, "package_order[]") for item in _array(handoff.get("package_order"), "session.handoff.package_order")],
        "summary": _object(handoff.get("summary"), "session.handoff.summary"),
        "product_or_game_directory_mutated": False,
        "runtime_executed": False,
        "save_mutated": False,
        "signing_performed": False,
        "publication_performed": False,
        "catalog_mutated": False,
        "evidence_promoted": False,
        "statement": RECORD_STATEMENT,
        "authority": _authority(),
    }
    return {**base, "state_record_sha256": sha256(base)}


def validate_state_record(record: Mapping[str, object]) -> dict[str, object]:
    document = dict(record)
    if document.get("schema_version") != 1 or document.get("record_scope") != RECORD_SCOPE:
        raise InstallationStatePublisherError("State record schema or scope is invalid.")
    if document.get("statement") != RECORD_STATEMENT:
        raise InstallationStatePublisherError("State record statement was altered.")
    _reference(document.get("state_reference"), "record.state_reference")
    for field in (
        "product_or_game_directory_mutated", "runtime_executed", "save_mutated", "signing_performed",
        "publication_performed", "catalog_mutated", "evidence_promoted",
    ):
        if document.get(field) is not False:
            raise InstallationStatePublisherError(f"State record forbidden side-effect flag {field} must be false.")
    _validate_authority(document.get("authority"), "record.authority")
    declared = _hash(document.get("state_record_sha256"), "record.state_record_sha256")
    unsigned = {key: value for key, value in document.items() if key != "state_record_sha256"}
    if sha256(unsigned) != declared:
        raise InstallationStatePublisherError("State record fingerprint does not match its content.")
    return document


def publish_state_record(grant: Mapping[str, object], state_root: Path, *, published_at_utc: str) -> dict[str, object]:
    checked = validate_publication_grant(grant)
    root = Path(state_root)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise InstallationStatePublisherError("State root must be an absolute existing non-symlink directory.")
    _reject_symlink_components(root, "State root")
    record = build_state_record(checked, published_at_utc=published_at_utc)
    target = root / _state_file_name(str(checked["state_reference"]))
    previous = _read_hash(target)
    if previous != checked["expected_previous_state_sha256"]:
        raise InstallationStatePublisherError("Existing state hash does not match the publication grant expectation.")
    content = canonical_json(record)
    replaced = _write_atomic(target, content, str(checked["grant_sha256"]))
    after = _read_hash(target)
    if after != hashlib.sha256(content).hexdigest():
        raise InstallationStatePublisherError("Published state file hash does not match the canonical record bytes.")
    base = {
        "schema_version": 1,
        "receipt_scope": RECEIPT_SCOPE,
        "grant_sha256": checked["grant_sha256"],
        "session_sha256": checked["session_sha256"],
        "lifecycle_result_sha256": checked["lifecycle_result_sha256"],
        "state_reference": checked["state_reference"],
        "state_file_name": target.name,
        "previous_state_sha256": previous,
        "state_record_sha256": record["state_record_sha256"],
        "state_file_sha256": after,
        "published_at_utc": _utc(published_at_utc, "published_at_utc"),
        "state_file_written": True,
        "atomic_replace_used": replaced,
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


def validate_publication_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    document = dict(receipt)
    if document.get("schema_version") != 1 or document.get("receipt_scope") != RECEIPT_SCOPE:
        raise InstallationStatePublisherError("Publication receipt schema or scope is invalid.")
    if document.get("statement") != RECEIPT_STATEMENT:
        raise InstallationStatePublisherError("Publication receipt statement was altered.")
    if document.get("state_file_written") is not True:
        raise InstallationStatePublisherError("Publication receipt must record a written state file.")
    for field in (
        "product_or_game_directory_mutated", "runtime_executed", "save_mutated", "signing_performed",
        "network_publication_performed", "catalog_mutated", "evidence_promoted",
    ):
        if document.get(field) is not False:
            raise InstallationStatePublisherError(f"Publication receipt forbidden side-effect flag {field} must be false.")
    _validate_authority(document.get("authority"), "receipt.authority")
    declared = _hash(document.get("receipt_sha256"), "receipt.receipt_sha256")
    unsigned = {key: value for key, value in document.items() if key != "receipt_sha256"}
    if sha256(unsigned) != declared:
        raise InstallationStatePublisherError("Publication receipt fingerprint does not match its content.")
    return document


def canonical_grant_bytes(grant: Mapping[str, object]) -> bytes:
    return canonical_json(validate_publication_grant(grant))


def canonical_record_bytes(record: Mapping[str, object]) -> bytes:
    return canonical_json(validate_state_record(record))


def canonical_receipt_bytes(receipt: Mapping[str, object]) -> bytes:
    return canonical_json(validate_publication_receipt(receipt))
