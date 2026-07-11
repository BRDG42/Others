"""Ad-hoc scenario runner — exercises several different pipeline paths so you can
watch outcomes other than the happy path. Not part of the shipped demo."""
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adapters.base import default_adapters
from foundation.audit import AuditLog
from foundation.rule_engine import RuleEngine
from models import Applicant, Application, Document, GateDecision, GateRequest, Unit
from orchestrator import Orchestrator

RULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")


def approve_all(gate: GateRequest) -> GateDecision:
    return GateDecision(approved=True, actor=f"human({gate.name})", note="signed off")


def reject(name):
    def h(gate: GateRequest) -> GateDecision:
        ok = gate.name != name
        return GateDecision(approved=ok, actor=f"human({gate.name})",
                            note="signed off" if ok else "FAILED checklist items")
    return h


def app(ref, unit_type, *, age=40, licenses=0, zone="residential",
        grant=False, noc=False, operator="self_managed"):
    start = date.today(); end = start + timedelta(days=365)
    a = Applicant("Demo Applicant", "784-1980-0000000-0", age=age, existing_license_count=licenses)
    u = Unit("U-1", unit_type, zone=zone, bedrooms=3, is_grant_property=grant)
    common = {"applicant_name": a.name, "unit_id": u.unit_id, "id_number": a.id_number}
    docs = [Document("emirates_id", common), Document("title_deed_or_tenancy", common),
            Document("insurance", common, expiry=end + timedelta(days=60)),
            Document("adcda_fire_cert", common), Document("unit_photos", common)]
    certs = ["adcda_fire_cert"]
    if unit_type == "apartment":
        docs.append(Document("hassantuk_connectivity", common)); certs.append("hassantuk_connectivity")
    if unit_type == "farm":
        docs.append(Document("adafsa_noc", common))
    return Application(ref, a, u, docs, certs, term_start=start, term_end=end,
                       operator_type=operator, noc_present=noc)


def show(out):
    print(f"  -> {out.status}")
    for r in out.reasons:
        print(f"     {r}")
    if out.parked_todos:
        print(f"     PARKED ON: {', '.join(out.parked_todos)}")
    if out.advisory_todos:
        print(f"     advisory flags: {', '.join(out.advisory_todos)}")
    if out.license:
        print(f"     LICENSE {out.license.reference} status={out.license.status}")


SCENARIOS = [
    ("FARM (needs ADAFSA NOC, grant property)",
     app("SC-FARM", "farm", grant=True, noc=True), approve_all),
    ("VILLA in a PROHIBITED zone (industrial)",
     app("SC-ZONE", "villa", zone="industrial"), approve_all),
    ("APPLICANT at the unverified license cap (6)",
     app("SC-CAP", "villa", licenses=6), approve_all),
    ("AUTHORIZED-OPERATOR mapping (ambiguous)",
     app("SC-OP", "villa", operator="authorized_operator"), approve_all),
    ("INSPECTION GATE REJECTED by the human inspector",
     app("SC-REJ", "villa"), reject("site_inspection")),
]

for title, application, handler in SCENARIOS:
    audit = AuditLog()
    engine = RuleEngine(RULES_DIR, audit=audit)
    orch = Orchestrator(engine, audit, default_adapters(), handler)
    print("\n" + "-" * 70)
    print(title)
    print("-" * 70)
    show(orch.run(application))
