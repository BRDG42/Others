"""ApprovalAgent (HUMAN-IN-THE-LOOP) — decision support (zoning / restricted-zone
/ grant-property checks, NOC compilation), recommend, then gate on a human
authority sign-off."""
from __future__ import annotations

from agents.base import CONTINUE, HALT, AgentResult, LLMAgent, PipelineContext
from foundation.rule_engine import FAIL
from models import GateRequest


class ApprovalAgent(LLMAgent):
    name = "ApprovalAgent"

    def run(self, ctx: PipelineContext) -> AgentResult:
        app = ctx.application
        eng = ctx.engine

        # Zoning / restricted-zone / grant-property decision support.
        zoning = eng.check_zoning(app.unit.zone, app.unit.is_grant_property, app.noc_present)
        if zoning.status == FAIL:
            return AgentResult(HALT, reasons=zoning.reasons)

        # Compile NOCs where the unit type requires one (farms -> ADAFSA, floating -> Maritime).
        noc_records = []
        noc_authority = {"farm": "ADAFSA", "floating": "Maritime"}.get(app.unit.unit_type)
        if noc_authority:
            noc = ctx.adapters["noc"].request_noc(noc_authority, app.unit.unit_id)
            noc_records.append(noc)
            self.log(ctx, "compile_noc", {"authority": noc_authority}, "GRANTED", noc=noc["noc_ref"])
        ctx.state["nocs"] = noc_records

        # Approval authority routing is unresolved (advisory).
        authority = eng.approval_authority()
        if authority.parked:
            ctx.flag_advisory(authority.todo_id, authority.reasons[0])

        # System-of-record target is unresolved (advisory).
        sor = eng.system_of_record()
        if sor.parked:
            ctx.flag_advisory(sor.todo_id, sor.reasons[0])

        # Recommendation (decision support) then HUMAN authority sign-off gate.
        recommendation = "RECOMMEND_APPROVE" if zoning.passed else "RECOMMEND_REJECT"
        self.model_call(f"Draft approval recommendation for {app.reference}: {recommendation}")
        gate = GateRequest(
            name="final_approval",
            application_ref=app.reference,
            summary=f"Final approval for {app.reference} ({app.unit.unit_type})",
            payload={"recommendation": recommendation, "nocs": noc_records,
                     "advisory_todos": list(ctx.advisory_todos)},
        )
        decision = ctx.gate_handler(gate)
        self.log(ctx, "approval_gate",
                 {"ref": app.reference, "recommendation": recommendation},
                 "APPROVED" if decision.approved else "REJECTED",
                 decided_by=decision.actor, note=decision.note)

        if not decision.approved:
            return AgentResult(HALT, reasons=[f"Final approval declined: {decision.note}"])
        return AgentResult(CONTINUE, reasons=["Authority sign-off recorded."])
