"""InspectionAgent (HUMAN-IN-THE-LOOP) — book the inspection, generate the
checklist, capture the inspector report, and gate on human approval."""
from __future__ import annotations

from datetime import date, timedelta

from agents.base import CONTINUE, HALT, AgentResult, LLMAgent, PipelineContext
from models import GateRequest


class InspectionAgent(LLMAgent):
    name = "InspectionAgent"

    def run(self, ctx: PipelineContext) -> AgentResult:
        app = ctx.application
        checklist = ctx.state.get("checklist", [])
        path = ctx.state.get("inspection_path")

        # Book (mock) and generate the checklist.
        booking_date = date.today() + timedelta(days=3)
        ctx.state["inspection_booking"] = str(booking_date)
        self.log(ctx, "book_inspection",
                 {"unit": app.unit.unit_id, "path": path},
                 "BOOKED", booking_date=str(booking_date), checklist=checklist)

        # HUMAN-IN-THE-LOOP gate: a human inspector must sign off the report.
        gate = GateRequest(
            name="site_inspection",
            application_ref=app.reference,
            summary=f"Site inspection for {app.unit.unit_type} {app.unit.unit_id}",
            payload={"checklist": checklist, "path": path},
        )
        decision = ctx.gate_handler(gate)
        self.log(ctx, "inspection_gate",
                 {"ref": app.reference}, "APPROVED" if decision.approved else "REJECTED",
                 decided_by=decision.actor, note=decision.note)

        ctx.state["inspection_passed"] = decision.approved
        if not decision.approved:
            # For inspect-before-issue this blocks; record and halt.
            return AgentResult(HALT, reasons=[f"Inspection not approved: {decision.note}"])

        return AgentResult(CONTINUE, reasons=["Inspection booked and human-approved."])
