"""Rule engine ("foundation").

Loads regulatory rules from the YAML config layer and evaluates them. The engine
holds only generic evaluation *logic*; every threshold, enumeration and figure
comes from ``rules/*.yaml``. No regulatory value is invented in code.

Unresolved rules are never given a guessed value. They live in
``rules/unresolved.yaml``. When an application's decision path actually depends
on one of them, the engine returns a PARKED result carrying the exact
``TODO(LRCD)`` statement, and refuses to decide that path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml

# Result statuses.
PASS = "PASS"
FAIL = "FAIL"
PARKED = "PARKED"


@dataclass
class RuleResult:
    rule_id: str
    status: str
    reasons: list[str] = field(default_factory=list)
    todo_id: str | None = None        # set when status == PARKED
    todo_text: str | None = None
    gating: bool = False              # for PARKED: does it halt the application?

    @property
    def passed(self) -> bool:
        return self.status == PASS

    @property
    def parked(self) -> bool:
        return self.status == PARKED


class RuleEngine:
    def __init__(self, rules_dir: str | Path, audit=None) -> None:
        self.rules_dir = Path(rules_dir)
        self.audit = audit
        self.config: dict[str, dict] = {}
        for path in sorted(self.rules_dir.glob("*.yaml")):
            with open(path, "r", encoding="utf-8") as fh:
                self.config[path.stem] = yaml.safe_load(fh) or {}
        self.unresolved: dict[str, dict] = self.config.get("unresolved", {})

    # -- internals ---------------------------------------------------------

    def _log(self, rule_id: str, inputs: dict[str, Any], result: RuleResult) -> None:
        if self.audit is None:
            return
        self.audit.record(
            actor="RuleEngine",
            action=f"evaluate:{rule_id}",
            inputs=inputs,
            outcome=result.status,
            reasons=result.reasons,
            todo=result.todo_id,
        )

    def _park(self, rule_id: str, todo_key: str, extra: str = "") -> RuleResult:
        meta = self.unresolved.get(todo_key, {})
        reason = meta.get("todo", f"TODO(LRCD): unresolved rule '{todo_key}'.")
        if extra:
            reason = f"{reason} ({extra})"
        return RuleResult(
            rule_id=rule_id,
            status=PARKED,
            reasons=[reason],
            todo_id=todo_key,
            todo_text=meta.get("todo"),
            gating=bool(meta.get("gating", False)),
        )

    def _result(self, rule_id: str, status: str, reasons: list[str], inputs: dict) -> RuleResult:
        res = RuleResult(rule_id=rule_id, status=status, reasons=reasons)
        self._log(rule_id, inputs, res)
        return res

    # -- eligibility -------------------------------------------------------

    def check_applicant_age(self, applicant_age: int) -> RuleResult:
        """PASS if the applicant is clearly above the highest stated floor.

        Only applicants below that floor have a decision that *depends* on the
        unresolved minimum age, so only those paths are parked.
        """
        floor = self.unresolved.get("min_applicant_age", {}).get("highest_stated_floor")
        inputs = {"applicant_age": applicant_age, "highest_stated_floor": floor}
        if floor is not None and applicant_age >= floor:
            return self._result(
                "min_applicant_age", PASS,
                [f"Applicant age {applicant_age} >= highest stated floor {floor}."],
                inputs,
            )
        res = self._park(
            "min_applicant_age", "min_applicant_age",
            extra=f"applicant_age={applicant_age} falls below the highest stated floor",
        )
        self._log("min_applicant_age", inputs, res)
        return res

    def check_license_count(self, existing_license_count: int) -> RuleResult:
        cap = self.unresolved.get("max_licenses_per_person", {}).get("stated_cap")
        inputs = {"existing_license_count": existing_license_count, "stated_cap": cap}
        if cap is not None and existing_license_count < cap:
            return self._result(
                "max_licenses_per_person", PASS,
                [f"Existing licenses {existing_license_count} < stated cap {cap}."],
                inputs,
            )
        res = self._park(
            "max_licenses_per_person", "max_licenses_per_person",
            extra=f"existing_license_count={existing_license_count} reaches the unverified cap",
        )
        self._log("max_licenses_per_person", inputs, res)
        return res

    def check_applicant_kind(self, kind: str) -> RuleResult:
        allowed = self.config.get("eligibility", {}).get("allowed_applicant_kinds", [])
        inputs = {"kind": kind, "allowed": allowed}
        if kind in allowed:
            return self._result("applicant_kind", PASS, [f"Applicant kind '{kind}' allowed."], inputs)
        return self._result(
            "applicant_kind", FAIL,
            [f"Applicant kind '{kind}' not in allowed set {allowed}."], inputs,
        )

    def check_emirate(self, emirate: str) -> RuleResult:
        covered = self.config.get("eligibility", {}).get("covered_emirates", [])
        inputs = {"emirate": emirate, "covered": covered}
        if emirate in covered:
            return self._result("covered_emirate", PASS, [f"Emirate '{emirate}' is covered."], inputs)
        return self._result(
            "covered_emirate", FAIL, [f"Emirate '{emirate}' not covered {covered}."], inputs,
        )

    # -- documents ---------------------------------------------------------

    def check_required_documents(self, unit_type: str, provided: list[str]) -> RuleResult:
        required = self.config.get("documents", {}).get("required_documents", {}).get(unit_type, [])
        missing = [d for d in required if d not in provided]
        inputs = {"unit_type": unit_type, "required": required, "provided": provided}
        if not required:
            return self._result(
                "required_documents", FAIL,
                [f"No document checklist configured for unit type '{unit_type}'."], inputs,
            )
        if missing:
            return self._result(
                "required_documents", FAIL,
                [f"Missing required documents: {', '.join(missing)}."], inputs,
            )
        return self._result("required_documents", PASS, ["All required documents present."], inputs)

    def check_cross_consistency(self, documents: list) -> RuleResult:
        """Verify the configured fields match across all documents."""
        fields = self.config.get("documents", {}).get("cross_check_fields", [])
        inputs = {"fields": fields, "doc_count": len(documents)}
        mismatches: list[str] = []
        for f in fields:
            values = {getattr(d, "fields", {}).get(f) for d in documents if f in getattr(d, "fields", {})}
            values.discard(None)
            if len(values) > 1:
                mismatches.append(f"{f}={sorted(values)}")
        if mismatches:
            return self._result(
                "cross_consistency", FAIL,
                [f"Inconsistent across documents: {'; '.join(mismatches)}."], inputs,
            )
        return self._result("cross_consistency", PASS, ["Cross-document fields consistent."], inputs)

    def check_insurance_validity(
        self, insurance_expiry: date, term_end: date,
    ) -> RuleResult:
        buffer_months = self.config.get("documents", {}).get("insurance", {}).get(
            "must_cover_term_plus_months", 0
        )
        # Approximate a month as 30 days for the prototype.
        required_until = _add_months(term_end, buffer_months)
        inputs = {
            "insurance_expiry": str(insurance_expiry),
            "term_end": str(term_end),
            "buffer_months": buffer_months,
            "required_until": str(required_until),
        }
        if insurance_expiry >= required_until:
            return self._result(
                "insurance_validity", PASS,
                [f"Insurance covers term + {buffer_months} month(s) (until {required_until})."],
                inputs,
            )
        return self._result(
            "insurance_validity", FAIL,
            [f"Insurance expires {insurance_expiry}, must cover until {required_until}."],
            inputs,
        )

    def check_required_certificates(self, unit_type: str, provided: list[str]) -> RuleResult:
        certs = self.config.get("documents", {}).get("required_certificates", {})
        needed = [c for c, meta in certs.items() if unit_type in meta.get("applies_to", [])]
        missing = [c for c in needed if c not in provided]
        inputs = {"unit_type": unit_type, "needed": needed, "provided": provided}
        if missing:
            return self._result(
                "required_certificates", FAIL,
                [f"Missing certificate(s): {', '.join(missing)}."], inputs,
            )
        return self._result("required_certificates", PASS, ["Required certificates present."], inputs)

    # -- classification / inspection --------------------------------------

    def inspection_path(self, unit_type: str) -> RuleResult:
        paths = self.config.get("inspection", {}).get("inspection_path", {})
        inputs = {"unit_type": unit_type}
        path = paths.get(unit_type)
        if path is None:
            return self._result(
                "inspection_path", FAIL,
                [f"No inspection path configured for unit type '{unit_type}'."], inputs,
            )
        res = self._result("inspection_path", PASS, [f"Inspection path: {path}."], inputs)
        res.reasons.append(path)  # carry the path value as the last reason for callers
        return res

    def apartment_sequencing(self) -> RuleResult:
        """The 3-day booking-duty / issue-before-inspect timing is unresolved.

        Advisory (non-gating): the orchestrator records the flag and continues.
        """
        res = self._park(
            "apartment_inspection_sequencing", "apartment_inspection_sequencing",
        )
        self._log("apartment_inspection_sequencing", {}, res)
        return res

    def checklist_for(self, unit_type: str) -> list[str]:
        return self.config.get("inspection", {}).get("checklists", {}).get(unit_type, [])

    # -- approval support --------------------------------------------------

    def check_zoning(self, zone: str, is_grant_property: bool, noc_present: bool) -> RuleResult:
        zoning = self.config.get("occupancy", {}).get("zoning", {})
        prohibited = zoning.get("prohibited_zones", [])
        inputs = {"zone": zone, "is_grant_property": is_grant_property, "noc_present": noc_present}
        if zone in prohibited:
            return self._result(
                "zoning", FAIL, [f"Zone '{zone}' is prohibited {prohibited}."], inputs,
            )
        if is_grant_property and zoning.get("grant_property_requires_noc") and not noc_present:
            return self._result(
                "zoning", FAIL, ["Grant property requires an NOC, none present."], inputs,
            )
        return self._result("zoning", PASS, [f"Zone '{zone}' permitted; NOC requirements met."], inputs)

    def approval_authority(self) -> RuleResult:
        """Which authority signs off is unresolved (advisory)."""
        res = self._park("approval_authority", "approval_authority_routing")
        self._log("approval_authority", {}, res)
        return res

    def operator_category(self, operator_type: str | None) -> RuleResult:
        meta = self.unresolved.get("operator_category_mapping", {})
        ambiguous = meta.get("ambiguous_operator_types", [])
        inputs = {"operator_type": operator_type, "ambiguous": ambiguous}
        if operator_type in ambiguous:
            res = self._park("operator_category_mapping", "operator_category_mapping",
                             extra=f"operator_type={operator_type}")
            self._log("operator_category_mapping", inputs, res)
            return res
        return self._result(
            "operator_category_mapping", PASS,
            [f"Operator type '{operator_type}' not in ambiguous mapping set."], inputs,
        )

    def system_of_record(self) -> RuleResult:
        """Persistence target is unresolved (advisory)."""
        res = self._park("system_of_record", "system_of_record_target")
        self._log("system_of_record", {}, res)
        return res

    # -- fees --------------------------------------------------------------

    def license_fee(self, unit_type: str) -> RuleResult:
        fees = self.config.get("fees", {})
        base = fees.get("license_fees", {}).get(unit_type)
        admin = fees.get("admin_fee", 0)
        inputs = {"unit_type": unit_type, "base": base, "admin_fee": admin}
        if base is None:
            return self._result(
                "license_fee", FAIL,
                [f"No license fee configured for unit type '{unit_type}'."], inputs,
            )
        res = self._result(
            "license_fee", PASS, [f"License fee {base} + admin {admin} = {base + admin}."], inputs,
        )
        res.reasons.append(str(base + admin))
        return res

    def tourism_fee_rate(self) -> float:
        return self.config.get("fees", {}).get("tourism_fee", {}).get("rate", 0.0)


def _add_months(d: date, months: int) -> date:
    """Add whole months to a date (prototype-grade; clamps day to 28 for safety)."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, 28)
    return date(year, month, day)
