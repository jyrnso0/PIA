from uuid import uuid4

from .errors import InvalidTransition
from .events import EventSource
from .state_machine import StateMachine
from .value_objects import Cancellation, Money, PagoState, PaymentBreakdown, Penalty

S = PagoState
_TABLE = {
    S.PENDIENTE: {"confirm": S.CONFIRMADO},
    S.CONFIRMADO: {"refund": S.REEMBOLSADO, "settle": S.LIQUIDADO},
}


class Pago(EventSource):
    """Aggregate root. Importe, desglose 20/80 (BR-0005), penalizaciones y reembolsos (BR-0017)."""

    COMMISSION = "0.20"
    LATE_PENALTY = "0.50"

    def __init__(self, reserva_id: str, amount: Money, id: str | None = None):
        self.id = id or str(uuid4())
        self.reserva_id, self.amount = reserva_id, amount
        self.machine = StateMachine("Pago", S.PENDIENTE, _TABLE)
        self.breakdown: PaymentBreakdown | None = None
        self.receipt: str | None = None
        self.refunded = Money(0)
        self.refund_reason: str | None = None
        self.refund_responsible: str | None = None
        self.refunded_at = None
        self.refund_evidence: list[str] = []

    @property
    def state(self) -> PagoState:
        return self.machine.state

    def confirm(self, receipt: str) -> None:
        self.machine.fire("confirm")
        commission = self.amount.times(self.COMMISSION)
        self.breakdown = PaymentBreakdown(commission, self.amount - commission)
        self.receipt = receipt
        self._record("PagoConfirmado", id=self.id, reserva_id=self.reserva_id)
        self._record("ComisionCalculada", commission=str(commission.amount))

    def penalty_for(self, cancellation: Cancellation) -> Penalty | None:
        """BR-0004: 50 % a quien cancela con menos de 4 h."""
        from .specifications import LateCancellation
        if LateCancellation().is_satisfied_by(cancellation):
            cancellation.penalty = Penalty(self.amount.times(self.LATE_PENALTY), cancellation.requester)
        return cancellation.penalty

    def refund(self, amount: Money, reason: str, responsible: str, now=None, evidence: list[str] | None = None) -> None:
        """BR-0017: todo reembolso lleva motivo, evidencia registrada y responsable."""
        if not reason or not responsible:
            raise InvalidTransition("El reembolso requiere motivo y responsable (BR-0017)")
        if not evidence or any(not e.strip() for e in evidence):
            raise InvalidTransition("El reembolso requiere evidencia registrada (BR-0017)")
        self.machine.fire("refund")
        self.refunded, self.refund_reason, self.refund_responsible = amount, reason, responsible
        self.refunded_at = now
        self.refund_evidence = list(evidence)
        self._record("PagoReembolsado", id=self.id, amount=str(amount.amount))

    def settle(self) -> PaymentBreakdown:
        self.machine.fire("settle")
        self._record("PagoLiquidado", id=self.id)
        assert self.breakdown is not None
        return self.breakdown

    def add_extra(self, extra: Money) -> None:
        """BR-0012: cargo proporcional por tiempo extra; la comisión se recalcula sobre el nuevo total."""
        if self.state is not PagoState.CONFIRMADO:
            raise InvalidTransition("Solo un pago confirmado admite cargos extra")
        self.amount = self.amount + extra
        commission = self.amount.times(self.COMMISSION)
        self.breakdown = PaymentBreakdown(commission, self.amount - commission)
        self._record("CargoExtraAplicado", id=self.id, extra=str(extra.amount))
