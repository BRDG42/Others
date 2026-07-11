"""IntakeAgent — collect application + documents, extract fields, cross-check
identity fields across documents, run the eligibility pre-screen."""
from __future__ import annotations

from agents.base import AMEND, CONTINUE, HALT, AgentResult, LLMAgent, PipelineContext
from foundation.rule_engine import FAIL


class IntakeAgent(LLMAgent):
    name = "IntakeAgent"

    def run(self, ctx: PipelineContext) -> AgentResult:
        app = ctx.application
        eng = ctx.engine

        # 1. "Extraction" (mocked LLM) — fields already populated on Document.fields.
        self.model_call(f"Extract fields from {len(app.documents)} documents for {app.reference}")
        self.log(ctx, "collect", {"docs": app.provided_doc_types}, "COLLECTED")

        # 2. Cross-document consistency of names / unit / id numbers.
        xcheck = eng.check_cross_consistency(app.documents)
        if xcheck.status == FAIL:
            self.log(ctx, "cross_check", {"ref": app.reference}, "FAIL", reasons=xcheck.reasons)
            return AgentResult(AMEND, reasons=xcheck.reasons)

        # 3. Eligibility pre-screen.
        kind = eng.check_applicant_kind(app.applicant.kind)
        if kind.status == FAIL:
            return AgentResult(HALT, reasons=kind.reasons)

        emirate = eng.check_emirate(app.unit.emirate)
        if emirate.status == FAIL:
            return AgentResult(HALT, reasons=emirate.reasons)

        age = eng.check_applicant_age(app.applicant.age)
        if age.parked and age.gating:
            return AgentResult(HALT, reasons=age.reasons, parked_todos=[age.todo_id])

        count = eng.check_license_count(app.applicant.existing_license_count)
        if count.parked and count.gating:
            return AgentResult(HALT, reasons=count.reasons, parked_todos=[count.todo_id])

        # 4. Operator category mapping (advisory — does not block).
        op = eng.operator_category(app.operator_type)
        if op.parked:
            ctx.flag_advisory(op.todo_id, op.reasons[0])

        self.log(ctx, "eligibility_prescreen", {"ref": app.reference}, "PASS")
        return AgentResult(CONTINUE, reasons=["Intake complete; eligibility pre-screen passed."])
