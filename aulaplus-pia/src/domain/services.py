"""Servicios de dominio: reglas que no pertenecen a un solo aggregate."""
from abc import ABC, abstractmethod

from .errors import ScheduleUnavailable
from .sesion import Sesion
from .specifications import NoOverlap
from .value_objects import Cancellation, Money, Role, Schedule


class OverlapValidator:
    """BR-0006: un tutor no puede tener dos sesiones confirmadas traslapadas."""

    def ensure_free(self, schedule: Schedule, sessions: list[Sesion]) -> None:
        active = [s for s in sessions if s.state.value in ("programada", "en_curso")]
        if not NoOverlap(schedule).is_satisfied_by(active):
            raise ScheduleUnavailable("El tutor ya tiene una sesión en ese horario (BR-0006)")


class RefundPolicy(ABC):
    """Strategy (SOLID-O): una implementación por causa de reembolso."""

    cause: str

    @abstractmethod
    def amount(self, cancellation: Cancellation | None, paid: Money) -> Money: ...


class TutorAbsenceRefund(RefundPolicy):
    cause = "ausencia_tutor"

    def amount(self, cancellation, paid):  # BR-0009: 100 %
        return paid


class StudentCancellationRefund(RefundPolicy):
    cause = "cancelacion"

    def amount(self, cancellation, paid):
        from .specifications import LateCancellation
        if cancellation and cancellation.requester is Role.STUDENT and LateCancellation().is_satisfied_by(cancellation):
            return paid.times("0.50")  # BR-0004
        return paid


class RefundCalculator:
    def __init__(self, policies: list[RefundPolicy] | None = None):
        policies = policies or [TutorAbsenceRefund(), StudentCancellationRefund()]
        self._by_cause = {p.cause: p for p in policies}

    def amount(self, cause: str, cancellation: Cancellation | None, paid: Money) -> Money:
        if cause not in self._by_cause:
            raise ValueError(f"Causa sin política de reembolso: {cause}")
        return self._by_cause[cause].amount(cancellation, paid)
