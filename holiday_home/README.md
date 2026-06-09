# Holiday Home Licensing — Agentic Automation (Reference Prototype)

A **concept demonstrator** of an agentic system that automates the Department of
Culture and Tourism – Abu Dhabi (DCT) Holiday Home licensing journey. Produced by
LRCD for the Technology & AI team as a starting point to extend toward production
on the TAMM platform.

> **This is NOT the production system.** There is no access to TAMM, ADCDA,
> MCC/Hassantuk, or any payment system. Every external system is reached through
> an **adapter interface with a mock implementation** (`# STUB:` marked). No real
> endpoint is ever called.

## Design principles (enforced in code)

1. **No invented regulatory rules.** Every threshold, document list, fee, checklist
   and routing decision is loaded from the `rules/` YAML config. The evaluation
   *logic* lives in code; the *values* live in config.
2. **Unresolved rules are parked, never guessed.** The six open items the LRCD team
   flagged live in `rules/unresolved.yaml`. When an application's decision path
   actually depends on one of them, the rule engine returns `PARKED` and reports the
   exact `TODO(LRCD)` id that blocks it.
3. **Humans stay in the loop** at two explicit gates — **site inspection** and
   **final approval**. These are real pause points handed to a `gate_handler`
   callback, not auto-pass. (In demo mode they auto-approve *with a logged note*.)
4. **Full audit trail.** Every agent action, rule evaluation and decision is logged
   with timestamp, actor, inputs and outcome (`foundation/audit.py`).
5. **LLM-agnostic, offline.** `LLMAgent.model_call` is a deterministic mock, so the
   whole system runs with no API keys.

## Run it

```bash
cd holiday_home
pip install -r requirements.txt          # only PyYAML is required
python demo.py                           # runs the full demo + prints the audit trail
python -m unittest discover -s tests     # run the unit tests (33 tests)
```

`python demo.py` processes three mock applications end to end:

| Application | What it demonstrates |
|---|---|
| **Apartment** (`APP-APT-100`) | The `issue_before_inspect` path → license issued as **"issued, not yet permitted to operate"**, with the apartment-sequencing `TODO(LRCD)` flagged advisory. |
| **Villa** (`APP-VIL-200`) | Insurance that expires too early → **returned for amendments**, resubmitted, then issued **active** via the `inspect_before_issue` path. |
| **Underage applicant** (`APP-AGE-300`) | Decision depends on the unresolved minimum-age rule → the engine **PARKS** it and reports `TODO(LRCD): min_applicant_age`. |

It then exercises the always-on agents (tourism fee, renewals, listings compliance)
and prints the complete audit trail.

## Architecture

```
holiday_home/
  rules/                     # the config layer — all regulatory VALUES live here
    eligibility.yaml documents.yaml fees.yaml inspection.yaml occupancy.yaml
    unresolved.yaml          # the 6 open TODO(LRCD) keys (central registry)
  foundation/
    rule_engine.py           # loads rules, evaluates them, PARKS unresolved paths
    audit.py                 # append-only audit trail
  agents/
    base.py                  # LLM-agnostic agent base (mocked model_call) + pipeline types
    intake.py verification.py classification.py
    inspection.py approval.py        # the two HUMAN-IN-THE-LOOP gates
    payment.py issuance.py
    scheduled.py             # TourismFee / Renewals / ListingsCompliance (always-on)
  adapters/
    base.py                  # adapter interfaces + MOCK implementations (# STUB)
  models.py                  # Application / Document / License / Gate dataclasses
  orchestrator.py            # pipeline, amendments loop, human gates
  demo.py                    # end-to-end demonstration
  tests/                     # unit tests for the rule engine and orchestrator gates
```

### Pipeline (in order)

`Intake → Verification → Classification → Inspection (HITL) → Approval (HITL) → Payment → Issuance`

- **IntakeAgent** — collect documents, extract fields, cross-check that
  names / unit id / id numbers match across documents, eligibility pre-screen.
- **VerificationAgent** — required documents & certificates (ADCDA fire cert,
  Hassantuk connectivity), insurance covers *term + 1 month*, authenticity;
  emits *returned for amendments* with reasons.
- **ClassificationAgent** — classify unit type, route the inspection path.
- **InspectionAgent** *(human gate)* — book, generate checklist, capture report,
  gate on human approval.
- **ApprovalAgent** *(human gate)* — zoning / restricted-zone / grant-property
  checks, NOC compilation, recommend, then authority sign-off.
- **PaymentAgent** — fee calculation from config, payment, receipt, reconciliation.
- **IssuanceAgent** — generate the license; apartments issue as
  "issued, not yet permitted to operate".

### Always-on agents (scheduled, not in the linear flow)

- **TourismFeeAgent** — monthly 6% declaration intake, nil-declaration enforcement,
  remittance deadline tracking, late flags.
- **RenewalsAgent** — expiry reminders (configurable lead time) + renewal cycle.
- **ListingsComplianceAgent** — scan platforms for license-number presence, detect
  unlicensed / shared-unit listings, issue takedown notices.

### Integration adapters (interface + mock)

`TammAdapter`, `AdcdaAdapter`, `MccHassantukAdapter`, `PaymentGatewayAdapter`,
`NocAdapter` (ADAFSA for farms, Maritime for floating). All in `adapters/base.py`,
all mocked, all marked `# STUB: replace with …`.

## Unresolved rules (`TODO(LRCD)`) — must be resolved before production

These are surfaced as config keys in `rules/unresolved.yaml`; the engine refuses any
path that depends on them rather than guessing a value:

| Key | Open question | Effect when triggered |
|---|---|---|
| `min_applicant_age` | 21 (2020 decision) vs. unstated (Guide) | **Gating** — parks the application |
| `max_licenses_per_person` | Guide says 6; no legal basis cited | **Gating** — parks the application |
| `apartment_inspection_sequencing` | issue-before-inspect + 3-day booking duty | Advisory flag on apartments |
| `approval_authority_routing` | DCT "Department" vs. Municipality + MCC | Advisory flag at approval |
| `system_of_record_target` | Holiday Homes System vs. TAMM | Advisory flag at issuance |
| `operator_category_mapping` | 2026 Art. 4 terms vs. Guide's "Authorized Operator" | Advisory flag at intake |

**Gating** items halt the application and report the exact `TODO(LRCD)`. **Advisory**
items are logged and flagged but do not block the prototype demo, so the happy-path
applications still complete while making the open dependency explicit in the audit trail.

## Notes for the production team

- Several config values (fee schedule, document checklists, inspection checklists,
  occupancy formula) are **prototype placeholders** marked `TODO(LRCD)` in the YAML.
  Confirm them against the authoritative DCT sources before use.
- The `gate_handler` callback is where a real deployment wires in human reviewers
  (queue, UI, notification). The demo's auto-approver is for demonstration only and
  records that fact in the audit trail.
- `LLMAgent.model_call` is the single seam for attaching a real LLM backend for
  natural-language extraction / drafting; no decision currently depends on its output.
```
