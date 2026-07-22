#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Authenticated one-shot publication of SDK-owned installation state."""
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
    INSTALLER_ROOT / "Bootstrapper" / "Security" / "Source",
    INSTALLER_ROOT / "SuiteWizard" / "ViewModel" / "Source",
):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from execution_security import (  # noqa: E402
    ExecutionSecurityError,
    canonical_json,
    claim_once,
    seal_authenticated_record,
    utc_datetime,
    verify_sealed_record,
)
from lifecycle_execution_coordinator import (  # noqa: E402
    LifecycleCoordinatorError,
    validate_lifecycle_result,
)
from package_engine import PackageEngineError, validate_engine_session  # noqa: E402
from wizard_view_model import AUTHORITY_FIELDS  # noqa: E402

PUBLICATION_CAPABILITY = "package-engine.publish-installation-state"
GRANT_SCOPE = "package-installation-state-publication-grant"
RECORD_SCOPE = "package-installation-state-record"
RECEIPT_SCOPE = "package-installation-state-publication-receipt"
MAX_GRANT_SECONDS = 900
REFERENCE_RE = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GRANT_STATEMENT = (
    "This authenticated grant authorizes one one-shot SDK-owned installation-state publication "
    "for one exact completed lifecycle result and expected prior state digest."
)
RECORD_STATEMENT = (
    "This authenticated record describes SDK-owned installer state and grants no product, game, "
    "runtime, save, signing, network, catalog, or evidence authority."
)
RECEIPT_STATEMENT = (
    "This authenticated receipt records one atomic installation-state publication after one-shot "
    "grant consumption and exact previous-state comparison."
)


class InstallationStatePublisherError(RuntimeError):
    pass


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise InstallationStatePublisherError(f"{label} must be an object.")
    return value


