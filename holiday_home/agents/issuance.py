"""IssuanceAgent — generate the license (owner name, validity, reference, unit
specs). For apartments (issue-before-inspect path), the license is issued as
'issued, not yet permitted to operate' because the exact point at which it
becomes operational depends on the unresolved sequencing rule."""
from __future__ import annotations

from datetime import date, timedelta

from agents.base import COMPLETE, AgentResult, LLMAgent, PipelineContext
from models import License


class IssuanceAgent(LLMAgent):
    name = "IssuanceAgent"

    def run(self, ctx: PipelineContext) -> AgentResult:
        app = ctx.application
        path = ctx.state.get("inspection_path")

        valid_from = app.term_start or date.today()
        valid_to = app.term_end or (valid_from + timedelta(days=365))

        if path == "issue_before_inspect":
            # Issued, but operation is gated; the flip-to-operational timing is
            # the unresolved apartment sequencing rule (already flagged advisory).
            status = "issued_not_operational"
            note = ("Issued, not yet permitted to operate. Operational permission "
                    "is blocked on TODO(LRCD): apartment_inspection_sequencing.")
        else:
            status = "active"
            note = "Active; issued after a passed inspection."

        license_ref = f"HH-{app.unit.unit_type[:3].upper()}-{app.reference}"
        lic = License(
            reference=license_ref,
            owner_name=app.applicant.name,
            unit_id=app.unit.unit_id,
            unit_type=app.unit.unit_type,
            valid_from=valid_from,
            valid_to=valid_to,
            status=status,
            specs={"bedrooms": app.unit.bedrooms, "zone": app.unit.zone,
                   "emirate": app.unit.emirate},
        )
        ctx.state["license"] = lic

        # Persist to the system of record (target is unresolved -> mock TAMM used).
        uri = ctx.adapters["tamm"].persist_record(license_ref, {"status": status})
        self.log(ctx, "issue_license",
                 {"ref": app.reference, "unit_type": app.unit.unit_type},
                 status.upper(), license_ref=license_ref, note=note, persisted=uri)

        return AgentResult(COMPLETE, reasons=[f"License {license_ref} issued ({status}). {note}"])
