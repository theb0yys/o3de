"""Read-only partial rollback plans for publication-intent dependency graphs."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

from .errors import PublicationIntentError
from .intent_dependencies import IntentDependencyGraph


def _canonical(doc: dict[str, Any]) -> bytes:
    return (
        json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


@dataclass(frozen=True)
class IntentPartialRollbackAction:
    intent_id: str
    source_status: str
    action: str
    affected_dependents: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "source_status": self.source_status,
            "action": self.action,
            "affected_dependents": list(self.affected_dependents),
        }

    @classmethod
    def from_dict(cls, doc: Any) -> "IntentPartialRollbackAction":
        expected = {"intent_id", "source_status", "action", "affected_dependents"}
        if not isinstance(doc, dict) or set(doc) != expected or not isinstance(doc["affected_dependents"], list):
            raise PublicationIntentError("partial rollback action is invalid")
        return cls(
            doc["intent_id"],
            doc["source_status"],
            doc["action"],
            tuple(doc["affected_dependents"]),
        )


@dataclass(frozen=True)
class IntentPartialRollbackPlan:
    source_graph_sha256: str
    trigger_intents: tuple[str, ...]
    affected_intents: tuple[str, ...]
    rollback_order: tuple[str, ...]
    actions: tuple[IntentPartialRollbackAction, ...]

    def __post_init__(self) -> None:
        if len(self.source_graph_sha256) != 64:
            raise PublicationIntentError("rollback plan graph hash is invalid")
        if not self.trigger_intents:
            raise PublicationIntentError("rollback plan requires trigger intents")
        if self.trigger_intents != tuple(sorted(self.trigger_intents)):
            raise PublicationIntentError("rollback triggers must be sorted")
        if set(self.rollback_order) != set(self.affected_intents):
            raise PublicationIntentError("rollback order does not cover affected intents")
        if tuple(item.intent_id for item in self.actions) != self.rollback_order:
            raise PublicationIntentError("rollback actions do not match rollback order")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "authority": "synthetic-publication-intent-partial-rollback-plan-only",
            "runtime_authority": "none",
            "promotion": "none",
            "execution_authority": "none",
            "source_graph_sha256": self.source_graph_sha256,
            "trigger_intents": list(self.trigger_intents),
            "affected_intents": list(self.affected_intents),
            "rollback_order": list(self.rollback_order),
            "actions": [item.to_dict() for item in self.actions],
        }

    def to_bytes(self) -> bytes:
        return _canonical(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()

    @classmethod
    def from_bytes(cls, data: bytes) -> "IntentPartialRollbackPlan":
        try:
            doc = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PublicationIntentError("invalid partial rollback plan") from exc
        expected = {
            "schema_version", "authority", "runtime_authority", "promotion",
            "execution_authority", "source_graph_sha256", "trigger_intents",
            "affected_intents", "rollback_order", "actions",
        }
        if not isinstance(doc, dict) or set(doc) != expected:
            raise PublicationIntentError("partial rollback plan has unexpected fields")
        if (
            doc["schema_version"] != 1
            or doc["authority"] != "synthetic-publication-intent-partial-rollback-plan-only"
            or doc["runtime_authority"] != "none"
            or doc["promotion"] != "none"
            or doc["execution_authority"] != "none"
            or not all(isinstance(doc[name], list) for name in (
                "trigger_intents", "affected_intents", "rollback_order", "actions"
            ))
        ):
            raise PublicationIntentError("partial rollback plan boundary is invalid")
        return cls(
            doc["source_graph_sha256"],
            tuple(doc["trigger_intents"]),
            tuple(doc["affected_intents"]),
            tuple(doc["rollback_order"]),
            tuple(IntentPartialRollbackAction.from_dict(item) for item in doc["actions"]),
        )


def build_intent_partial_rollback_plan(
    graph: IntentDependencyGraph,
    trigger_intents: Iterable[str],
) -> IntentPartialRollbackPlan:
    triggers = tuple(sorted(set(trigger_intents)))
    if not triggers:
        raise PublicationIntentError("partial rollback requires trigger intents")
    by_id = {node.intent_id: node for node in graph.nodes}
    missing = [item for item in triggers if item not in by_id]
    if missing:
        raise PublicationIntentError("partial rollback trigger is absent from graph")
    if tuple(sorted(by_id)) != tuple(sorted(graph.topological_order)):
        raise PublicationIntentError("partial rollback graph order is incomplete")

    dependents: dict[str, set[str]] = {item: set() for item in by_id}
    for node in graph.nodes:
        for dependency in node.dependencies:
            dependents[dependency].add(node.intent_id)

    affected = set(triggers)
    queue = list(triggers)
    while queue:
        current = queue.pop(0)
        for dependent in sorted(dependents[current]):
            if dependent not in affected:
                affected.add(dependent)
                queue.append(dependent)

    rollback_order = tuple(
        intent_id
        for intent_id in reversed(graph.topological_order)
        if intent_id in affected
    )
    actions: list[IntentPartialRollbackAction] = []
    for intent_id in rollback_order:
        node = by_id[intent_id]
        if node.status == "intent-committed":
            action = "rollback-committed"
        elif node.status == "intent-prepared":
            action = "cancel-and-rollback-prepared"
        elif node.status == "intent-rolled-back":
            action = "none-already-rolled-back"
        else:
            raise PublicationIntentError("partial rollback status is unsupported")
        actions.append(
            IntentPartialRollbackAction(
                intent_id,
                node.status,
                action,
                tuple(sorted(dependents[intent_id].intersection(affected))),
            )
        )
    return IntentPartialRollbackPlan(
        graph.sha256,
        triggers,
        tuple(sorted(affected)),
        rollback_order,
        tuple(actions),
    )


def verify_intent_partial_rollback_plan(
    graph: IntentDependencyGraph,
    plan: IntentPartialRollbackPlan,
) -> bool:
    rebuilt = build_intent_partial_rollback_plan(graph, plan.trigger_intents)
    if rebuilt != plan:
        raise PublicationIntentError("partial rollback plan does not match graph")
    return True
