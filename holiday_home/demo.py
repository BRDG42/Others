"""End-to-end demonstration of the Holiday Home licensing prototype.

Runs three mock applications:
  1. APARTMENT — clean; demonstrates the issue-before-inspect path
     (issued, not yet permitted to operate) and the apartment-sequencing TODO.
  2. VILLA — first submission has insurance that expires too early, so it is
     returned for amendments; on resubmission it completes (active) and shows
     the inspect-before-issue path.
  3. UNDERAGE APPLICANT — depends on the unresolved minimum-age rule, so the
     engine PARKS it and reports the exact TODO(LRCD) that blocks it.

Both human-in-the-loop gates (site inspection, final approval) are
auto-approved in demo mode WITH A LOGGED NOTE. No real external calls are made.
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adapters.base import default_adapters
from agents.scheduled import (
    ListingsComplianceAgent, RenewalsAgent, TourismFeeAgent,
)
from foundation.audit import AuditLog
from foundation.rule_engine import RuleEngine
from models import Applicant, Application, Document, GateDecision, GateRequest, Unit
from orchestrator import Orchestrator

RULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rules")


# -- demo-mode human gate: auto-approve WITH a logged note --------------------

def demo_gate_handler(gate: GateRequest) -> GateDecision:
    return GateDecision(
        approved=True,
        actor=f"demo-auto-approver({gate.name})",
        note="DEMO MODE: human gate auto-approved with logged note. "
             "A real deployment requires a human inspector / authority sign-off.",
    )


# -- demo amendment provider: fix the villa's insurance expiry on round 1 -----

def demo_amendment_provider(app: Application, reasons: list[str], round_no: int) -> bool:
    fixed = False
    for reason in reasons:
        if "Insurance expires" in reason:
            insurance = next((d for d in app.documents if d.doc_type == "insurance"), None)
            if insurance and app.term_end:
                insurance.expiry = app.term_end + timedelta(days=60)  # now covers term + buffer
                fixed = True
    return fixed


def build_apartment() -> Application:
    start = date.today()
    end = start + timedelta(days=365)
    applicant = Applicant(name="Sara Al Mansoori", id_number="784-1990-1234567-1",
                          age=35, existing_license_count=1)
    unit = Unit(unit_id="APT-001", unit_type="apartment", zone="residential", bedrooms=2)
    common = {"applicant_name": applicant.name, "unit_id": unit.unit_id,
              "id_number": applicant.id_number}
    docs = [
        Document("emirates_id", common),
        Document("title_deed_or_tenancy", common),
        Document("insurance", common, expiry=end + timedelta(days=60)),
        Document("adcda_fire_cert", common),
        Document("hassantuk_connectivity", common),
        Document("unit_photos", common),
    ]
    return Application(
        reference="APP-APT-100", applicant=applicant, unit=unit, documents=docs,
        certificates=["adcda_fire_cert", "hassantuk_connectivity"],
        term_start=start, term_end=end, operator_type="self_managed",
    )


def build_villa() -> Application:
    start = date.today()
    end = start + timedelta(days=365)
    applicant = Applicant(name="Khalid Al Hosani", id_number="784-1985-7654321-2",
                          age=41, existing_license_count=0)
    unit = Unit(unit_id="VIL-009", unit_type="villa", zone="residential", bedrooms=4)
    common = {"applicant_name": applicant.name, "unit_id": unit.unit_id,
              "id_number": applicant.id_number}
    docs = [
        Document("emirates_id", common),
        Document("title_deed_or_tenancy", common),
        # Expires BEFORE term + 1 month -> triggers the amendments loop on round 1.
        Document("insurance", common, expiry=end - timedelta(days=10)),
        Document("adcda_fire_cert", common),
        Document("unit_photos", common),
    ]
    return Application(
        reference="APP-VIL-200", applicant=applicant, unit=unit, documents=docs,
        certificates=["adcda_fire_cert"],
        term_start=start, term_end=end, operator_type="self_managed",
    )


def build_underage() -> Application:
    start = date.today()
    end = start + timedelta(days=365)
    applicant = Applicant(name="Younger Applicant", id_number="784-2007-1111111-3",
                          age=19, existing_license_count=0)
    unit = Unit(unit_id="APT-777", unit_type="apartment", zone="residential", bedrooms=1)
    common = {"applicant_name": applicant.name, "unit_id": unit.unit_id,
              "id_number": applicant.id_number}
    docs = [
        Document("emirates_id", common),
        Document("title_deed_or_tenancy", common),
        Document("insurance", common, expiry=end + timedelta(days=60)),
        Document("adcda_fire_cert", common),
        Document("hassantuk_connectivity", common),
        Document("unit_photos", common),
    ]
    return Application(
        reference="APP-AGE-300", applicant=applicant, unit=unit, documents=docs,
        certificates=["adcda_fire_cert", "hassantuk_connectivity"],
        term_start=start, term_end=end, operator_type="self_managed",
    )


def print_outcome(outcome) -> None:
    print(f"\n  RESULT: {outcome.reference} -> {outcome.status}")
    for r in outcome.reasons:
        print(f"    - {r}")
    if outcome.parked_todos:
        print("    PARKED on unresolved rule(s):")
        for t in outcome.parked_todos:
            print(f"      * TODO(LRCD): {t}")
    if outcome.advisory_todos:
        print("    Advisory TODO(LRCD) flags raised (non-blocking):")
        for t in outcome.advisory_todos:
            print(f"      * {t}")
    if outcome.license:
        lic = outcome.license
        print(f"    LICENSE {lic.reference}: {lic.owner_name} | {lic.unit_type} "
              f"{lic.unit_id} | {lic.valid_from}..{lic.valid_to} | status={lic.status}")


def run_pipeline_demos(audit: AuditLog) -> dict:
    engine = RuleEngine(RULES_DIR, audit=audit)
    adapters = default_adapters()
    orch = Orchestrator(engine, audit, adapters, demo_gate_handler, demo_amendment_provider)

    results = {}
    for label, app in [("APARTMENT", build_apartment()),
                       ("VILLA", build_villa()),
                       ("UNDERAGE (unresolved-rule refusal)", build_underage())]:
        print("\n" + "=" * 78)
        print(f"PROCESSING {label}: {app.reference}")
        print("=" * 78)
        outcome = orch.run(app)
        print_outcome(outcome)
        results[app.reference] = outcome
    return results


def run_scheduled_demos(audit: AuditLog, known_license: str | None) -> None:
    print("\n" + "=" * 78)
    print("ALWAYS-ON AGENTS (scheduled, outside the linear pipeline)")
    print("=" * 78)
    engine = RuleEngine(RULES_DIR, audit=audit)

    tourism = TourismFeeAgent(engine, audit)
    r1 = tourism.process_declaration("HH-VIL-APP-VIL-200", "2026-05", 50000.0,
                                     filed_on=date(2026, 6, 20))  # late
    print(f"\n  TourismFee: 6% on 50000 -> fee_due={r1['fee_due']} late={r1['late']} "
          f"(deadline {r1['deadline']})")
    r2 = tourism.process_declaration("HH-VIL-APP-VIL-200", "2026-06", 0.0,
                                     filed_on=date(2026, 7, 10))  # nil, on time
    print(f"  TourismFee: nil declaration -> nil={r2['nil']} late={r2['late']}")

    renewals = RenewalsAgent(audit, lead_time_days=30)
    r3 = renewals.check_expiry("HH-VIL-APP-VIL-200", date.today() + timedelta(days=20))
    print(f"\n  Renewals: expiring in {r3['days_left']}d -> reminder_due={r3['reminder_due']}")

    listings = ListingsComplianceAgent(audit, known_licenses={known_license} if known_license else set())
    c1 = listings.scan_listing({"id": "L1", "platform": "MockBnB",
                                "license_number": known_license, "shared_unit": False})
    c2 = listings.scan_listing({"id": "L2", "platform": "MockBnB",
                                "license_number": None, "shared_unit": True})
    print(f"\n  Listings: L1 compliant={c1['compliant']} issues={c1['issues']}")
    print(f"  Listings: L2 compliant={c2['compliant']} issues={c2['issues']}")


def main() -> None:
    audit = AuditLog()
    results = run_pipeline_demos(audit)

    villa = results.get("APP-VIL-200")
    known_license = villa.license.reference if villa and villa.license else None
    run_scheduled_demos(audit, known_license)

    print("\n" + "=" * 78)
    print("FULL AUDIT TRAIL")
    print("=" * 78)
    print(audit.render())


if __name__ == "__main__":
    main()
