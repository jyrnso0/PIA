"""Patrón Specification: reglas de negocio componibles con & (AND), | (OR) y ~ (NOT)."""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Specification(ABC, Generic[T]):
    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool: ...

    def __and__(self, other: "Specification[T]") -> "Specification[T]":
        return _And(self, other)

    def __or__(self, other: "Specification[T]") -> "Specification[T]":
        return _Or(self, other)

    def __invert__(self) -> "Specification[T]":
        return _Not(self)


class _And(Specification):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def is_satisfied_by(self, candidate) -> bool:
        return self.a.is_satisfied_by(candidate) and self.b.is_satisfied_by(candidate)


class _Or(Specification):
    def __init__(self, a, b):
        self.a, self.b = a, b

    def is_satisfied_by(self, candidate) -> bool:
        return self.a.is_satisfied_by(candidate) or self.b.is_satisfied_by(candidate)


class _Not(Specification):
    def __init__(self, a):
        self.a = a

    def is_satisfied_by(self, candidate) -> bool:
        return not self.a.is_satisfied_by(candidate)


# ---- Specifications concretas del negocio AulaPlus ------------------------------------------

class StudentActive(Specification[Any]):
    """El estudiante puede reservar (cuenta activa). Candidato: objeto con `active`."""

    def is_satisfied_by(self, candidate) -> bool:
        return bool(candidate.active)


class TutorActive(Specification[Any]):
    """BR-0018: un tutor suspendido no recibe reservas. Candidato: Tutor."""

    def is_satisfied_by(self, candidate) -> bool:
        return candidate.state.value == "activo"


class TutorOffersSubject(Specification[Any]):
    """BR-0015: el tutor tiene disponibilidad declarada para la materia."""

    def __init__(self, subject: str):
        self.subject = subject

    def is_satisfied_by(self, candidate) -> bool:
        return self.subject in candidate.availability


class SlotWithinAvailability(Specification[Any]):
    """El horario solicitado cae dentro de alguna franja de la materia (BR-0015)."""

    def __init__(self, subject: str, schedule):
        self.subject, self.schedule = subject, schedule

    def is_satisfied_by(self, candidate) -> bool:
        slot = candidate.availability.get(self.subject)
        if slot is None:
            return False
        return any(f.start <= self.schedule.start and self.schedule.end <= f.end for f in slot.slots)


class NoOverlap(Specification[Any]):
    """BR-0006: el horario no traslapa con las sesiones confirmadas. Candidato: lista de Sesion."""

    def __init__(self, schedule):
        self.schedule = schedule

    def is_satisfied_by(self, candidate) -> bool:
        return not any(self.schedule.overlaps(s.schedule) for s in candidate)


class LateCancellation(Specification[Any]):
    """BR-0004: cancelación con menos de 4 h de anticipación. Candidato: Cancellation."""

    def is_satisfied_by(self, candidate) -> bool:
        return candidate.notice < timedelta(hours=4)


class WithinDisputeWindow(Specification[Any]):
    """BR-0007: disputa dentro de 24 h tras el fin de la sesión. Candidato: Sesion."""

    def __init__(self, now: datetime):
        self.now = now

    def is_satisfied_by(self, candidate) -> bool:
        return self.now - candidate.schedule.end <= timedelta(hours=24)


class ReportedAbsence(Specification[Any]):
    """BR-0003: Soporte solo cancela con una situación reportada. Candidato: str|None."""

    def is_satisfied_by(self, candidate) -> bool:
        return bool(candidate)


class ConnectionCounts(Specification[Any]):
    """BR-0010: un corte de conexión cuenta como sesión solo si duró >= 15 min."""

    def is_satisfied_by(self, candidate) -> bool:
        return candidate >= timedelta(minutes=15)


# Composición de ejemplo usada por el servicio de reservas (BR-0006, BR-0015, BR-0018).
def can_receive_booking(subject: str, schedule) -> Specification:
    return TutorActive() & TutorOffersSubject(subject) & SlotWithinAvailability(subject, schedule)
