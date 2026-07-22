"""Engine-neutral diagnostic paths, generation checks, and atomic publication."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .errors import LockOwnershipError, RepairError, StaleGenerationError
from .ownership import ExclusiveResourceLock, ResourceLease

_RESERVED_WINDOWS_NAMES = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}
_FORMULA_PREFIXES = ("=", "+", "-", "@")
_STATE_SCHEMA = 1


def _canonical_json(doc: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(doc), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


@dataclass(frozen=True)
class DiagnosticLimits:
    field_bytes: int = 256
    row_bytes: int = 4096
    session_bytes: int = 65536
    session_segment_chars: int = 64

    def __post_init__(self) -> None:
        if min(
            self.field_bytes,
            self.row_bytes,
            self.session_bytes,
            self.session_segment_chars,
        ) <= 0:
            raise RepairError("diagnostic limits must be positive")
        if self.field_bytes > self.row_bytes or self.row_bytes > self.session_bytes:
            raise RepairError("diagnostic limits must be field <= row <= session")


@dataclass(frozen=True)
class PublicationState:
    generation: int = 0
    published_bytes: int = 0
    last_owner_id: str | None = None
    row_sha256: str | None = None
    summary_sha256: str | None = None

    def __post_init__(self) -> None:
        if type(self.generation) is not int or self.generation < 0:
            raise RepairError("publication generation must be non-negative")
        if type(self.published_bytes) is not int or self.published_bytes < 0:
            raise RepairError("publication byte count must be non-negative")

    def to_bytes(self) -> bytes:
        return _canonical_json(
            {
                "schema_version": _STATE_SCHEMA,
                "kind": "diagnostic-publication-state",
                "generation": self.generation,
                "published_bytes": self.published_bytes,
                "last_owner_id": self.last_owner_id,
                "row_sha256": self.row_sha256,
                "summary_sha256": self.summary_sha256,
            }
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "PublicationState":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RepairError("invalid diagnostic publication state") from exc
        expected = {
            "schema_version", "kind", "generation", "published_bytes",
            "last_owner_id", "row_sha256", "summary_sha256",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise RepairError("diagnostic publication state has unexpected fields")
        if doc["schema_version"] != _STATE_SCHEMA or doc["kind"] != "diagnostic-publication-state":
            raise RepairError("diagnostic publication state schema mismatch")
        return cls(
            doc["generation"],
            doc["published_bytes"],
            doc["last_owner_id"],
            doc["row_sha256"],
            doc["summary_sha256"],
        )


@dataclass(frozen=True)
class PublicationReceipt:
    owner_id: str
    lock_generation: int
    publication_generation: int
    published_bytes: int
    row_sha256: str
    summary_sha256: str

    def to_bytes(self) -> bytes:
        return _canonical_json(
            {
                "schema_version": 1,
                "authority": "synthetic-two-writer-publication-only",
                "runtime_authority": "none",
                "promotion": "none",
                "owner_id": self.owner_id,
                "lock_generation": self.lock_generation,
                "publication_generation": self.publication_generation,
                "published_bytes": self.published_bytes,
                "row_sha256": self.row_sha256,
                "summary_sha256": self.summary_sha256,
            }
        )


@dataclass
class DiagnosticSession:
    root: Path
    session_name: str
    limits: DiagnosticLimits = field(default_factory=DiagnosticLimits)
    _published_bytes: int = 0

    def __post_init__(self) -> None:
        self.root = self.root.resolve(strict=False)
        self.session_name = validate_session_segment(
            self.session_name,
            self.limits.session_segment_chars,
        )

    @property
    def session_dir(self) -> Path:
        candidate = (self.root / self.session_name).resolve(strict=False)
        _require_descendant(self.root, candidate)
        return candidate

    @property
    def published_bytes(self) -> int:
        return max(self._published_bytes, self.publication_state().published_bytes)

    @property
    def publication_lock(self) -> ExclusiveResourceLock:
        return ExclusiveResourceLock(
            self.session_dir / ".publication.lock",
            f"diagnostic:{self.session_name}",
        )

    @property
    def publication_state_path(self) -> Path:
        return self.session_dir / ".publication-state.json"

    def acquire_writer(
        self,
        owner_id: str,
        *,
        expected_lock_generation: int | None = None,
    ) -> ResourceLease:
        self.session_dir.mkdir(parents=True, exist_ok=True)
        return self.publication_lock.acquire(
            owner_id,
            expected_generation=expected_lock_generation,
        )

    def publication_state(self) -> PublicationState:
        if not self.publication_state_path.exists():
            return PublicationState()
        return PublicationState.from_bytes(self.publication_state_path.read_bytes())

    def encode_support_csv(
        self,
        values: Mapping[str, Any],
        *,
        sensitive_fields: set[str],
    ) -> bytes:
        unknown_sensitive = sensitive_fields.difference(values)
        if unknown_sensitive:
            raise RepairError("sensitive field classification references unknown fields")
        sanitized: list[str] = []
        for key in sorted(values):
            raw = "[REDACTED]" if key in sensitive_fields else str(values[key])
            neutralized = "'" + raw if raw.startswith(_FORMULA_PREFIXES) else raw
            data = neutralized.encode("utf-8")
            if len(data) > self.limits.field_bytes:
                marker = "…[TRUNCATED]"
                budget = max(
                    0,
                    self.limits.field_bytes - len(marker.encode("utf-8")),
                )
                neutralized = data[:budget].decode("utf-8", errors="ignore") + marker
            sanitized.append(neutralized)
        stream = io.StringIO(newline="")
        csv.writer(stream, lineterminator="\n").writerow(sanitized)
        encoded = stream.getvalue().encode("utf-8")
        if len(encoded) > self.limits.row_bytes:
            raise RepairError("diagnostic row exceeds byte limit")
        if self.published_bytes + len(encoded) > self.limits.session_bytes:
            raise RepairError("diagnostic session exceeds byte limit")
        return encoded

    def publish(
        self,
        filename: str,
        payload: bytes,
        summary: Mapping[str, Any],
    ) -> tuple[Path, Path]:
        if self.publication_lock.current_identity() is not None:
            raise LockOwnershipError("diagnostic session is locked; publish_owned is required")
        row_path, summary_path, _ = self._publication_paths(filename)
        new_total = self._published_bytes + len(payload)
        if new_total > self.limits.session_bytes:
            raise RepairError("diagnostic session exceeds byte limit")
        row_before = row_path.read_bytes() if row_path.exists() else None
        summary_before = summary_path.read_bytes() if summary_path.exists() else None
        summary_bytes = _canonical_json(summary)
        try:
            _atomic_write(row_path, payload)
            _atomic_write(summary_path, summary_bytes)
        except Exception:
            _restore(row_path, row_before)
            _restore(summary_path, summary_before)
            raise
        self._published_bytes = new_total
        return row_path, summary_path

    def publish_owned(
        self,
        lease: ResourceLease,
        filename: str,
        payload: bytes,
        summary: Mapping[str, Any],
        *,
        expected_generation: int,
    ) -> PublicationReceipt:
        self.publication_lock.assert_owned(lease)
        if len(payload) > self.limits.row_bytes:
            raise RepairError("diagnostic row exceeds byte limit")
        current = self.publication_state()
        if expected_generation != current.generation:
            raise StaleGenerationError(
                f"expected publication generation {expected_generation}, current is {current.generation}"
            )
        new_total = current.published_bytes + len(payload)
        if new_total > self.limits.session_bytes:
            raise RepairError("diagnostic session exceeds byte limit")

        row_path, summary_path, state_path = self._publication_paths(filename)
        next_generation = current.generation + 1
        summary_doc = dict(summary)
        reserved = {"publication_generation", "publication_owner_id"}.intersection(summary_doc)
        if reserved:
            raise RepairError("publication summary contains reserved ownership fields")
        summary_doc.update(
            {
                "publication_generation": next_generation,
                "publication_owner_id": lease.identity.owner_id,
            }
        )
        summary_bytes = _canonical_json(summary_doc)
        row_sha = hashlib.sha256(payload).hexdigest()
        summary_sha = hashlib.sha256(summary_bytes).hexdigest()
        next_state = PublicationState(
            next_generation,
            new_total,
            lease.identity.owner_id,
            row_sha,
            summary_sha,
        )

        before = {
            row_path: row_path.read_bytes() if row_path.exists() else None,
            summary_path: summary_path.read_bytes() if summary_path.exists() else None,
            state_path: state_path.read_bytes() if state_path.exists() else None,
        }
        try:
            _atomic_write(row_path, payload)
            _atomic_write(summary_path, summary_bytes)
            _atomic_write(state_path, next_state.to_bytes())
        except Exception:
            for path, previous in before.items():
                _restore(path, previous)
            raise
        self._published_bytes = new_total
        return PublicationReceipt(
            lease.identity.owner_id,
            lease.identity.generation,
            next_generation,
            new_total,
            row_sha,
            summary_sha,
        )

    def _publication_paths(self, filename: str) -> tuple[Path, Path, Path]:
        if not filename or Path(filename).name != filename:
            raise RepairError("unsafe diagnostic filename")
        target_dir = self.session_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        return (
            target_dir / filename,
            target_dir / "diagnostic-summary.json",
            self.publication_state_path,
        )


def validate_session_segment(value: str, max_chars: int = 64) -> str:
    if not isinstance(value, str):
        raise RepairError("session segment must be text")
    segment = value.strip()
    if not segment or segment in {".", ".."}:
        raise RepairError("unsafe session segment")
    if Path(segment).is_absolute() or "/" in segment or "\\" in segment:
        raise RepairError("session segment must be one relative component")
    if len(segment) > max_chars:
        raise RepairError("session segment too long")
    if segment.rstrip(" .").lower() in _RESERVED_WINDOWS_NAMES:
        raise RepairError("reserved session segment")
    if re.search(r"[\x00-\x1f<>:\"|?*]", segment):
        raise RepairError("invalid session segment characters")
    return segment


def _require_descendant(root: Path, candidate: Path) -> None:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise RepairError("path escapes configured root") from exc
    if candidate == root:
        raise RepairError("session path must be a strict descendant")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def _restore(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
    else:
        _atomic_write(path, previous)
