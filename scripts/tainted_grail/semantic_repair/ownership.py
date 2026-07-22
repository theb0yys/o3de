"""Deterministic owner/generation leases backed by atomic lock-file creation."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import LockOwnershipError, RepairError, StaleGenerationError

_SCHEMA_VERSION = 1


def _canonical(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _nonempty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RepairError(f"{name} must be non-empty text")
    return value


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


@dataclass(frozen=True)
class LeaseIdentity:
    resource_id: str
    owner_id: str
    generation: int

    def __post_init__(self) -> None:
        _nonempty(self.resource_id, "resource_id")
        _nonempty(self.owner_id, "owner_id")
        if type(self.generation) is not int or self.generation <= 0:
            raise RepairError("lease generation must be a positive integer")

    def to_bytes(self) -> bytes:
        return _canonical(
            {
                "schema_version": _SCHEMA_VERSION,
                "kind": "resource-lease",
                "resource_id": self.resource_id,
                "owner_id": self.owner_id,
                "generation": self.generation,
            }
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "LeaseIdentity":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LockOwnershipError("invalid resource lease") from exc
        expected = {"schema_version", "kind", "resource_id", "owner_id", "generation"}
        if not isinstance(doc, dict) or set(doc) != expected:
            raise LockOwnershipError("resource lease has unexpected fields")
        if doc["schema_version"] != _SCHEMA_VERSION or doc["kind"] != "resource-lease":
            raise LockOwnershipError("resource lease schema mismatch")
        return cls(doc["resource_id"], doc["owner_id"], doc["generation"])


@dataclass
class ResourceLease:
    lock_path: Path
    identity: LeaseIdentity
    _active: bool = field(default=True, init=False, repr=False)

    @property
    def active(self) -> bool:
        return self._active

    def _deactivate(self) -> None:
        self._active = False

    def __enter__(self) -> "ResourceLease":
        if not self._active:
            raise LockOwnershipError("resource lease is inactive")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        ExclusiveResourceLock(self.lock_path, self.identity.resource_id).release(self)


class ExclusiveResourceLock:
    """A portable synthetic lock with monotonic acquisition generations."""

    def __init__(self, path: Path, resource_id: str):
        self.path = Path(path)
        self.resource_id = _nonempty(resource_id, "resource_id")
        self.generation_path = self.path.with_name(f"{self.path.name}.generation")

    def current_identity(self) -> LeaseIdentity | None:
        if not self.path.exists():
            return None
        identity = LeaseIdentity.from_bytes(self.path.read_bytes())
        if identity.resource_id != self.resource_id:
            raise LockOwnershipError("resource lease belongs to another resource")
        return identity

    def current_generation(self) -> int:
        if not self.generation_path.exists():
            return 0
        try:
            doc = json.loads(self.generation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LockOwnershipError("invalid lease generation state") from exc
        expected = {"schema_version", "resource_id", "generation"}
        if not isinstance(doc, dict) or set(doc) != expected:
            raise LockOwnershipError("lease generation state has unexpected fields")
        if doc["schema_version"] != _SCHEMA_VERSION or doc["resource_id"] != self.resource_id:
            raise LockOwnershipError("lease generation state mismatch")
        generation = doc["generation"]
        if type(generation) is not int or generation < 0:
            raise LockOwnershipError("lease generation is invalid")
        return generation

    def acquire(
        self,
        owner_id: str,
        *,
        expected_generation: int | None = None,
    ) -> ResourceLease:
        owner_id = _nonempty(owner_id, "owner_id")
        current_generation = self.current_generation()
        next_generation = current_generation + 1
        if expected_generation is not None and expected_generation != next_generation:
            raise StaleGenerationError(
                f"expected lease generation {expected_generation}, next is {next_generation}"
            )
        identity = LeaseIdentity(self.resource_id, owner_id, next_generation)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            current = self.current_identity()
            detail = (
                f"resource locked by {current.owner_id} generation {current.generation}"
                if current is not None
                else "resource lock exists"
            )
            raise LockOwnershipError(detail) from exc
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(identity.to_bytes())
                handle.flush()
                os.fsync(handle.fileno())
            _atomic_write(
                self.generation_path,
                _canonical(
                    {
                        "schema_version": _SCHEMA_VERSION,
                        "resource_id": self.resource_id,
                        "generation": next_generation,
                    }
                ),
            )
        except Exception:
            self.path.unlink(missing_ok=True)
            raise
        return ResourceLease(self.path, identity)

    def assert_owned(self, lease: ResourceLease) -> None:
        if not isinstance(lease, ResourceLease) or not lease.active:
            raise LockOwnershipError("resource lease is inactive")
        if lease.lock_path != self.path or lease.identity.resource_id != self.resource_id:
            raise LockOwnershipError("resource lease targets another resource")
        current = self.current_identity()
        if current != lease.identity:
            raise LockOwnershipError("resource lease is stale or owned by another writer")

    def release(self, lease: ResourceLease) -> None:
        self.assert_owned(lease)
        self.path.unlink()
        lease._deactivate()