def _text(value: object, label: str, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise InstallationStatePublisherError(
            f"{label} must be non-empty trimmed text of at most {maximum} characters."
        )
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
    return None if value is None else _hash(value, label)


def _utc(value: object, label: str) -> str:
    try:
        utc_datetime(value, label)
    except ExecutionSecurityError as exc:
        raise InstallationStatePublisherError(str(exc)) from exc
    return str(value)


def _authority() -> dict[str, bool]:
    return {field: False for field in AUTHORITY_FIELDS}


def _state_status(operation: str) -> str:
    if operation == "uninstall":
        return "removed"
    if operation == "rollback":
        return "rolled-back"
    return "active"


def _validate_lifecycle_publication_policy(lifecycle: Mapping[str, object]) -> None:
    if lifecycle.get("status") != "completed" or lifecycle.get("lifecycle_completed") is not True:
        raise InstallationStatePublisherError(
            "Installation state can only be published from a completed lifecycle result."
        )
    elevation_confirmed = lifecycle.get("elevation_request_confirmed")
    elevated_observed = lifecycle.get("elevated_completion_observed")
    elevated_observation_sha = lifecycle.get("elevated_completion_observation_sha256")
    if elevation_confirmed is True:
        if elevated_observed is not True or elevated_observation_sha is None:
            raise InstallationStatePublisherError(
                "Elevated lifecycle publication requires an authenticated elevated completion observation."
            )
        _hash(elevated_observation_sha, "lifecycle.elevated_completion_observation_sha256")
    elif elevation_confirmed is False:
        if elevated_observed is not False or elevated_observation_sha is not None:
            raise InstallationStatePublisherError(
                "Non-elevated lifecycle publication must not include elevated completion evidence."
            )
    else:
        raise InstallationStatePublisherError("Lifecycle elevation_request_confirmed flag is invalid.")


def _reject_symlink_components(path: Path, label: str) -> None:
    current = path
    while True:
        if current.is_symlink():
            raise InstallationStatePublisherError(f"{label} contains a symbolic link: {current}")
        if current.parent == current:
            break
        current = current.parent


def _file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise InstallationStatePublisherError("Existing state path is not a regular non-symlink file.")
    digest = hashlib.sha256()
    descriptor = os.open(path, os.O_RDONLY | (os.O_NOFOLLOW if hasattr(os, "O_NOFOLLOW") else 0))
    try:
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        os.close(descriptor)
    return digest.hexdigest()


def build_publication_grant(
    session: Mapping[str, object],
    lifecycle_result: Mapping[str, object],
    *,
    authority_key_path: Path,
    state_reference: str,
    expected_previous_state_sha256: str | None,
    issuer: str,
    issued_at_utc: str,
    expires_at_utc: str,
    nonce: str,
) -> dict[str, object]:
    try:
        checked_session = validate_engine_session(session, authority_key_path=authority_key_path)
        checked_lifecycle = validate_lifecycle_result(
            lifecycle_result, authority_key_path=authority_key_path
        )
    except (PackageEngineError, LifecycleCoordinatorError) as exc:
        raise InstallationStatePublisherError(f"Publication intake failed: {exc}") from exc
    capabilities = checked_session.get("authorized_capabilities")
    if not isinstance(capabilities, list) or PUBLICATION_CAPABILITY not in capabilities:
        raise InstallationStatePublisherError(
            "Authenticated session does not grant package-engine.publish-installation-state."
        )
    _validate_lifecycle_publication_policy(checked_lifecycle)
    if (
        checked_lifecycle.get("session_sha256") != checked_session.get("session_sha256")
        or checked_lifecycle.get("operation") != checked_session.get("operation")
    ):
        raise InstallationStatePublisherError(
            "Lifecycle result is not bound to the exact authenticated session and operation."
        )
    issued = utc_datetime(issued_at_utc, "issued_at_utc")
    expires = utc_datetime(expires_at_utc, "expires_at_utc")
    completed = utc_datetime(checked_lifecycle["completed_at_utc"], "lifecycle.completed_at_utc")
    if issued < completed or expires <= issued or expires - issued > dt.timedelta(seconds=MAX_GRANT_SECONDS):
        raise InstallationStatePublisherError(
            "Publication grant must follow lifecycle completion and expire within 15 minutes."
        )
    base = {
        "schema_version": 2,
        "grant_scope": GRANT_SCOPE,
        "capability": PUBLICATION_CAPABILITY,
        "session_sha256": checked_session["session_sha256"],
        "lifecycle_result_sha256": checked_lifecycle["result_sha256"],
        "operation": checked_lifecycle["operation"],
        "state_reference": _reference(state_reference, "state_reference"),
        "expected_previous_state_sha256": _optional_hash(
            expected_previous_state_sha256, "expected_previous_state_sha256"
        ),
        "issuer": _text(issuer, "issuer", 160),
        "issued_at_utc": _utc(issued_at_utc, "issued_at_utc"),
        "expires_at_utc": _utc(expires_at_utc, "expires_at_utc"),
        "nonce": _reference(nonce, "nonce"),
        "session": checked_session,
        "lifecycle_result": checked_lifecycle,
        "statement": GRANT_STATEMENT,
        "authority": _authority(),
    }
    try:
        return seal_authenticated_record(
            base, authority_key_path=authority_key_path, digest_field="grant_sha256"
        )
    except ExecutionSecurityError as exc:
        raise InstallationStatePublisherError(f"Publication grant authentication failed: {exc}") from exc


def validate_publication_grant(
    grant: Mapping[str, object], *, authority_key_path: Path
) -> dict[str, object]:
    document = dict(grant)
    if (
        document.get("schema_version") != 2
        or document.get("grant_scope") != GRANT_SCOPE
        or document.get("capability") != PUBLICATION_CAPABILITY
        or document.get("statement") != GRANT_STATEMENT
        or document.get("authority") != _authority()
    ):
        raise InstallationStatePublisherError("Publication grant contract is invalid.")
    try:
        verify_sealed_record(
            document, authority_key_path=authority_key_path, digest_field="grant_sha256"
        )
    except ExecutionSecurityError as exc:
        raise InstallationStatePublisherError(f"Publication grant authentication failed: {exc}") from exc
    expected = build_publication_grant(
        _object(document.get("session"), "grant.session"),
        _object(document.get("lifecycle_result"), "grant.lifecycle_result"),
        authority_key_path=authority_key_path,
        state_reference=_reference(document.get("state_reference"), "state_reference"),
        expected_previous_state_sha256=_optional_hash(
            document.get("expected_previous_state_sha256"), "expected_previous_state_sha256"
        ),
        issuer=_text(document.get("issuer"), "issuer", 160),
        issued_at_utc=_utc(document.get("issued_at_utc"), "issued_at_utc"),
        expires_at_utc=_utc(document.get("expires_at_utc"), "expires_at_utc"),
        nonce=_reference(document.get("nonce"), "nonce"),
    )
    if document != expected:
        raise InstallationStatePublisherError(
            "Publication grant is stale, altered, or not canonically derived."
        )
    return document


def build_state_record(
    grant: Mapping[str, object], *, authority_key_path: Path, published_at_utc: str
) -> dict[str, object]:
    checked = validate_publication_grant(grant, authority_key_path=authority_key_path)
    published = utc_datetime(published_at_utc, "published_at_utc")
    if (
        published < utc_datetime(checked["issued_at_utc"], "grant.issued_at_utc")
        or published > utc_datetime(checked["expires_at_utc"], "grant.expires_at_utc")
    ):
        raise InstallationStatePublisherError("Publication grant is not valid at publication time.")
    session = _object(checked["session"], "grant.session")
    handoff = _object(session.get("handoff"), "session.handoff")
    lifecycle = _object(checked["lifecycle_result"], "grant.lifecycle_result")
    base = {
        "schema_version": 2,
        "record_scope": RECORD_SCOPE,
        "state_reference": checked["state_reference"],
        "state_status": _state_status(str(checked["operation"])),
        "operation": checked["operation"],
        "target_reference": handoff["target_reference"],
        "prior_installation_reference": handoff.get("prior_installation_reference"),
        "session_sha256": checked["session_sha256"],
        "handoff_sha256": handoff["handoff_sha256"],
        "receipt_sha256": handoff["receipt_sha256"],
        "plan_sha256": handoff["plan_sha256"],
        "lifecycle_result_sha256": lifecycle["result_sha256"],
        "elevation_request_confirmed": lifecycle.get("elevation_request_confirmed"),
        "elevated_completion_observed": lifecycle.get("elevated_completion_observed"),
        "elevation_result_sha256": lifecycle.get("elevation_result_sha256"),
        "elevated_completion_observation_sha256": lifecycle.get("elevated_completion_observation_sha256"),
        "operation_plan_sha256": session["operation_plan_sha256"],
        "published_at_utc": _utc(published_at_utc, "published_at_utc"),
        "product_or_game_directory_mutated": False,
        "runtime_executed": False,
        "save_mutated": False,
        "signing_performed": False,
        "publication_performed": False,
        "catalog_mutated": False,
        "evidence_promoted": False,
        "statement": RECORD_STATEMENT,
        "publication_grant": checked,
    }
    try:
        return seal_authenticated_record(
            base, authority_key_path=authority_key_path, digest_field="state_record_sha256"
        )
    except ExecutionSecurityError as exc:
        raise InstallationStatePublisherError(f"State record authentication failed: {exc}") from exc


def validate_state_record(
    record: Mapping[str, object], *, authority_key_path: Path
) -> dict[str, object]:
    document = dict(record)
    if (
        document.get("schema_version") != 2
        or document.get("record_scope") != RECORD_SCOPE
        or document.get("statement") != RECORD_STATEMENT
    ):
        raise InstallationStatePublisherError("State record contract is invalid.")
    for field in (
        "product_or_game_directory_mutated",
        "runtime_executed",
        "save_mutated",
        "signing_performed",
        "publication_performed",
        "catalog_mutated",
        "evidence_promoted",
    ):
        if document.get(field) is not False:
            raise InstallationStatePublisherError(f"State record flag {field} must remain false.")
    try:
        verify_sealed_record(
            document, authority_key_path=authority_key_path, digest_field="state_record_sha256"
        )
    except ExecutionSecurityError as exc:
        raise InstallationStatePublisherError(f"State record authentication failed: {exc}") from exc
    checked_grant = validate_publication_grant(
        _object(document.get("publication_grant"), "record.publication_grant"),
        authority_key_path=authority_key_path,
    )
    if (
        document.get("session_sha256") != checked_grant["session_sha256"]
        or document.get("lifecycle_result_sha256") != checked_grant["lifecycle_result_sha256"]
        or document.get("state_reference") != checked_grant["state_reference"]
    ):
        raise InstallationStatePublisherError("State record is not bound to its authenticated grant.")
    lifecycle = _object(checked_grant.get("lifecycle_result"), "record.lifecycle_result")
    for field in (
        "elevation_request_confirmed",
        "elevated_completion_observed",
        "elevation_result_sha256",
        "elevated_completion_observation_sha256",
    ):
        if document.get(field) != lifecycle.get(field):
            raise InstallationStatePublisherError("State record elevated lifecycle fields do not match the grant.")
    return document


def _write_atomic(target: Path, payload: bytes, grant_sha: str, *, replace: bool) -> None:
    temporary = target.parent / f".{target.name}.{grant_sha}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | (os.O_NOFOLLOW if hasattr(os, "O_NOFOLLOW") else 0)
    descriptor = os.open(temporary, flags, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise InstallationStatePublisherError("State publication made no forward progress.")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        if replace:
            os.replace(temporary, target)
        else:
            os.link(temporary, target)
            temporary.unlink()
        directory = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except Exception:
        if temporary.exists() and not temporary.is_symlink():
            temporary.unlink()
        raise


def publish_state_record(
    grant: Mapping[str, object],
    state_root: Path,
    *,
    authority_key_path: Path,
    claim_root: Path,
    published_at_utc: str,
) -> dict[str, object]:
    checked = validate_publication_grant(grant, authority_key_path=authority_key_path)
    root = Path(state_root)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise InstallationStatePublisherError(
            "State root must be an absolute existing non-symlink directory."
        )
    _reject_symlink_components(root, "State root")
    target = root / f"{checked['state_reference']}.json"
    # This read-only preflight gives deterministic replay diagnostics without
    # replacing the atomic O_EXCL claim that remains the enforcement point.
    claim_target = (
        Path(claim_root)
        / "claim.installation-state-publication-grant"
        / f"{checked['grant_sha256']}.claim.json"
    )
    if claim_target.exists() or claim_target.is_symlink():
        raise InstallationStatePublisherError(
            "Publication grant consumption failed: Artifact has already been consumed: "
            + str(checked["grant_sha256"])
        )
    previous = _file_sha256(target)
    expected = checked["expected_previous_state_sha256"]
    if previous != expected:
        raise InstallationStatePublisherError(
            "Existing state hash does not match expected_previous_state_sha256."
        )
    try:
        claim = claim_once(
            claim_root,
            authority_key_path=authority_key_path,
            claim_kind="claim.installation-state-publication-grant",
            artifact_sha256=str(checked["grant_sha256"]),
            nonce=str(checked["nonce"]),
            claimed_at_utc=published_at_utc,
        )
    except ExecutionSecurityError as exc:
        raise InstallationStatePublisherError(f"Publication grant consumption failed: {exc}") from exc
    record = build_state_record(
        checked, authority_key_path=authority_key_path, published_at_utc=published_at_utc
    )
    payload = canonical_json(record)
    _write_atomic(target, payload, str(checked["grant_sha256"]), replace=previous is not None)
    written_hash = _file_sha256(target)
    if written_hash != hashlib.sha256(payload).hexdigest():
        raise InstallationStatePublisherError("Published state file does not match canonical record bytes.")
    base = {
        "schema_version": 2,
        "receipt_scope": RECEIPT_SCOPE,
        "grant_sha256": checked["grant_sha256"],
        "claim_sha256": claim["claim_sha256"],
        "session_sha256": checked["session_sha256"],
        "lifecycle_result_sha256": checked["lifecycle_result_sha256"],
        "state_reference": checked["state_reference"],
        "state_file_name": target.name,
        "state_file_sha256": written_hash,
        "previous_state_sha256": previous,
        "state_record_sha256": record["state_record_sha256"],
        "published_at_utc": _utc(published_at_utc, "published_at_utc"),
        "state_file_written": True,
        "atomic_replace_used": previous is not None,
        "product_or_game_directory_mutated": False,
        "runtime_executed": False,
        "save_mutated": False,
        "signing_performed": False,
        "network_publication_performed": False,
        "catalog_mutated": False,
        "evidence_promoted": False,
        "statement": RECEIPT_STATEMENT,
        "state_record": record,
        "publication_grant": checked,
    }
    try:
        return seal_authenticated_record(
            base, authority_key_path=authority_key_path, digest_field="receipt_sha256"
        )
    except ExecutionSecurityError as exc:
        raise InstallationStatePublisherError(f"Publication receipt authentication failed: {exc}") from exc


def validate_publication_receipt(
    receipt: Mapping[str, object], *, authority_key_path: Path
) -> dict[str, object]:
    document = dict(receipt)
    if (
        document.get("schema_version") != 2
        or document.get("receipt_scope") != RECEIPT_SCOPE
        or document.get("statement") != RECEIPT_STATEMENT
        or document.get("state_file_written") is not True
    ):
        raise InstallationStatePublisherError("Publication receipt contract is invalid.")
    for field in (
        "product_or_game_directory_mutated",
        "runtime_executed",
        "save_mutated",
        "signing_performed",
        "network_publication_performed",
        "catalog_mutated",
        "evidence_promoted",
    ):
        if document.get(field) is not False:
            raise InstallationStatePublisherError(f"Publication receipt flag {field} must remain false.")
    try:
        verify_sealed_record(
            document, authority_key_path=authority_key_path, digest_field="receipt_sha256"
        )
    except ExecutionSecurityError as exc:
        raise InstallationStatePublisherError(f"Publication receipt authentication failed: {exc}") from exc
    grant = validate_publication_grant(
        _object(document.get("publication_grant"), "receipt.publication_grant"),
        authority_key_path=authority_key_path,
    )
    record = validate_state_record(
        _object(document.get("state_record"), "receipt.state_record"),
        authority_key_path=authority_key_path,
    )
    if (
        document.get("grant_sha256") != grant["grant_sha256"]
        or document.get("state_record_sha256") != record["state_record_sha256"]
    ):
        raise InstallationStatePublisherError("Publication receipt is not bound to grant and record.")
    return document


__all__ = [
    "InstallationStatePublisherError",
    "PUBLICATION_CAPABILITY",
    "build_publication_grant",
    "build_state_record",
    "publish_state_record",
    "validate_publication_grant",
    "validate_publication_receipt",
    "validate_state_record",
]
