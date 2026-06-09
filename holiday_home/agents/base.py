"""LLM-agnostic agent base class and shared pipeline types.

The base class exposes a single ``model_call`` hook so any LLM backend can be
plugged in. The default implementation is a deterministic MOCK so the whole
system runs offline with no API keys. Agent *decisions* are driven by the rule
engine, not by the model; the model hook exists only to demonstrate where
natural-language extraction / drafting would attach.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from foundation.audit import AuditLog
from foundation.rule_engine import RuleEngine
from models import Application, GateDecision, GateRequest

# Agent outcome statuses (distinct from rule-engine statuses).
CONTINUE = "CONTINUE"          # proceed to the next agent
AMEND = "AMEND"                # returned for amendments (re-enter the loop)
HALT = "HALT"                  # blocked; stop processing this application
COMPLETE = "COMPLETE"          # pipeline finished


@dataclass
class AgentResult:
    status: str
    reasons: list[str] = field(default_factory=list)
    parked_todos: list[str] = field(default_factory=list)


@dataclass
class PipelineContext:
    """Carried through the pipeline; agents read and enrich it."""
    application: Application
    engine: RuleEngine
    audit: AuditLog
    adapters: dict[str, Any]
    gate_handler: Callable[[GateRequest], GateDecision]
    state: dict[str, Any] = field(default_factory=dict)
    advisory_todos: list[str] = field(default_factory=list)  # non-gating parked items
    amendment_round: int = 0

    def flag_advisory(self, todo_id: str, text: str | None = None) -> None:
        if todo_id not in self.advisory_todos:
            self.advisory_todos.append(todo_id)
        self.audit.record(
            actor="Orchestrator",
            action="advisory_park",
            inputs={"todo": todo_id},
            outcome="FLAGGED",
            note=text or "",
        )


class LLMAgent:
    """Base class for all pipeline and scheduled agents."""

    name: str = "Agent"

    def __init__(self, name: str | None = None) -> None:
        if name:
            self.name = name

    # -- model hook (mocked) ----------------------------------------------

    def model_call(self, prompt: str, **kwargs: Any) -> str:
        """Deterministic mock of an LLM call.

        Replace with a real backend (e.g. an Anthropic client) to enable
        natural-language extraction/drafting. The prototype never depends on
        the *content* of this for a decision.
        """
        return f"[MOCK-LLM:{self.name}] {prompt.strip()[:80]}"

    # -- audit helper ------------------------------------------------------

    def log(self, ctx: PipelineContext, action: str, inputs: dict, outcome: str, **detail: Any):
        return ctx.audit.record(self.name, action, inputs, outcome, **detail)

    # -- interface ---------------------------------------------------------

    def run(self, ctx: PipelineContext) -> AgentResult:  # pragma: no cover - overridden
        raise NotImplementedError
