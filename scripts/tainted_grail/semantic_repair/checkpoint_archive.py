"""Archive manifests for rotated checkpoint chains."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .checkpoint_chain import CheckpointChainEntry, read_checkpoint_chain
from .errors import CheckpointProofError

_ZERO_HASH = "0" * 64


def _canonical(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_chain_bytes(data: bytes) -> tuple[CheckpointChainEntry, ...]:
    if not data:
        raise CheckpointProofError("checkpoint archive cannot be empty")
    entries: list[CheckpointChainEntry] = []
    expected_previous = _ZERO_HASH
    for line_number, raw in enumerate(data.splitlines(), start=1):
        try:
            doc = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CheckpointProofError(
                f"checkpoint archive line {line_number} is invalid"
            ) from exc
        entry = CheckpointChainEntry.from_dict(doc)
        if entry.index != line_number or entry.previous_entry_sha256 != expected_previous:
            raise CheckpointProofError("checkpoint archive chain continuity failed")
        entries.append(entry)
        expected_previous = entry.entry_sha256
    return tuple(entries)


@dataclass(frozen=True)
class CheckpointArchiveManifest:
    archive_id: str
    archive_index: int
    archive_name: str
    archive_sha256: str
    archived_entry_count: int
    archived_first_entry_sha256: str
    archived_final_entry_sha256: str
    rotation_anchor_sha256: str
    previous_manifest_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.archive_id, str) or not self.archive_id.strip():
            raise CheckpointProofError("archive_id must be non-empty text")
        if type(self.archive_index) is not int or self.archive_index <= 0:
            raise CheckpointProofError("archive_index must be positive")
        if Path(self.archive_name).name != self.archive_name or not self.archive_name:
            raise CheckpointProofError("archive_name must be one safe file name")
        if type(self.archived_entry_count) is not int or self.archived_entry_count <= 0:
            raise CheckpointProofError("archived_entry_count must be positive")
        for value in (
            self.archive_sha256,
            self.archived_first_entry_sha256,
            self.archived_final_entry_sha256,
            self.rotation_anchor_sha256,
            self.previous_manifest_sha256,
        ):
            if not isinstance(value, str) or len(value) != 64:
                raise CheckpointProofError("archive manifest hash is invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-checkpoint-archive-manifest-only",
            "runtime_authority": "none",
            "promotion": "none",
            "archive_id": self.archive_id,
            "archive_index": self.archive_index,
            "archive_name": self.archive_name,
            "archive_sha256": self.archive_sha256,
            "archived_entry_count": self.archived_entry_count,
            "archived_first_entry_sha256": self.archived_first_entry_sha256,
            "archived_final_entry_sha256": self.archived_final_entry_sha256,
            "rotation_anchor_sha256": self.rotation_anchor_sha256,
            "previous_manifest_sha256": self.previous_manifest_sha256,
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return _sha(self.to_bytes())

    @classmethod
    def from_bytes(cls, data: bytes) -> "CheckpointArchiveManifest":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CheckpointProofError("invalid checkpoint archive manifest") from exc
        expected = {
            "schema_version",
            "authority",
            "runtime_authority",
            "promotion",
            "archive_id",
            "archive_index",
            "archive_name",
            "archive_sha256",
            "archived_entry_count",
            "archived_first_entry_sha256",
            "archived_final_entry_sha256",
            "rotation_anchor_sha256",
            "previous_manifest_sha256",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise CheckpointProofError(
                "checkpoint archive manifest has unexpected fields"
            )
        if (
            doc["schema_version"] != 1
            or doc["authority"]
            != "synthetic-checkpoint-archive-manifest-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
        ):
            raise CheckpointProofError(
                "checkpoint archive manifest boundary is invalid"
            )
        return cls(
            doc["archive_id"],
            doc["archive_index"],
            doc["archive_name"],
            doc["archive_sha256"],
            doc["archived_entry_count"],
            doc["archived_first_entry_sha256"],
            doc["archived_final_entry_sha256"],
            doc["rotation_anchor_sha256"],
            doc["previous_manifest_sha256"],
        )


def build_checkpoint_archive_manifest(
    archive_path: Path,
    active_chain_path: Path,
    *,
    archive_id: str,
    archive_index: int,
    previous_manifest: CheckpointArchiveManifest | None = None,
) -> CheckpointArchiveManifest:
    archive_path = Path(archive_path)
    active_chain_path = Path(active_chain_path)
    archive_bytes = archive_path.read_bytes()
    archived = _parse_chain_bytes(archive_bytes)
    active = read_checkpoint_chain(active_chain_path)
    if len(active) != 1 or active[0].kind != "rotation-anchor":
        raise CheckpointProofError(
            "active chain must contain one rotation anchor"
        )
    anchor = active[0]
    if (
        anchor.payload.get("rotated_chain_sha256") != _sha(archive_bytes)
        or anchor.payload.get("rotated_entry_count") != len(archived)
        or anchor.payload.get("rotated_final_entry_sha256")
        != archived[-1].entry_sha256
    ):
        raise CheckpointProofError(
            "rotation anchor does not bind archived chain"
        )
    expected_index = (
        1 if previous_manifest is None else previous_manifest.archive_index + 1
    )
    if archive_index != expected_index:
        raise CheckpointProofError("archive manifest index is not contiguous")
    return CheckpointArchiveManifest(
        archive_id,
        archive_index,
        archive_path.name,
        _sha(archive_bytes),
        len(archived),
        archived[0].entry_sha256,
        archived[-1].entry_sha256,
        anchor.entry_sha256,
        previous_manifest.sha256 if previous_manifest is not None else _ZERO_HASH,
    )


def verify_checkpoint_archive_manifest(
    archive_path: Path,
    active_chain_path: Path,
    manifest: CheckpointArchiveManifest,
    *,
    previous_manifest: CheckpointArchiveManifest | None = None,
) -> bool:
    rebuilt = build_checkpoint_archive_manifest(
        archive_path,
        active_chain_path,
        archive_id=manifest.archive_id,
        archive_index=manifest.archive_index,
        previous_manifest=previous_manifest,
    )
    if rebuilt != manifest:
        raise CheckpointProofError(
            "checkpoint archive manifest does not match archive"
        )
    return True
