"""Canonical API v2 replay-window evaluation and application receipts."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .dialogue_v2 import DEFAULT_MAX_GENERATION_GAP, DialogueRegistryV2, RegistrySnapshot
from .errors import RepairError


def _canonical(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


@dataclass(frozen=True)
class SnapshotReplayWindowReceipt:
    current_generation: int
    incoming_generation: int
    max_generation_gap: int
    generation_gap: int
    current_snapshot_sha256: str
    incoming_snapshot_sha256: str
    status: str

    def to_bytes(self) -> bytes:
        return _canonical(
            {
                "schema_version": 1,
                "authority": "synthetic-api-v2-replay-window-only",
                "runtime_authority": "none",
                "promotion": "none",
                "current_generation": self.current_generation,
                "incoming_generation": self.incoming_generation,
                "max_generation_gap": self.max_generation_gap,
                "generation_gap": self.generation_gap,
                "current_snapshot_sha256": self.current_snapshot_sha256,
                "incoming_snapshot_sha256": self.incoming_snapshot_sha256,
                "status": self.status,
            }
        )

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()


def evaluate_snapshot_replay_window(
    registry: DialogueRegistryV2,
    snapshot: RegistrySnapshot,
    *,
    max_generation_gap: int = DEFAULT_MAX_GENERATION_GAP,
) -> SnapshotReplayWindowReceipt:
    if type(max_generation_gap) is not int or max_generation_gap <= 0:
        raise RepairError("max_generation_gap must be a positive integer")
    current = registry.snapshot()
    gap = snapshot.generation - current.generation
    if gap < 0:
        status = "replayed-stale"
    elif gap == 0:
        status = (
            "already-current"
            if snapshot.to_bytes() == current.to_bytes()
            else "same-generation-conflict"
        )
    elif gap > max_generation_gap:
        status = "replay-window-exceeded"
    else:
        status = "accepted"
    return SnapshotReplayWindowReceipt(
        current.generation,
        snapshot.generation,
        max_generation_gap,
        gap,
        hashlib.sha256(current.to_bytes()).hexdigest(),
        hashlib.sha256(snapshot.to_bytes()).hexdigest(),
        status,
    )


def apply_snapshot_with_replay_receipt(
    registry: DialogueRegistryV2,
    snapshot: RegistrySnapshot,
    *,
    max_generation_gap: int = DEFAULT_MAX_GENERATION_GAP,
) -> SnapshotReplayWindowReceipt:
    receipt = evaluate_snapshot_replay_window(
        registry,
        snapshot,
        max_generation_gap=max_generation_gap,
    )
    if receipt.status == "accepted":
        registry.apply_snapshot(snapshot, max_generation_gap=max_generation_gap)
    return receipt
