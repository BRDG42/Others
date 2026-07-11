"""Domain models for the Holiday Home licensing prototype."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class Document:
    """A submitted document. ``fields`` carries extracted values used for
    cross-document consistency checks (applicant_name, unit_id, id_number, ...)."""
    doc_type: str
    fields: dict[str, Any] = field(default_factory=dict)
    expiry: date | None = None        # used for insurance, etc.
    authentic: bool = True            # mock authenticity flag


@dataclass
class Applicant:
    name: str
    id_number: str
    age: int
    kind: str = "natural_person"      # natural_person | legal_entity
    existing_license_count: int = 0


@dataclass
class Unit:
    unit_id: str
    unit_type: str                    # apartment | villa | townhouse | farm | caravan | floating
    emirate: str = "abu_dhabi"
    zone: str = "residential"
    bedrooms: int = 1
    is_grant_property: bool = False


@dataclass
class Application:
    reference: str
    applicant: Applicant
    unit: Unit
    documents: list[Document] = field(default_factory=list)
    certificates: list[str] = field(default_factory=list)
    term_start: date | None = None
    term_end: date | None = None
    operator_type: str | None = None
    noc_present: bool = False

    @property
    def provided_doc_types(self) -> list[str]:
        return [d.doc_type for d in self.documents]


@dataclass
class GateRequest:
    """A human-in-the-loop pause point handed to the gate handler."""
    name: str                         # "site_inspection" | "final_approval"
    application_ref: str
    summary: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class GateDecision:
    approved: bool
    actor: str                        # who decided (human inspector / authority)
    note: str = ""


@dataclass
class License:
    reference: str
    owner_name: str
    unit_id: str
    unit_type: str
    valid_from: date
    valid_to: date
    status: str                       # "active" | "issued_not_operational"
    specs: dict[str, Any] = field(default_factory=dict)
