"""Unit tests for the orchestrator: human-in-the-loop gates, the amendments
loop, and the unresolved-rule refusal (PARKED) behaviour."""
import os
import sys
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters.base import default_adapters
from foundation.audit import AuditLog
from foundation.rule_engine import RuleEngine
from models import Applicant, Application, Document, GateDecision, GateRequest, Unit
from orchestrator import Orchestrator

RULES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules")


def approve_all(gate: GateRequest) -> GateDecision:
    return GateDecision(approved=True, actor=f"test({gate.name})", note="approved in test")


def reject_gate(name):
    def handler(gate: GateRequest) -> GateDecision:
        approved = gate.name != name
        return GateDecision(approved=approved, actor=f"test({gate.name})", note="test")
    return handler


def make_app(unit_type="villa", age=40, license_count=0, bad_insurance=False,
             zone="residential", ref="APP-T") -> Application:
    start = date.today()
    end = start + timedelta(days=365)
    applicant = Applicant(name="Test User", id_number="784-1980-0000000-0",
                          age=age, existing_license_count=license_count)
    unit = Unit(unit_id="U-1", unit_type=unit_type, zone=zone, bedrooms=2)
    common = {"applicant_name": applicant.name, "unit_id": unit.unit_id,
              "id_number": applicant.id_number}
    ins_expiry = (end - timedelta(days=10)) if bad_insurance else (end + timedelta(days=60))
    docs = [
        Document("emirates_id", common),
        Document("title_deed_or_tenancy", common),
        Document("insurance", common, expiry=ins_expiry),
        Document("adcda_fire_cert", common),
        Document("unit_photos", common),
    ]
    certs = ["adcda_fire_cert"]
    if unit_type == "apartment":
        docs.append(Document("hassantuk_connectivity", common))
        certs.append("hassantuk_connectivity")
    return Application(reference=ref, applicant=applicant, unit=unit, documents=docs,
                       certificates=certs, term_start=start, term_end=end,
                       operator_type="self_managed")


def build(gate_handler=approve_all, amendment_provider=None):
    audit = AuditLog()
    engine = RuleEngine(RULES_DIR, audit=audit)
    orch = Orchestrator(engine, audit, default_adapters(), gate_handler, amendment_provider)
    return orch, audit


class TestGates(unittest.TestCase):
    def test_villa_completes_active(self):
        orch, _ = build()
        out = orch.run(make_app("villa", ref="APP-V"))
        self.assertEqual(out.status, "ISSUED")
        self.assertEqual(out.license.status, "active")

    def test_apartment_issued_not_operational(self):
        orch, _ = build()
        out = orch.run(make_app("apartment", ref="APP-A"))
        self.assertEqual(out.status, "ISSUED")
        self.assertEqual(out.license.status, "issued_not_operational")
        self.assertIn("apartment_inspection_sequencing", out.advisory_todos)

    def test_inspection_gate_rejection_halts(self):
        orch, audit = build(gate_handler=reject_gate("site_inspection"))
        out = orch.run(make_app("villa", ref="APP-V"))
        self.assertEqual(out.status, "HALTED")
        actions = [e.action for e in audit.entries]
        self.assertIn("inspection_gate", actions)

    def test_final_approval_rejection_halts(self):
        orch, _ = build(gate_handler=reject_gate("final_approval"))
        out = orch.run(make_app("villa", ref="APP-V"))
        self.assertEqual(out.status, "HALTED")

    def test_both_gates_are_invoked(self):
        seen = []

        def handler(gate: GateRequest) -> GateDecision:
            seen.append(gate.name)
            return GateDecision(approved=True, actor="t", note="")

        orch, _ = build(gate_handler=handler)
        orch.run(make_app("villa", ref="APP-V"))
        self.assertEqual(seen, ["site_inspection", "final_approval"])


class TestAmendmentsLoop(unittest.TestCase):
    def test_amendment_resubmission_recovers(self):
        def provider(app, reasons, rnd):
            ins = next(d for d in app.documents if d.doc_type == "insurance")
            ins.expiry = app.term_end + timedelta(days=60)
            return True

        orch, audit = build(amendment_provider=provider)
        out = orch.run(make_app("villa", bad_insurance=True, ref="APP-V"))
        self.assertEqual(out.status, "ISSUED")
        actions = [e.action for e in audit.entries]
        self.assertIn("returned_for_amendments", actions)

    def test_no_resubmission_halts(self):
        orch, _ = build(amendment_provider=lambda a, r, n: False)
        out = orch.run(make_app("villa", bad_insurance=True, ref="APP-V"))
        self.assertEqual(out.status, "HALTED")

    def test_amendment_rounds_exhausted(self):
        # Provider always claims to resubmit but never fixes -> rounds exhausted.
        orch, _ = build(amendment_provider=lambda a, r, n: True)
        out = orch.run(make_app("villa", bad_insurance=True, ref="APP-V"))
        self.assertEqual(out.status, "AMEND_EXHAUSTED")


class TestUnresolvedRefusal(unittest.TestCase):
    def test_underage_is_parked_with_exact_todo(self):
        orch, _ = build()
        out = orch.run(make_app("apartment", age=19, ref="APP-AGE"))
        self.assertEqual(out.status, "PARKED")
        self.assertEqual(out.parked_todos, ["min_applicant_age"])

    def test_over_cap_is_parked(self):
        orch, _ = build()
        out = orch.run(make_app("villa", license_count=6, ref="APP-CAP"))
        self.assertEqual(out.status, "PARKED")
        self.assertEqual(out.parked_todos, ["max_licenses_per_person"])

    def test_prohibited_zone_halts(self):
        orch, _ = build()
        out = orch.run(make_app("villa", zone="industrial", ref="APP-Z"))
        self.assertEqual(out.status, "HALTED")


if __name__ == "__main__":
    unittest.main()
