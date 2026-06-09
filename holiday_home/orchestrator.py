"""Orchestrator — runs the pipeline, handles the 'returned for amendments' loop,
and pauses at the two human-in-the-loop gates (via the gate handler)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from agents.base import (
    AMEND, COMPLETE, CONTINUE, HALT, LLMAgent, PipelineContext,
)
from agents.classification import ClassificationAgent
from agents.approval import ApprovalAgent
from agents.inspection import InspectionAgent
from agents.intake import IntakeAgent
from agents.issuance import IssuanceAgent
from agents.payment import PaymentAgent
from agents.verification import VerificationAgent
from foundation.audit import AuditLog
from foundation.rule_engine import RuleEngine
from models import Application, GateDecision, GateRequest

# Where in the pipeline an amendment loop re-enters.
AMENDMENT_REENTRY_INDEX = 0   # restart from Intake after amendments
MAX_AMENDMENT_ROUNDS = 3


@dataclass
class PipelineOutcome:
    reference: str
    status: str                       # ISSUED | PARKED | HALTED | AMEND_EXHAUSTED
    reasons: list[str] = field(default_factory=list)
    parked_todos: list[str] = field(default_factory=list)
    advisory_todos: list[str] = field(default_factory=list)
    license: Any = None
    context: PipelineContext | None = None


class Orchestrator:
    def __init__(
        self,
        engine: RuleEngine,
        audit: AuditLog,
        adapters: dict[str, Any],
        gate_handler: Callable[[GateRequest], GateDecision],
        amendment_provider: Callable[[Application, list[str], int], bool] | None = None,
    ) -> None:
        self.engine = engine
        self.audit = audit
        self.adapters = adapters
        self.gate_handler = gate_handler
        # amendment_provider(app, reasons, round) -> True if applicant resubmitted.
        self.amendment_provider = amendment_provider
        self.pipeline: list[LLMAgent] = [
            IntakeAgent(),
            VerificationAgent(),
            ClassificationAgent(),
            InspectionAgent(),
            ApprovalAgent(),
            PaymentAgent(),
            IssuanceAgent(),
        ]

    def run(self, application: Application) -> PipelineOutcome:
        ctx = PipelineContext(
            application=application,
            engine=self.engine,
            audit=self.audit,
            adapters=self.adapters,
            gate_handler=self.gate_handler,
        )
        self.audit.record("Orchestrator", "pipeline_start",
                          {"ref": application.reference, "unit_type": application.unit.unit_type},
                          "STARTED")

        idx = 0
        while idx < len(self.pipeline):
            agent = self.pipeline[idx]
            result = agent.run(ctx)

            if result.status == CONTINUE:
                idx += 1
                continue

            if result.status == COMPLETE:
                self.audit.record("Orchestrator", "pipeline_complete",
                                  {"ref": application.reference}, "ISSUED",
                                  advisory_todos=list(ctx.advisory_todos))
                return PipelineOutcome(
                    reference=application.reference, status="ISSUED",
                    reasons=result.reasons, advisory_todos=list(ctx.advisory_todos),
                    license=ctx.state.get("license"), context=ctx,
                )

            if result.status == AMEND:
                outcome = self._handle_amendment(ctx, result.reasons)
                if outcome is not None:
                    return outcome
                idx = AMENDMENT_REENTRY_INDEX
                continue

            if result.status == HALT:
                # A gating parked rule reports the exact TODO(LRCD) that blocks it.
                if result.parked_todos:
                    self.audit.record("Orchestrator", "pipeline_parked",
                                      {"ref": application.reference}, "PARKED",
                                      todos=result.parked_todos, reasons=result.reasons)
                    return PipelineOutcome(
                        reference=application.reference, status="PARKED",
                        reasons=result.reasons, parked_todos=result.parked_todos,
                        advisory_todos=list(ctx.advisory_todos), context=ctx,
                    )
                self.audit.record("Orchestrator", "pipeline_halted",
                                  {"ref": application.reference}, "HALTED",
                                  reasons=result.reasons)
                return PipelineOutcome(
                    reference=application.reference, status="HALTED",
                    reasons=result.reasons, advisory_todos=list(ctx.advisory_todos),
                    context=ctx,
                )

            raise RuntimeError(f"Unknown agent status: {result.status}")

        # Should not fall through; IssuanceAgent returns COMPLETE.
        return PipelineOutcome(reference=application.reference, status="HALTED",
                               reasons=["Pipeline ended without issuance."], context=ctx)

    def _handle_amendment(self, ctx: PipelineContext, reasons: list[str]) -> PipelineOutcome | None:
        ctx.amendment_round += 1
        self.audit.record("Orchestrator", "returned_for_amendments",
                          {"ref": ctx.application.reference, "round": ctx.amendment_round},
                          "RETURNED", reasons=reasons)

        if ctx.amendment_round > MAX_AMENDMENT_ROUNDS:
            return PipelineOutcome(
                reference=ctx.application.reference, status="AMEND_EXHAUSTED",
                reasons=[f"Exceeded {MAX_AMENDMENT_ROUNDS} amendment rounds."] + reasons,
                advisory_todos=list(ctx.advisory_todos), context=ctx,
            )

        resubmitted = False
        if self.amendment_provider is not None:
            resubmitted = self.amendment_provider(ctx.application, reasons, ctx.amendment_round)
        self.audit.record("Orchestrator", "amendment_resubmission",
                          {"ref": ctx.application.reference, "round": ctx.amendment_round},
                          "RESUBMITTED" if resubmitted else "NO_RESUBMISSION")

        if not resubmitted:
            return PipelineOutcome(
                reference=ctx.application.reference, status="HALTED",
                reasons=["Applicant did not resubmit amendments."] + reasons,
                advisory_todos=list(ctx.advisory_todos), context=ctx,
            )
        return None  # loop re-enters the pipeline
