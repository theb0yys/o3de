"""Versioned, serializable engine-neutral model of the proposed dialogue API v2."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .errors import RepairError, StaleGenerationError

_SCHEMA_VERSION = 1
API_VERSION = 2
DEFAULT_MAX_GENERATION_GAP = 64


def _canonical_json(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _parse_object(data: bytes, expected_kind: str) -> dict[str, Any]:
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RepairError("invalid API v2 JSON") from exc
    if not isinstance(doc, dict):
        raise RepairError("API v2 document must be an object")
    if doc.get("schema_version") != _SCHEMA_VERSION:
        raise RepairError("unsupported API v2 schema version")
    if doc.get("kind") != expected_kind:
        raise RepairError("unexpected API v2 document kind")
    return doc


def _nonempty(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RepairError(f"{field_name} must be non-empty text")
    return value


def _generation_gap_limit(value: int) -> int:
    if type(value) is not int or value <= 0:
        raise RepairError("max_generation_gap must be a positive integer")
    return value


@dataclass(frozen=True)
class ApiHello:
    assembly_name: str
    assembly_version: str
    supported_api_versions: tuple[int, ...] = (API_VERSION,)

    def __post_init__(self) -> None:
        _nonempty(self.assembly_name, "assembly_name")
        _nonempty(self.assembly_version, "assembly_version")
        if (
            not self.supported_api_versions
            or any(type(version) is not int or version <= 0 for version in self.supported_api_versions)
            or len(set(self.supported_api_versions)) != len(self.supported_api_versions)
        ):
            raise RepairError("supported_api_versions must contain unique positive integers")

    def to_bytes(self) -> bytes:
        return _canonical_json(
            {
                "schema_version": _SCHEMA_VERSION,
                "kind": "api-hello",
                "assembly_name": self.assembly_name,
                "assembly_version": self.assembly_version,
                "supported_api_versions": list(self.supported_api_versions),
            }
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "ApiHello":
        doc = _parse_object(data, "api-hello")
        expected = {
            "schema_version",
            "kind",
            "assembly_name",
            "assembly_version",
            "supported_api_versions",
        }
        if set(doc) != expected:
            raise RepairError("api-hello contains unexpected fields")
        versions = doc["supported_api_versions"]
        if not isinstance(versions, list):
            raise RepairError("supported_api_versions must be an array")
        return cls(
            _nonempty(doc["assembly_name"], "assembly_name"),
            _nonempty(doc["assembly_version"], "assembly_version"),
            tuple(versions),
        )


def negotiate_api_version(local: ApiHello, remote: ApiHello) -> int:
    common = set(local.supported_api_versions).intersection(remote.supported_api_versions)
    if not common:
        raise RepairError("no mutually supported API version")
    return max(common)


@dataclass(frozen=True)
class CommandRegistration:
    owner_id: str
    command_id: str
    label: str

    def __post_init__(self) -> None:
        _nonempty(self.owner_id, "owner_id")
        _nonempty(self.command_id, "command_id")
        _nonempty(self.label, "label")

    def to_bytes(self) -> bytes:
        return _canonical_json(
            {
                "schema_version": _SCHEMA_VERSION,
                "kind": "command-registration",
                "api_version": API_VERSION,
                "owner_id": self.owner_id,
                "command_id": self.command_id,
                "label": self.label,
            }
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "CommandRegistration":
        doc = _parse_object(data, "command-registration")
        expected = {
            "schema_version",
            "kind",
            "api_version",
            "owner_id",
            "command_id",
            "label",
        }
        if set(doc) != expected:
            raise RepairError("command-registration contains unexpected fields")
        if doc["api_version"] != API_VERSION:
            raise RepairError("unsupported command-registration API version")
        return cls(doc["owner_id"], doc["command_id"], doc["label"])


@dataclass(frozen=True)
class RegistrationToken:
    value: str
    owner_id: str
    command_id: str
    generation: int = 0

    def __post_init__(self) -> None:
        _nonempty(self.value, "token value")
        _nonempty(self.owner_id, "owner_id")
        _nonempty(self.command_id, "command_id")
        if type(self.generation) is not int or self.generation < 0:
            raise RepairError("registration generation must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "owner_id": self.owner_id,
            "command_id": self.command_id,
            "registration_generation": self.generation,
        }

    @classmethod
    def from_dict(cls, doc: Any) -> "RegistrationToken":
        expected = {"value", "owner_id", "command_id", "registration_generation"}
        if not isinstance(doc, dict) or set(doc) != expected:
            raise RepairError("registration token has unexpected fields")
        return cls(
            doc["value"],
            doc["owner_id"],
            doc["command_id"],
            doc["registration_generation"],
        )


@dataclass(frozen=True)
class RegistrySnapshot:
    generation: int
    registrations: tuple[RegistrationToken, ...]

    def __post_init__(self) -> None:
        if type(self.generation) is not int or self.generation < 0:
            raise RepairError("registry generation must be non-negative")
        keys: set[tuple[str, str]] = set()
        for token in self.registrations:
            key = (token.owner_id, token.command_id)
            if key in keys:
                raise RepairError("registry snapshot contains duplicate owner/command")
            if token.generation > self.generation:
                raise RepairError("registration generation exceeds registry generation")
            keys.add(key)
        if self.generation == 0 and self.registrations:
            raise RepairError("generation zero registry must be empty")

    def to_bytes(self) -> bytes:
        ordered = sorted(
            self.registrations,
            key=lambda token: (token.owner_id, token.command_id),
        )
        return _canonical_json(
            {
                "schema_version": _SCHEMA_VERSION,
                "kind": "registry-snapshot",
                "api_version": API_VERSION,
                "generation": self.generation,
                "registrations": [token.to_dict() for token in ordered],
            }
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "RegistrySnapshot":
        doc = _parse_object(data, "registry-snapshot")
        expected = {
            "schema_version", "kind", "api_version", "generation", "registrations"
        }
        if set(doc) != expected:
            raise RepairError("registry snapshot contains unexpected fields")
        if doc["api_version"] != API_VERSION:
            raise RepairError("unsupported registry snapshot API version")
        registrations = doc["registrations"]
        if not isinstance(registrations, list):
            raise RepairError("registry snapshot registrations must be an array")
        return cls(
            doc["generation"],
            tuple(RegistrationToken.from_dict(item) for item in registrations),
        )


@dataclass
class DialogueRegistryV2:
    api_version: int = API_VERSION
    _registrations: dict[tuple[str, str], RegistrationToken] = field(default_factory=dict)
    _generation: int = 0

    @property
    def generation(self) -> int:
        return self._generation

    def register(self, registration: CommandRegistration) -> RegistrationToken:
        key = (registration.owner_id, registration.command_id)
        if key in self._registrations:
            raise RepairError("duplicate owner/command registration")
        self._generation += 1
        token = RegistrationToken(
            value=f"v2:{registration.owner_id}:{registration.command_id}",
            owner_id=registration.owner_id,
            command_id=registration.command_id,
            generation=self._generation,
        )
        self._registrations[key] = token
        return token

    def query(self, owner_id: str) -> tuple[RegistrationToken, ...]:
        _nonempty(owner_id, "owner_id")
        return tuple(
            sorted(
                (
                    token
                    for (owner, _), token in self._registrations.items()
                    if owner == owner_id
                ),
                key=lambda token: token.command_id,
            )
        )

    def unregister(
        self,
        owner_id: str,
        token: RegistrationToken,
        *,
        fail: bool = False,
    ) -> bool:
        key = (owner_id, token.command_id)
        current = self._registrations.get(key)
        if current != token or token.owner_id != owner_id:
            raise RepairError("stale or cross-owner registration token")
        if fail:
            return False
        del self._registrations[key]
        self._generation += 1
        return True

    def snapshot(self) -> RegistrySnapshot:
        return RegistrySnapshot(
            self._generation,
            tuple(self._registrations.values()),
        )

    def to_snapshot_bytes(self) -> bytes:
        return self.snapshot().to_bytes()

    def apply_snapshot(
        self,
        snapshot: RegistrySnapshot,
        *,
        max_generation_gap: int = DEFAULT_MAX_GENERATION_GAP,
    ) -> bool:
        limit = _generation_gap_limit(max_generation_gap)
        if snapshot.generation < self._generation:
            raise StaleGenerationError(
                f"snapshot generation {snapshot.generation} is older than current {self._generation}"
            )
        if snapshot.generation == self._generation:
            if snapshot.to_bytes() != self.snapshot().to_bytes():
                raise RepairError("registry snapshot conflicts at the current generation")
            return False
        gap = snapshot.generation - self._generation
        if gap > limit:
            raise StaleGenerationError(
                f"snapshot generation gap {gap} exceeds limit {limit}"
            )
        self._registrations = {
            (token.owner_id, token.command_id): token
            for token in snapshot.registrations
        }
        self._generation = snapshot.generation
        return True

    def apply_snapshot_bytes(
        self,
        data: bytes,
        *,
        max_generation_gap: int = DEFAULT_MAX_GENERATION_GAP,
    ) -> bool:
        return self.apply_snapshot(
            RegistrySnapshot.from_bytes(data),
            max_generation_gap=max_generation_gap,
        )


@dataclass
class RetryableCleanup:
    registry: DialogueRegistryV2
    owner_id: str
    token: RegistrationToken | None

    def attempt(self, *, fail: bool = False) -> bool:
        if self.token is None:
            return True
        removed = self.registry.unregister(self.owner_id, self.token, fail=fail)
        if removed:
            self.token = None
        return removed
