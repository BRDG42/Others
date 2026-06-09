"""ClassificationAgent — classify the unit type and route the inspection path."""
from __future__ import annotations

from agents.base import CONTINUE, HALT, AgentResult, LLMAgent, PipelineContext
from foundation.rule_engine import FAIL


class ClassificationAgent(LLMAgent):
    name = "ClassificationAgent"

    def run(self, ctx: PipelineContext) -> AgentResult:
        app = ctx.application
        eng = ctx.engine

        path_result = eng.inspection_path(app.unit.unit_type)
        if path_result.status == FAIL:
            return AgentResult(HALT, reasons=path_result.reasons)

        path = path_result.reasons[-1]  # engine appends the path value last
        ctx.state["inspection_path"] = path
        ctx.state["checklist"] = eng.checklist_for(app.unit.unit_type)

        # Apartment uses issue-before-inspect, whose timing duty is unresolved.
        if path == "issue_before_inspect":
            seq = eng.apartment_sequencing()
            ctx.flag_advisory(seq.todo_id, seq.reasons[0])
            ctx.state["sequencing_parked"] = True

        self.log(ctx, "classify",
                 {"unit_type": app.unit.unit_type}, "CLASSIFIED",
                 inspection_path=path)
        return AgentResult(CONTINUE, reasons=[f"Classified as {app.unit.unit_type}; path {path}."])
