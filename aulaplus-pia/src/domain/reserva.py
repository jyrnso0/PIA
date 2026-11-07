from datetime import datetime, timedelta
from uuid import uuid4

from .errors import DeadlineExpired
from .events import EventSource
from .state_machine import StateMachine
from .value_objects import Modality, Money, PaymentDeadline, ReservaState, Schedule

_TABLE = {
    ReservaState.PENDIENTE: {"pay": ReservaState.CONFIRMADA, "expire": ReservaState.LIBERADA},
    ReservaState.CONFIRMADA: {"cancel": ReservaState.CANCELADA},
}


class Reserva(EventSource):
    """Aggregate root. Controla el plazo de pago de 15 minutos (BR-0001)."""

    PAYMENT_MINUTES = 15

    def __init__(self, tutor_id: str, student_id: str, subject: str, modality: Modality,
                 schedule: Schedule, amount: Money, now: datetime, id: str | None = None, topic: str = ""):
        self.id = id or str(uuid4())
        self.tutor_id, self.student_id = tutor_id, student_id
        self.subject, self.modality, self.topic = subject, modality, topic
        self.schedule, self.amount = schedule, amount
        self.deadline = PaymentDeadline(now + timedelta(minutes=self.PAYMENT_MINUTES))
        self.machine = StateMachine("Reserva", ReservaState.PENDIENTE, _TABLE)
        self._record("ReservaCreada", id=self.id, expires_at=self.deadline.expires_at.isoformat())

    @property
    def state(self) -> ReservaState:
        return self.machine.state

    def confirm_payment(self, now: datetime) -> None:
        if self.deadline.expired(now):
            raise DeadlineExpired("El plazo de 15 minutos venció (BR-0001)")
        self.machine.fire("pay")
        self._record("ReservaConfirmada", id=self.id)

    def release_if_expired(self, now: datetime) -> bool:
        if self.state is ReservaState.PENDIENTE and self.deadline.expired(now):
            self.machine.fire("expire")
            self._record("ReservaLiberada", id=self.id)
            return True
        return False

    def cancel(self) -> None:
        self.machine.fire("cancel")
        self._record("ReservaCancelada", id=self.id)
