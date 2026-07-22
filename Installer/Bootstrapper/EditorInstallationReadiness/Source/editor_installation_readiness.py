#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Read-only bridge from installation-state registry snapshots to editor readiness."""
from __future__ import annotations

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
    validate_registry_snapshot,
)
from wizard_view_model import AUTHORITY_FIELDS, sha256  # noqa: E402

EDITOR_READINESS_CAPABILITY = "tg-editor.consume-installation-state"
EDITOR_READINESS_SCOPE = "tg-editor-installation-readiness"
REFERENCE_RE = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
READINESS_STATEMENT = (
    "This readiness document lets editor tooling consume one validated SDK installation-state registry "
    "snapshot. It is read-only and grants no package copy, process launch, elevation, lifecycle execution, "
    "installation-state publication, product or game directory mutation, runtime execution, save mutation, "
    "signing, network publication, catalogue mutation, or evidence-promotion authority."
)


class EditorInstallationReadinessError(RuntimeError):
    pass


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise EditorInstallationReadinessError(f"{label} must be an object.")
    return value


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise EditorInstallationReadinessError(f"{label} must be an array.")
    return value


def _text(value: object, label: str, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum:
        raise EditorInstallationReadinessError(
            f"{label} must be non-empty trimmed text of at most {maximum} characters."
        )
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise EditorInstallationReadinessError(f"{label} contains a forbidden control character.")
    return value


def _reference(value: object, label: str) -> str:
    result = _text(value, label, 128)
    if REFERENCE_RE.fullmatch(result) is None:
        raise EditorInstallationReadinessError(f"{label} must be a stable namespaced logical ID.")
    return result


def _optional_reference(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _reference(value, label)


def _hash(value: object, label: str) -> str:
    result = _text(value, label, 64)
    if SHA256_RE.fullmatch(result) is None:
        raise EditorInstallationReadinessError(f"{label} must be a lowercase SHA-256 value.")
    return result


def _optional_hash(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _hash(value, label)


def _bool(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise EditorInstallationReadinessError(f"{label} must be a boolean.")
    return bool(value)


def _authority() -> dict[str, bool]:
    return {field: False for field in AUTHORITY_FIELDS}


def _forbidden_flags() -> tuple[str, ...]:
    return (
        "product_or_game_directory_mutated",
        "runtime_executed",
        "save_mutated",
        "signing_performed",
        "network_publication_performed",
        "catalog_mutated",
        "evidence_promoted",
    )


def _validated_snapshot(snapshot: Mapping[str, object]) -> dict[str, object]:
    try:
        return validate_registry_snapshot(snapshot)
    except InstallationStateRegistryError as exc:
        raise EditorInstallationReadinessError(f"Registry snapshot verification failed: {exc}") from exc


def _active_records(snapshot: Mapping[str, object], target_reference: str | None) -> list[dict[str, object]]:
    matches: list[dict[str, object]] = []
    for index, raw in enumerate(_array(snapshot.get("records"), "snapshot.records")):
        record = _object(raw, f"snapshot.records[{index}]")
        if record.get("state_status") != "active":
            continue
        if target_reference is not None and record.get("target_reference") != target_reference:
            continue
        matches.append(record)
    return matches


def _ready_payload(record: Mapping[str, object] | None) -> dict[str, object]:
    if record is None:
        return {
            "state_reference": None,
            "state_status": None,
            "state_file_sha256": None,
            "state_record_sha256": None,
            "published_at_utc": None,
            "package_order": [],
            "summary": None,
            "evidence": None,
        }
    package_order = [
        _reference(item, f"ready_record.package_order[{index}]")
        for index, item in enumerate(_array(record.get("package_order"), "ready_record.package_order"))
    ]
    summary = _object(record.get("summary"), "ready_record.summary")
    return {
        "state_reference": _reference(record.get("state_reference"), "ready_record.state_reference"),
        "state_status": _text(record.get("state_status"), "ready_record.state_status", 32),
        "state_file_sha256": _hash(record.get("state_file_sha256"), "ready_record.state_file_sha256"),
        "state_record_sha256": _hash(record.get("state_record_sha256"), "ready_record.state_record_sha256"),
        "published_at_utc": _text(record.get("published_at_utc"), "ready_record.published_at_utc", 64),
        "package_order": package_order,
        "summary": {
            "package_count": summary.get("package_count"),
            "payload_file_count": summary.get("payload_file_count"),
            "payload_size_bytes": summary.get("payload_size_bytes"),
        },
        "evidence": {
            "session_sha256": _hash(record.get("session_sha256"), "ready_record.session_sha256"),
            "handoff_sha256": _hash(record.get("handoff_sha256"), "ready_record.handoff_sha256"),
            "lifecycle_result_sha256": _hash(
                record.get("lifecycle_result_sha256"),
                "ready_record.lifecycle_result_sha256",
            ),
            "copy_receipt_sha256": _optional_hash(
                record.get("copy_receipt_sha256"),
                "ready_record.copy_receipt_sha256",
            ),
            "launch_result_sha256": _optional_hash(
                record.get("launch_result_sha256"),
                "ready_record.launch_result_sha256",
            ),
            "elevation_request_confirmed": bool(record.get("elevation_request_confirmed", False)),
            "elevated_completion_observed": bool(record.get("elevated_completion_observed", False)),
            "elevation_result_sha256": _optional_hash(
                record.get("elevation_result_sha256"),
                "ready_record.elevation_result_sha256",
            ),
            "elevated_completion_observation_sha256": _optional_hash(
                record.get("elevated_completion_observation_sha256"),
                "ready_record.elevated_completion_observation_sha256",
            ),
        },
    }


def build_editor_installation_readiness(
    registry_snapshot: Mapping[str, object], *, editor_reference: str, requested_at_utc: str,
    target_reference: str | None = None,
) -> dict[str, object]:
    snapshot = _validated_snapshot(registry_snapshot)
    requested_target = _optional_reference(target_reference, "target_reference")
    active = _active_records(snapshot, requested_target)
    selected: dict[str, object] | None = None
    if len(active) == 1:
        selected = active[0]
        ready = True
        status = "ready"
        reason = "One active SDK installation state is available for editor tooling."
    elif len(active) > 1:
        ready = False
        status = "blocked-ambiguous-active-installation"
        reason = "Multiple active SDK installation states match the editor request."
    else:
        ready = False
        status = "blocked-no-active-installation"
        reason = "No active SDK installation state is available for editor tooling."
    target = requested_target
    if target is None and selected is not None:
        target = _reference(selected.get("target_reference"), "selected.target_reference")
    payload = _ready_payload(selected)
    base = {
        "schema_version": 1,
        "readiness_scope": EDITOR_READINESS_SCOPE,
        "capability": EDITOR_READINESS_CAPABILITY,
        "registry_snapshot_sha256": _hash(snapshot.get("snapshot_sha256"), "snapshot.snapshot_sha256"),
        "state_root_reference": _reference(snapshot.get("state_root_reference"), "snapshot.state_root_reference"),
        "editor_reference": _reference(editor_reference, "editor_reference"),
        "target_reference": target,
        "requested_at_utc": _text(requested_at_utc, "requested_at_utc", 64),
        "observed_at_utc": _text(snapshot.get("observed_at_utc"), "snapshot.observed_at_utc", 64),
        "ready": ready,
        "status": status,
        "reason": reason,
        "active_match_count": len(active),
        "registry_record_count": snapshot.get("record_count"),
        "registry_active_count": snapshot.get("active_count"),
        **payload,
        "registry_snapshot": snapshot,
        "product_or_game_directory_mutated": False,
        "runtime_executed": False,
        "save_mutated": False,
        "signing_performed": False,
        "network_publication_performed": False,
        "catalog_mutated": False,
        "evidence_promoted": False,
        "statement": READINESS_STATEMENT,
        "authority": _authority(),
    }
    return {**base, "readiness_sha256": sha256(base)}


def validate_editor_installation_readiness(readiness: Mapping[str, object]) -> dict[str, object]:
    document = dict(readiness)
    if (
        document.get("schema_version") != 1
        or document.get("readiness_scope") != EDITOR_READINESS_SCOPE
        or document.get("capability") != EDITOR_READINESS_CAPABILITY
        or document.get("statement") != READINESS_STATEMENT
        or document.get("authority") != _authority()
    ):
        raise EditorInstallationReadinessError("Editor installation readiness contract is invalid.")
    for field in _forbidden_flags():
        if document.get(field) is not False:
            raise EditorInstallationReadinessError(f"Editor readiness flag {field} must remain false.")
    if document.get("ready") is not (document.get("status") == "ready"):
        raise EditorInstallationReadinessError("Editor readiness flags are inconsistent.")
    _bool(document.get("ready"), "readiness.ready")
    expected = build_editor_installation_readiness(
        _object(document.get("registry_snapshot"), "readiness.registry_snapshot"),
        editor_reference=_reference(document.get("editor_reference"), "readiness.editor_reference"),
        requested_at_utc=_text(document.get("requested_at_utc"), "readiness.requested_at_utc", 64),
        target_reference=_optional_reference(document.get("target_reference"), "readiness.target_reference"),
    )
    if document != expected:
        raise EditorInstallationReadinessError("Editor installation readiness is stale, altered, or not canonically derived.")
    return document


__all__ = [
    "EDITOR_READINESS_CAPABILITY",
    "EDITOR_READINESS_SCOPE",
    "EditorInstallationReadinessError",
    "build_editor_installation_readiness",
    "validate_editor_installation_readiness",
]
