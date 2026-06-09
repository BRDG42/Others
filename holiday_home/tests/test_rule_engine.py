"""Unit tests for the rule engine — including that it refuses (parks) any
unresolved-rule path and reports the exact TODO(LRCD) id."""
import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from foundation.audit import AuditLog
from foundation.rule_engine import FAIL, PARKED, PASS, RuleEngine
from models import Document

RULES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules")


def engine():
    return RuleEngine(RULES_DIR, audit=AuditLog())


class TestEligibility(unittest.TestCase):
    def test_age_above_floor_passes(self):
        self.assertEqual(engine().check_applicant_age(35).status, PASS)

    def test_age_below_floor_parks_with_todo(self):
        res = engine().check_applicant_age(19)
        self.assertEqual(res.status, PARKED)
        self.assertEqual(res.todo_id, "min_applicant_age")
        self.assertTrue(res.gating)
        self.assertIn("TODO(LRCD)", res.reasons[0])

    def test_license_count_under_cap_passes(self):
        self.assertEqual(engine().check_license_count(3).status, PASS)

    def test_license_count_at_cap_parks(self):
        res = engine().check_license_count(6)
        self.assertEqual(res.status, PARKED)
        self.assertEqual(res.todo_id, "max_licenses_per_person")
        self.assertTrue(res.gating)

    def test_unknown_emirate_fails(self):
        self.assertEqual(engine().check_emirate("dubai").status, FAIL)


class TestDocuments(unittest.TestCase):
    def test_missing_documents_fail(self):
        res = engine().check_required_documents("apartment", ["emirates_id"])
        self.assertEqual(res.status, FAIL)
        self.assertIn("hassantuk_connectivity", res.reasons[0])

    def test_complete_documents_pass(self):
        provided = ["emirates_id", "title_deed_or_tenancy", "insurance",
                    "adcda_fire_cert", "hassantuk_connectivity", "unit_photos"]
        self.assertEqual(engine().check_required_documents("apartment", provided).status, PASS)

    def test_insurance_must_cover_term_plus_buffer(self):
        eng = engine()
        term_end = date(2027, 1, 1)
        self.assertEqual(eng.check_insurance_validity(date(2026, 12, 1), term_end).status, FAIL)
        self.assertEqual(eng.check_insurance_validity(date(2027, 3, 1), term_end).status, PASS)

    def test_cross_consistency_detects_mismatch(self):
        docs = [Document("a", {"applicant_name": "X"}), Document("b", {"applicant_name": "Y"})]
        self.assertEqual(engine().check_cross_consistency(docs).status, FAIL)

    def test_apartment_requires_hassantuk_certificate(self):
        # Apartment needs both fire cert and Hassantuk; villa needs only the fire cert.
        self.assertEqual(engine().check_required_certificates("apartment", []).status, FAIL)
        self.assertEqual(
            engine().check_required_certificates("apartment", ["adcda_fire_cert"]).status, FAIL)
        self.assertEqual(
            engine().check_required_certificates("villa", ["adcda_fire_cert"]).status, PASS)


class TestUnresolvedPaths(unittest.TestCase):
    def test_apartment_sequencing_parks_non_gating(self):
        res = engine().apartment_sequencing()
        self.assertEqual(res.status, PARKED)
        self.assertEqual(res.todo_id, "apartment_inspection_sequencing")
        self.assertFalse(res.gating)

    def test_approval_authority_parks(self):
        self.assertEqual(engine().approval_authority().todo_id, "approval_authority_routing")

    def test_system_of_record_parks(self):
        self.assertEqual(engine().system_of_record().todo_id, "system_of_record_target")

    def test_operator_category_ambiguous_parks(self):
        res = engine().operator_category("authorized_operator")
        self.assertEqual(res.status, PARKED)
        self.assertEqual(res.todo_id, "operator_category_mapping")

    def test_operator_category_known_passes(self):
        self.assertEqual(engine().operator_category("self_managed").status, PASS)

    def test_no_regulatory_value_invented_for_unresolved_keys(self):
        # Unresolved keys must NOT carry a resolved value in the eligibility config.
        elig = engine().config["eligibility"]
        self.assertEqual(elig["min_applicant_age"], {"unresolved": "min_applicant_age"})
        self.assertEqual(elig["max_licenses_per_person"],
                         {"unresolved": "max_licenses_per_person"})


class TestRoutingAndFees(unittest.TestCase):
    def test_apartment_routes_issue_before_inspect(self):
        self.assertEqual(engine().inspection_path("apartment").reasons[-1], "issue_before_inspect")

    def test_villa_routes_inspect_before_issue(self):
        self.assertEqual(engine().inspection_path("villa").reasons[-1], "inspect_before_issue")

    def test_zoning_prohibited_zone_fails(self):
        self.assertEqual(engine().check_zoning("industrial", False, False).status, FAIL)

    def test_grant_property_without_noc_fails(self):
        self.assertEqual(engine().check_zoning("residential", True, False).status, FAIL)

    def test_license_fee_includes_admin(self):
        res = engine().license_fee("apartment")
        self.assertEqual(res.status, PASS)
        self.assertEqual(res.reasons[-1], "1250")  # 1000 + 250 admin

    def test_tourism_fee_rate(self):
        self.assertAlmostEqual(engine().tourism_fee_rate(), 0.06)


if __name__ == "__main__":
    unittest.main()
