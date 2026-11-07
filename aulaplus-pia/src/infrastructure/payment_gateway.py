from ..application.ports import PaymentGateway


class FakePaymentGateway(PaymentGateway):
    """Simula al proveedor de cobro (Stripe/Conekta en producción). Rechaza referencias que empiezan con 'FAIL'."""

    def charge(self, reference: str, amount) -> str:
        if reference.upper().startswith("FAIL"):
            from ..domain.errors import RuleViolation
            raise RuleViolation("La pasarela rechazó el cobro")
        return f"RCPT-{reference}"
