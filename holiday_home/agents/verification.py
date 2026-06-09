"""VerificationAgent — validate documents, validity dates, required certificates
and authenticity. Emits 'returned for amendments' with reasons."""
from __future__ import annotations

from agents.base import AMEND, CONTINUE, AgentResult, LLMAgent, PipelineContext
from foundation.rule_engine import FAIL


class VerificationAgent(LLMAgent):
    name = "VerificationAgent"

    def run(self, ctx: PipelineContext) -> AgentResult:
        app = ctx.application
        eng = ctx.engine
        amend_reasons: list[str] = []

        # Required documents present?
        docs = eng.check_required_documents(app.unit.unit_type, app.provided_doc_types)
        if docs.status == FAIL:
            amend_reasons += docs.reasons

        # Required certificates present?
        certs = eng.check_required_certificates(app.unit.unit_type, app.certificates)
        if certs.status == FAIL:
            amend_reasons += certs.reasons

        # Insurance must cover term + buffer.
        insurance = next((d for d in app.documents if d.doc_type == "insurance"), None)
        if insurance and insurance.expiry and app.term_end:
            ins = eng.check_insurance_validity(insurance.expiry, app.term_end)
            if ins.status == FAIL:
                amend_reasons += ins.reasons

        # Authenticity (mock flag on each document).
        forged = [d.doc_type for d in app.documents if not d.authentic]
        if forged:
            amend_reasons.append(f"Documents failed authenticity check: {', '.join(forged)}.")

        # External certificate verification via adapters (all mocked).
        if "adcda_fire_cert" in app.certificates:
            ok = ctx.adapters["adcda"].verify_fire_certificate(app.unit.unit_id, "FIRE-CERT-REF")
            self.log(ctx, "adcda_verify", {"unit": app.unit.unit_id}, "PASS" if ok else "FAIL")
            if not ok:
                amend_reasons.append("ADCDA fire certificate could not be verified.")
        if app.unit.unit_type == "apartment":
            connected = ctx.adapters["mcc_hassantuk"].check_connectivity(app.unit.unit_id)
            self.log(ctx, "hassantuk_check", {"unit": app.unit.unit_id},
                     "CONNECTED" if connected else "DISCONNECTED")
            if not connected:
                amend_reasons.append("Hassantuk connectivity not confirmed for apartment.")

        if amend_reasons:
            self.log(ctx, "verify", {"ref": app.reference}, "RETURNED_FOR_AMENDMENTS",
                     reasons=amend_reasons)
            return AgentResult(AMEND, reasons=amend_reasons)

        self.log(ctx, "verify", {"ref": app.reference}, "PASS")
        return AgentResult(CONTINUE, reasons=["All documents and certificates verified."])
