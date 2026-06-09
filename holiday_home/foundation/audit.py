"""Append-only audit trail.

Every agent action, rule evaluation, and decision is recorded here with a
timestamp, the actor (agent or component name), the inputs it acted on, and the
outcome. This is a licensing system: traceability is mandatory, so the log is
append-only and never mutated in place.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class AuditEntry:
    timestamp: str
    actor: str
    action: str
    inputs: dict[str, Any]
    outcome: str
    detail: dict[str, Any] = field(default_factory=dict)

    def as_line(self) -> str:
        base = f"[{self.timestamp}] {self.actor:<22} | {self.action:<28} | {self.outcome}"
        if self.detail:
            base += f"  :: {json.dumps(self.detail, default=str, sort_keys=True)}"
        return base


class AuditLog:
    """Append-only collection of audit entries scoped to a single run."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def record(
        self,
        actor: str,
        action: str,
        inputs: dict[str, Any] | None = None,
        outcome: str = "",
        **detail: Any,
    ) -> AuditEntry:
        entry = AuditEntry(
            timestamp=_now_iso(),
            actor=actor,
            action=action,
            inputs=inputs or {},
            outcome=outcome,
            detail=detail,
        )
        self._entries.append(entry)
        return entry

    @property
    def entries(self) -> list[AuditEntry]:
        # Return a copy so callers cannot mutate the append-only log.
        return list(self._entries)

    def render(self) -> str:
        return "\n".join(e.as_line() for e in self._entries)

    def to_json(self) -> str:
        return json.dumps([asdict(e) for e in self._entries], indent=2, default=str)
