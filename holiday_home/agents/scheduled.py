"""Always-on agents (scheduled, not part of the linear application pipeline):

- TourismFeeAgent       — monthly 6% declaration intake, nil-declaration
                          enforcement, remittance deadline tracking, late flags.
- RenewalsAgent         — expiry reminders (configurable lead time) + renewal cycle.
- ListingsComplianceAgent — scan platforms for license-number presence, detect
                          unlicensed / shared-unit listings, issue takedown notices.

These take their own inputs and write to the shared audit log.
"""
from __future__ import annotations

from datetime import date, timedelta

from agents.base import LLMAgent
from foundation.audit import AuditLog
from foundation.rule_engine import RuleEngine


class TourismFeeAgent(LLMAgent):
    name = "TourismFeeAgent"

    def __init__(self, engine: RuleEngine, audit: AuditLog) -> None:
        super().__init__()
        self.engine = engine
        self.audit = audit

    def process_declaration(self, license_ref: str, period: str, revenue: float,
                            filed_on: date, today: date | None = None) -> dict:
        today = today or date.today()
        rate = self.engine.tourism_fee_rate()
        fee_cfg = self.engine.config.get("fees", {}).get("tourism_fee", {})
        deadline_day = fee_cfg.get("remittance_deadline_day", 15)

        fee_due = round(revenue * rate, 2)
        is_nil = revenue == 0
        # Deadline is the configured day of the month following the period.
        year, month = (int(x) for x in period.split("-"))
        nxt = date(year + (month // 12), (month % 12) + 1, min(deadline_day, 28))
        late = filed_on > nxt

        outcome = "NIL_DECLARATION" if is_nil else "FEE_DUE"
        if is_nil and not fee_cfg.get("nil_declaration_required", False):
            outcome = "NIL_NOT_REQUIRED"

        self.audit.record(
            self.name, "tourism_declaration",
            {"license": license_ref, "period": period, "revenue": revenue},
            outcome, fee_due=fee_due, deadline=str(nxt), filed_on=str(filed_on), late=late,
        )
        return {"fee_due": fee_due, "nil": is_nil, "late": late, "deadline": str(nxt)}


class RenewalsAgent(LLMAgent):
    name = "RenewalsAgent"

    def __init__(self, audit: AuditLog, lead_time_days: int = 30) -> None:
        super().__init__()
        self.audit = audit
        self.lead_time_days = lead_time_days

    def check_expiry(self, license_ref: str, valid_to: date, today: date | None = None) -> dict:
        today = today or date.today()
        days_left = (valid_to - today).days
        reminder_due = 0 <= days_left <= self.lead_time_days
        expired = days_left < 0
        outcome = "EXPIRED" if expired else ("REMINDER_SENT" if reminder_due else "OK")
        self.audit.record(
            self.name, "renewal_check", {"license": license_ref, "valid_to": str(valid_to)},
            outcome, days_left=days_left, lead_time_days=self.lead_time_days,
        )
        return {"days_left": days_left, "reminder_due": reminder_due, "expired": expired}


class ListingsComplianceAgent(LLMAgent):
    name = "ListingsComplianceAgent"

    def __init__(self, audit: AuditLog, known_licenses: set[str] | None = None) -> None:
        super().__init__()
        self.audit = audit
        self.known_licenses = known_licenses or set()

    def scan_listing(self, listing: dict) -> dict:
        """listing = {id, platform, license_number, shared_unit(bool)}"""
        lic = listing.get("license_number")
        issues = []
        if not lic:
            issues.append("no_license_number")
        elif lic not in self.known_licenses:
            issues.append("unlicensed_or_unknown_license")
        if listing.get("shared_unit"):
            issues.append("shared_unit_listing")

        takedown = bool(issues)
        outcome = "TAKEDOWN_NOTICE" if takedown else "COMPLIANT"
        self.audit.record(
            self.name, "listing_scan",
            {"listing": listing.get("id"), "platform": listing.get("platform")},
            outcome, issues=issues,
        )
        return {"compliant": not takedown, "issues": issues, "takedown": takedown}
