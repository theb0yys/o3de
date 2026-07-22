"""Bounded backup policy for recoverable multi-file publication intents."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .errors import PublicationIntentError
from .publication_intent import MultiFileIntentPublisher, PublicationTarget
from .ownership import ResourceLease


@dataclass(frozen=True)
class PublicationBackupLimits:
    per_target_bytes: int = 65536
    total_bytes: int = 262144
    max_targets: int = 32

    def __post_init__(self) -> None:
        if min(self.per_target_bytes, self.total_bytes, self.max_targets) <= 0:
            raise PublicationIntentError("publication backup limits must be positive")
        if self.per_target_bytes > self.total_bytes:
            raise PublicationIntentError("per-target backup limit cannot exceed total limit")


class BoundedMultiFileIntentPublisher(MultiFileIntentPublisher):
    """Existing publisher with fail-closed bounds on captured before-images."""

    def __init__(self, root, journal, limits: PublicationBackupLimits | None = None):
        super().__init__(root, journal)
        self.backup_limits = limits or PublicationBackupLimits()

    def _build_intent(
        self,
        lease: ResourceLease,
        intent_id: str,
        targets: Iterable[PublicationTarget],
    ):
        supplied = tuple(targets)
        if len(supplied) > self.backup_limits.max_targets:
            raise PublicationIntentError("publication target count exceeds backup limit")
        total = 0
        for target in supplied:
            path = self._target_path(target.relative_path)
            before_size = path.stat().st_size if path.exists() else 0
            if before_size > self.backup_limits.per_target_bytes:
                raise PublicationIntentError(
                    f"publication backup for {target.relative_path} exceeds per-target limit"
                )
            total += before_size
            if total > self.backup_limits.total_bytes:
                raise PublicationIntentError("publication backups exceed total byte limit")
        return super()._build_intent(lease, intent_id, supplied)
