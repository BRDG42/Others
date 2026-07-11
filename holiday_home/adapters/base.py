"""Integration adapter interfaces + MOCK implementations.

Every external system is reached through one of these adapters. NONE of them
makes a real network call. Each method documents the contract a production
implementation must honour and is marked so it cannot be mistaken for a real
integration.

    # STUB: replace with TAMM / ADCDA / MCC-Hassantuk / payment / NOC backend.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Protocol


class TammAdapter(Protocol):
    def persist_record(self, reference: str, payload: dict) -> str: ...
    def fetch_application(self, reference: str) -> dict | None: ...


class AdcdaAdapter(Protocol):
    def verify_fire_certificate(self, unit_id: str, cert_ref: str) -> bool: ...


class MccHassantukAdapter(Protocol):
    def check_connectivity(self, unit_id: str) -> bool: ...


class PaymentGatewayAdapter(Protocol):
    def charge(self, reference: str, amount: float) -> dict: ...


class NocAdapter(Protocol):
    def request_noc(self, authority: str, unit_id: str) -> dict: ...


# --------------------------------------------------------------------------
# MOCK implementations
# --------------------------------------------------------------------------

class MockTammAdapter:
    # STUB: replace with TAMM platform integration.
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    def persist_record(self, reference: str, payload: dict) -> str:
        self._store[reference] = payload
        return f"tamm-mock://{reference}"

    def fetch_application(self, reference: str) -> dict | None:
        return self._store.get(reference)


class MockAdcdaAdapter:
    # STUB: replace with ADCDA fire-certificate verification.
    def verify_fire_certificate(self, unit_id: str, cert_ref: str) -> bool:
        return bool(cert_ref)  # mock: any non-empty reference is treated as valid


class MockMccHassantukAdapter:
    # STUB: replace with MCC / Hassantuk connectivity check.
    def __init__(self, connected: bool = True) -> None:
        self._connected = connected

    def check_connectivity(self, unit_id: str) -> bool:
        return self._connected


class MockPaymentGatewayAdapter:
    # STUB: replace with the real payment gateway.
    def charge(self, reference: str, amount: float) -> dict:
        return {
            "transaction_id": f"pay-mock-{uuid.uuid4().hex[:8]}",
            "reference": reference,
            "amount": amount,
            "status": "captured",
            "captured_on": str(date.today()),
        }


class MockNocAdapter:
    # STUB: replace with ADAFSA (farms) / Maritime (floating) NOC services.
    def request_noc(self, authority: str, unit_id: str) -> dict:
        return {
            "authority": authority,
            "unit_id": unit_id,
            "noc_ref": f"noc-mock-{uuid.uuid4().hex[:8]}",
            "granted": True,
        }


def default_adapters() -> dict[str, Any]:
    """Bundle of mock adapters used by the demo and tests."""
    return {
        "tamm": MockTammAdapter(),
        "adcda": MockAdcdaAdapter(),
        "mcc_hassantuk": MockMccHassantukAdapter(),
        "payment": MockPaymentGatewayAdapter(),
        "noc": MockNocAdapter(),
    }
