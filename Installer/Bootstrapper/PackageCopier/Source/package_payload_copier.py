#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Capability-gated, hash-verifying package payload staging copier."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Mapping

INSTALLER_ROOT = Path(__file__).resolve().parents[3]
ENGINE_SOURCE = INSTALLER_ROOT / "Bootstrapper" / "PackageEngine" / "Source"
VIEW_MODEL_SOURCE = INSTALLER_ROOT / "SuiteWizard" / "ViewModel" / "Source"
for root in (ENGINE_SOURCE, VIEW_MODEL_SOURCE):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from package_engine import PackageEngineError, validate_engine_session  # noqa: E402
from wizard_view_model import AUTHORITY_FIELDS, canonical_json, sha256  # noqa: E402

COPY_CAPABILITY = "package-engine.copy-payload"
GRANT_SCOPE = "package-payload-copy-grant"
RECEIPT_SCOPE = "package-payload-copy-receipt"
MAX_GRANT_SECONDS = 1800
REFERENCE_RE = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GRANT_STATEMENT = (
    "This grant authorizes only hash-verified payload staging for one exact package-engine "
    "session. It grants no process launch, elevation, installation finalization, runtime "
    "execution, deployment, save mutation, signing, publication, catalog mutation, or "
    "evidence promotion authority."
)
RECEIPT_STATEMENT = (
    "This receipt records a completed hash-verified copy into a new staging directory. "
    "It does not install into a product or game directory and grants no later authority."
)


class PackageCopyError(RuntimeError):
    pass


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise PackageCopyError(f"{label} must be an object.")
    return value


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise PackageCopyError(f"{label} must be an array.")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PackageCopyError(f"{label} must be a non-empty string.")
    return value


def _reference(value: object, label: str) -> str:
    result = _text(value, label)
    if len(result) > 128 or REFERENCE_RE.fullmatch(result) is None:
        raise PackageCopyError(f"{label} must be a stable namespaced logical ID.")
    return result


def _hash(value: object, label: str) -> str:
    result = _text(value, label)
    if SHA256_RE.fullmatch(result) is None:
        raise PackageCopyError(f"{label} must be a lowercase SHA-256 value.")
    return result


def _utc(value: object, label: str) -> str:
    result = _text(value, label)
    if len(result) > 64 or not result.endswith("Z") or "T" not in result:
        raise PackageCopyError(f"{label} must be an ISO-8601 UTC timestamp ending in Z.")
    try:
        parsed = dt.datetime.fromisoformat(result[:-1] + "+00:00")
    except ValueError as exc:
        raise PackageCopyError(f"{label} is not a valid ISO-8601 timestamp.") from exc
    if parsed.utcoffset() != dt.timedelta(0):
        raise PackageCopyError(f"{label} must use UTC.")
    return result


def _utc_dt(value: object, label: str) -> dt.datetime:
    return dt.datetime.fromisoformat(_utc(value, label)[:-1] + "+00:00")


def _authority() -> dict[str, bool]:
    return {field: False for field in AUTHORITY_FIELDS}


def _relative_path(value: object, label: str) -> str:
    result = _text(value, label)
    path = PurePosixPath(result)
    if (
        path.is_absolute()
        or "\\" in result
        or "//" in result
        or any(part in {"", ".", ".."} for part in path.parts)
        or any(ord(ch) < 32 or ord(ch) == 127 for ch in result)
        or len(result) > 1024
    ):
        raise PackageCopyError(f"{label} must be a safe relative POSIX path.")
    return result


def _reject_symlink_components(path: Path, label: str) -> None:
    current = path
    while True:
        if current.is_symlink():
            raise PackageCopyError(f"{label} contains a symbolic link: {current}")
        if current.parent == current:
            break
        current = current.parent


