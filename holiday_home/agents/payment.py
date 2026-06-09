"""PaymentAgent — fee calculation (from the fee-schedule config), payment,
receipt, reconciliation."""
from __future__ import annotations

from agents.base import CONTINUE, HALT, AgentResult, LLMAgent, PipelineContext
from foundation.rule_engine import FAIL


class PaymentAgent(LLMAgent):
    name = "PaymentAgent"

    def run(self, ctx: PipelineContext) -> AgentResult:
        app = ctx.application
        eng = ctx.engine

        fee = eng.license_fee(app.unit.unit_type)
        if fee.status == FAIL:
            return AgentResult(HALT, reasons=fee.reasons)
        amount = float(fee.reasons[-1])  # engine appends the total last

        receipt = ctx.adapters["payment"].charge(app.reference, amount)
        self.log(ctx, "charge", {"ref": app.reference, "amount": amount},
                 receipt["status"].upper(), transaction_id=receipt["transaction_id"])

        # Reconciliation: charged amount must match the calculated fee.
        reconciled = receipt["status"] == "captured" and receipt["amount"] == amount
        self.log(ctx, "reconcile", {"expected": amount, "charged": receipt["amount"]},
                 "OK" if reconciled else "MISMATCH")
        if not reconciled:
            return AgentResult(HALT, reasons=["Payment reconciliation failed."])

        ctx.state["receipt"] = receipt
        ctx.state["fee_paid"] = amount
        return AgentResult(CONTINUE, reasons=[f"Fee {amount} captured and reconciled."])
