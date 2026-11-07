from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .errors import RuleViolation
from .events import EventSource
from .value_objects import AccountState, Modality, Schedule


@dataclass
class SubjectAvailability:
    """Entidad interna del Tutor: disponibilidad independiente por materia (BR-0015)."""
    subject: str
    slots: list[Schedule] = field(default_factory=list)
    modalities: list[Modality] = field(default_factory=list)


class Tutor(EventSource):
    """Aggregate root. Protege su suspensión automática (BR-0018)."""

    MAX_ABSENCES = 2
    WINDOW = timedelta(days=30)

    def __init__(self, id: str, name: str = ""):
        self.id, self.name = id, name
        self.state = AccountState.ACTIVO
        self.availability: dict[str, SubjectAvailability] = {}
        self.absences: list[tuple[str, datetime]] = []
        self.rating_sum, self.rating_count = 0, 0

    def set_availability(self, subject: str, slots: list[Schedule], modalities: list[Modality]) -> None:
        if not slots:
            raise RuleViolation("Se requiere al menos una franja de disponibilidad")
        self.availability[subject] = SubjectAvailability(subject, list(slots), list(modalities))
        self._record("DisponibilidadActualizada", tutor_id=self.id, subject=subject)

    def register_absence(self, session_id: str, now: datetime) -> bool:
        """Más de 2 ausencias en 30 días suspende al tutor. Devuelve True si se suspendió ahora."""
        self.absences.append((session_id, now))
        recent = [a for a in self.absences if now - a[1] <= self.WINDOW]
        if len(recent) > self.MAX_ABSENCES and self.state is AccountState.ACTIVO:
            self.state = AccountState.SUSPENDIDO
            self._record("TutorSuspendido", tutor_id=self.id)
            return True
        return False

    def add_rating(self, stars: int) -> None:
        self.rating_sum += stars
        self.rating_count += 1

    @property
    def average_rating(self) -> float:
        return round(self.rating_sum / self.rating_count, 2) if self.rating_count else 0.0

    def reactivate(self, responsible: str) -> None:
        """BR-0018: la suspensión dura hasta la revisión de Administración."""
        if self.state is not AccountState.SUSPENDIDO:
            raise RuleViolation("El tutor no está suspendido")
        self.state = AccountState.ACTIVO
        self.absences = []
        self._record("TutorReactivado", tutor_id=self.id, responsible=responsible)
