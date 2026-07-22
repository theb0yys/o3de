"""Explicit transaction and cancellation states shared by synthetic primitives."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .errors import CancellationRequested, StateTransitionError
from .journal import CrashRecoveryJournal
from .ownership import ResourceLease


class TransactionPhase(str, Enum):
    NEW = "new"
    PREPARING = "preparing"
    PREPARED = "prepared"
    COMMITTING = "committing"
    COMMITTED = "committed"
    FAILED = "failed"
    ROLLING_BACK = "rolling-back"
    ROLLED_BACK = "rolled-back"
    CANCEL_REQUESTED = "cancel-requested"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"


_ALLOWED: dict[TransactionPhase, frozenset[TransactionPhase]] = {
    TransactionPhase.NEW: frozenset({TransactionPhase.PREPARING, TransactionPhase.CANCEL_REQUESTED}),
    TransactionPhase.PREPARING: frozenset(
        {TransactionPhase.PREPARED, TransactionPhase.FAILED, TransactionPhase.CANCEL_REQUESTED}
    ),
    TransactionPhase.PREPARED: frozenset(
        {TransactionPhase.COMMITTING, TransactionPhase.ROLLING_BACK, TransactionPhase.CANCEL_REQUESTED}
    ),
    TransactionPhase.COMMITTING: frozenset(
        {TransactionPhase.COMMITTED, TransactionPhase.FAILED, TransactionPhase.CANCEL_REQUESTED}
    ),
    TransactionPhase.COMMITTED: frozenset({TransactionPhase.ROLLING_BACK}),
    TransactionPhase.FAILED: frozenset({TransactionPhase.ROLLING_BACK}),
    TransactionPhase.ROLLING_BACK: frozenset({TransactionPhase.ROLLED_BACK, TransactionPhase.FAILED}),
    TransactionPhase.ROLLED_BACK: frozenset(),
    TransactionPhase.CANCEL_REQUESTED: frozenset({TransactionPhase.CANCELLING}),
    TransactionPhase.CANCELLING: frozenset({TransactionPhase.CANCELLED, TransactionPhase.FAILED}),
    TransactionPhase.CANCELLED: frozenset(),
}


@dataclass
class CancellationToken:
    _requested: bool = field(default=False, init=False)
    _reason: str = field(default="cancelled", init=False)

    def request(self, reason: str = "cancelled") -> None:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("cancellation reason must be non-empty text")
        if not self._requested:
            self._requested = True
            self._reason = reason

    @property
    def requested(self) -> bool:
        return self._requested

    @property
    def reason(self) -> str:
        return self._reason

    def checkpoint(self) -> None:
        if self._requested:
            raise CancellationRequested(self._reason)


@dataclass
class TransactionStateMachine:
    transaction_id: str
    journal: CrashRecoveryJournal | None = None
    journal_lease: ResourceLease | None = None
    phase: TransactionPhase = field(init=False, default=TransactionPhase.NEW)
    history: list[TransactionPhase] = field(init=False, default_factory=lambda: [TransactionPhase.NEW])

    def transition(
        self,
        target: TransactionPhase,
        *,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if target not in _ALLOWED[self.phase]:
            raise StateTransitionError(
                f"illegal transaction transition: {self.phase.value} -> {target.value}"
            )
        if self.journal is not None:
            if self.journal_lease is not None:
                self.journal.append_owned(
                    self.journal_lease,
                    self.transaction_id,
                    target.value,
                    payload,
                )
            else:
                self.journal.append(self.transaction_id, target.value, payload)
        elif self.journal_lease is not None:
            raise StateTransitionError("journal lease requires a journal")
        self.phase = target
        self.history.append(target)

    def mark_failed(self, exc: BaseException) -> None:
        if TransactionPhase.FAILED in _ALLOWED[self.phase]:
            self.transition(
                TransactionPhase.FAILED,
                payload={"error_type": type(exc).__name__, "error": str(exc)},
            )

    def request_cancel(self, reason: str) -> None:
        self.transition(TransactionPhase.CANCEL_REQUESTED, payload={"reason": reason})

    def finish_cancel(self) -> None:
        self.transition(TransactionPhase.CANCELLING)
        self.transition(TransactionPhase.CANCELLED)

    @property
    def committed(self) -> bool:
        return self.phase is TransactionPhase.COMMITTED

    @property
    def rolled_back(self) -> bool:
        return self.phase is TransactionPhase.ROLLED_BACK

    @property
    def cancelled(self) -> bool:
        return self.phase is TransactionPhase.CANCELLED