def _file_sha256(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    finally:
        os.close(descriptor)
    return digest.hexdigest(), size


def _plan(session: Mapping[str, object]) -> dict[str, object]:
    handoff = _object(session.get("handoff"), "session.handoff")
    receipt = _object(handoff.get("receipt"), "session.handoff.receipt")
    return _object(receipt.get("plan"), "session.handoff.receipt.plan")


def _inventory(session: Mapping[str, object]) -> list[dict[str, object]]:
    plan = _plan(session)
    rows: list[dict[str, object]] = []
    destinations: set[str] = set()
    for package_index, raw_package in enumerate(_array(plan.get("packages"), "plan.packages")):
        package = _object(raw_package, f"plan.packages[{package_index}]")
        package_id = _reference(package.get("package_id"), f"plan.packages[{package_index}].package_id")
        for file_index, raw_file in enumerate(_array(package.get("payload"), f"{package_id}.payload")):
            item = _object(raw_file, f"{package_id}.payload[{file_index}]")
            destination = _relative_path(item.get("destination"), f"{package_id}.payload[{file_index}].destination")
            if destination.casefold() in destinations:
                raise PackageCopyError(f"Duplicate or case-colliding destination: {destination}")
            destinations.add(destination.casefold())
            size = item.get("size_bytes")
            if type(size) is not int or size < 0:
                raise PackageCopyError(f"{package_id}.payload[{file_index}].size_bytes must be non-negative.")
            rows.append({
                "package_id": package_id,
                "source": _relative_path(item.get("source"), f"{package_id}.payload[{file_index}].source"),
                "destination": destination,
                "sha256": _hash(item.get("sha256"), f"{package_id}.payload[{file_index}].sha256"),
                "size_bytes": size,
                "redistribution": _text(item.get("redistribution"), f"{package_id}.payload[{file_index}].redistribution"),
            })
    rows.sort(key=lambda row: (str(row["destination"]).casefold(), str(row["destination"])))
    summary = _object(plan.get("summary"), "plan.summary")
    if len(rows) != summary.get("payload_file_count") or sum(int(row["size_bytes"]) for row in rows) != summary.get("payload_size_bytes"):
        raise PackageCopyError("Payload inventory does not match the resolver summary.")
    return rows


def build_copy_grant(
    session: Mapping[str, object], *, issuer: str, issued_at_utc: str,
    expires_at_utc: str, nonce: str
) -> dict[str, object]:
    try:
        checked = validate_engine_session(session)
    except PackageEngineError as exc:
        raise PackageCopyError(f"Package-engine session verification failed: {exc}") from exc
    issued = _utc_dt(issued_at_utc, "issued_at_utc")
    expires = _utc_dt(expires_at_utc, "expires_at_utc")
    accepted = _utc_dt(checked["accepted_at_utc"], "session.accepted_at_utc")
    if issued < accepted:
        raise PackageCopyError("issued_at_utc must not precede session acceptance.")
    if expires <= issued or expires - issued > dt.timedelta(seconds=MAX_GRANT_SECONDS):
        raise PackageCopyError("Copy grant expiry must be after issuance and within 30 minutes.")
    inventory = _inventory(checked)
    base = {
        "schema_version": 1,
        "grant_scope": GRANT_SCOPE,
        "session_sha256": checked["session_sha256"],
        "capability": COPY_CAPABILITY,
        "issuer": _text(issuer, "issuer"),
        "issued_at_utc": _utc(issued_at_utc, "issued_at_utc"),
        "expires_at_utc": _utc(expires_at_utc, "expires_at_utc"),
        "nonce": _reference(nonce, "nonce"),
        "inventory_sha256": sha256(inventory),
        "session": checked,
        "statement": GRANT_STATEMENT,
        "authority": _authority(),
    }
    return {**base, "grant_sha256": sha256(base)}


def validate_copy_grant(grant: Mapping[str, object]) -> dict[str, object]:
    document = dict(grant)
    if document.get("schema_version") != 1 or document.get("grant_scope") != GRANT_SCOPE:
        raise PackageCopyError("Copy grant schema or scope is invalid.")
    if document.get("capability") != COPY_CAPABILITY or document.get("statement") != GRANT_STATEMENT:
        raise PackageCopyError("Copy grant capability or statement is invalid.")
    declared = _hash(document.get("grant_sha256"), "grant.grant_sha256")
    unsigned = {key: value for key, value in document.items() if key != "grant_sha256"}
    if sha256(unsigned) != declared:
        raise PackageCopyError("Copy grant fingerprint does not match its content.")
    expected = build_copy_grant(
        _object(document.get("session"), "grant.session"),
        issuer=_text(document.get("issuer"), "grant.issuer"),
        issued_at_utc=_utc(document.get("issued_at_utc"), "grant.issued_at_utc"),
        expires_at_utc=_utc(document.get("expires_at_utc"), "grant.expires_at_utc"),
        nonce=_reference(document.get("nonce"), "grant.nonce"),
    )
    if document != expected:
        raise PackageCopyError("Copy grant is stale, altered, or not canonically derived.")
    return document


def stage_payload(
    grant: Mapping[str, object], source_root: Path, staging_root: Path, *, copied_at_utc: str
) -> dict[str, object]:
    checked = validate_copy_grant(grant)
    copied_at = _utc_dt(copied_at_utc, "copied_at_utc")
    if copied_at < _utc_dt(checked["issued_at_utc"], "grant.issued_at_utc"):
        raise PackageCopyError("copied_at_utc must not precede grant issuance.")
    if copied_at > _utc_dt(checked["expires_at_utc"], "grant.expires_at_utc"):
        raise PackageCopyError("Copy grant expired before staging began.")
    source = Path(source_root)
    target = Path(staging_root)
    if not source.is_dir() or source.is_symlink():
        raise PackageCopyError("Source root must be an existing non-symlink directory.")
    _reject_symlink_components(source, "Source root")
    if target.exists() or target.is_symlink():
        raise PackageCopyError("Staging root must not already exist.")
    if not target.parent.is_dir() or target.parent.is_symlink():
        raise PackageCopyError("Staging parent must be an existing non-symlink directory.")
    _reject_symlink_components(target.parent, "Staging parent")
    if source.resolve() == target.parent.resolve() or source.resolve() in target.parent.resolve().parents:
        raise PackageCopyError("Staging root must be outside the source tree.")

    inventory = _inventory(_object(checked.get("session"), "grant.session"))
    temporary = target.parent / f".{target.name}.{checked['grant_sha256']}.tmp"
    if temporary.exists() or temporary.is_symlink():
        raise PackageCopyError("Deterministic temporary staging directory already exists.")
    copied_rows: list[dict[str, object]] = []
    temporary.mkdir(mode=0o700)
    try:
        for row in inventory:
            source_path = source.joinpath(*PurePosixPath(str(row["source"])).parts)
            destination_path = temporary.joinpath(*PurePosixPath(str(row["destination"])).parts)
            if source_path.is_symlink() or not source_path.is_file():
                raise PackageCopyError(f"Payload source is not a regular non-symlink file: {row['source']}")
            _reject_symlink_components(source_path.parent, "Payload source")
            actual_hash, actual_size = _file_sha256(source_path)
            if actual_hash != row["sha256"] or actual_size != row["size_bytes"]:
                raise PackageCopyError(f"Payload source hash or size mismatch: {row['source']}")
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            if destination_path.exists() or destination_path.is_symlink():
                raise PackageCopyError(f"Payload destination collision: {row['destination']}")
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            out_fd = os.open(destination_path, flags, 0o600)
            in_fd = os.open(source_path, os.O_RDONLY | (os.O_NOFOLLOW if hasattr(os, "O_NOFOLLOW") else 0))
            try:
                while True:
                    chunk = os.read(in_fd, 1024 * 1024)
                    if not chunk:
                        break
                    view = memoryview(chunk)
                    while view:
                        written = os.write(out_fd, view)
                        if written <= 0:
                            raise PackageCopyError("Payload copy made no forward progress.")
                        view = view[written:]
                os.fsync(out_fd)
            finally:
                os.close(in_fd)
                os.close(out_fd)
            staged_hash, staged_size = _file_sha256(destination_path)
            if staged_hash != row["sha256"] or staged_size != row["size_bytes"]:
                raise PackageCopyError(f"Staged payload verification failed: {row['destination']}")
            copied_rows.append(dict(row))
        os.rename(temporary, target)
    except Exception:
        if temporary.exists() and not temporary.is_symlink():
            for child in sorted(temporary.rglob("*"), reverse=True):
                if child.is_file() or child.is_symlink():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            temporary.rmdir()
        raise

    base = {
        "schema_version": 1,
        "receipt_scope": RECEIPT_SCOPE,
        "grant_sha256": checked["grant_sha256"],
        "session_sha256": checked["session_sha256"],
        "inventory_sha256": checked["inventory_sha256"],
        "copied_at_utc": _utc(copied_at_utc, "copied_at_utc"),
        "staging_reference": _reference(f"staging.{target.name.lower().replace('_', '-')}", "staging_reference"),
        "file_count": len(copied_rows),
        "size_bytes": sum(int(row["size_bytes"]) for row in copied_rows),
        "files": copied_rows,
        "copy_performed": True,
        "process_launched": False,
        "elevation_requested": False,
        "installation_finalized": False,
        "statement": RECEIPT_STATEMENT,
        "authority": _authority(),
    }
    return {**base, "copy_receipt_sha256": sha256(base)}


__all__ = [
    "COPY_CAPABILITY", "PackageCopyError", "build_copy_grant", "validate_copy_grant", "stage_payload"
]
