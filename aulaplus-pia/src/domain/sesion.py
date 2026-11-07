from datetime import datetime, timedelta
from uuid import uuid4

from .errors import InvalidTransition, RuleViolation
from .events import EventSource
from .specifications import ConnectionCounts, ReportedAbsence
from .state_machine import StateMachine
from .value_objects import Cancellation, Modality, Money, Rating, Role, Schedule, SesionState

S = SesionState
_TABLE = {
    S.PROGRAMADA: {"start": S.EN_CURSO, "cancel": S.CANCELADA,
                   "tutor_absent": S.AUSENCIA_TUTOR, "student_absent": S.AUSENCIA_ESTUDIANTE},
    S.EN_CURSO: {"finish": S.REALIZADA, "cut_counts": S.REALIZADA, "cut_short": S.INTERRUMPIDA},
    S.REALIZADA: {"close": S.CERRADA},
}
PARTIES = {Role.STUDENT.value, Role.TUTOR.value}


class Sesion(EventSource):
    """Aggregate root. Nace al confirmarse el pago de una Reserva."""

    AUTO_CLOSE = timedelta(hours=48)            # BR-0002
    MODALITY_NOTICE = timedelta(hours=1)        # BR-0013

    def __init__(self, reserva_id: str, tutor_id: str, student_id: str, schedule: Schedule, id: str | None = None,
                 modality: Modality = Modality.VIRTUAL, hourly_rate: Money | None = None):
        self.id = id or str(uuid4())
        self.reserva_id, self.tutor_id, self.student_id = reserva_id, tutor_id, student_id
        self.schedule, self.modality = schedule, modality
        self.hourly_rate = hourly_rate or Money(0)
        self.machine = StateMachine("Sesion", S.PROGRAMADA, _TABLE)
        self.checklist: dict[str, datetime] = {}      # BR-0014: parte -> timestamp
        self.presence: dict[str, datetime] = {}       # BR-0008: presencia confirmada antes de la sesión
        self.ratings: dict[str, Rating] = {}          # BR-0002
        self.cancellation: Cancellation | None = None
        self.started_at: datetime | None = None
        self.finished_at: datetime | None = None
        self.pending_extension: dict | None = None    # BR-0012
        self.pending_modality: dict | None = None     # BR-0013
        self._record("SesionProgramada", id=self.id, reserva_id=reserva_id)

    @property
    def state(self) -> SesionState:
        return self.machine.state

    # ---- ciclo de vida ----
    def start(self, now: datetime) -> None:
        self.machine.fire("start")
        self.started_at = now

    def confirm_presence(self, party: Role, now: datetime) -> None:
        """BR-0008: el tutor confirma su presencia en el sistema."""
        if self.state is not S.PROGRAMADA and self.state is not S.EN_CURSO:
            raise InvalidTransition("La presencia se confirma antes o durante la sesión")
        self._ensure_party(party)
        self.presence[party.value] = now

    def confirm_checklist(self, party: Role, now: datetime) -> None:
        if self.state is not S.EN_CURSO:
            raise InvalidTransition("El checklist se confirma durante la sesión")
        self._ensure_party(party)
        self.checklist[party.value] = now

    def finish(self, now: datetime) -> None:
        """BR-0014: no se da por realizada sin checklist de ambas partes."""
        if self.state is not S.EN_CURSO:
            raise InvalidTransition("Solo una sesión en curso puede finalizar")
        if not PARTIES <= set(self.checklist):
            raise RuleViolation("Falta el checklist de una de las partes (BR-0014)")
        self.machine.fire("finish")
        self.finished_at = now
        self._record("SesionRealizada", id=self.id)

    def connection_cut(self, duration: timedelta, now: datetime) -> bool:
        """BR-0010: con ≥ 15 min la sesión cuenta como realizada; con menos, queda interrumpida."""
        counts = ConnectionCounts().is_satisfied_by(duration)
        self.machine.fire("cut_counts" if counts else "cut_short")
        self.finished_at = now
        self._record("SesionRealizada" if counts else "SesionInterrumpida", id=self.id)
        return counts

    def cancel(self, requester: Role, now: datetime, reported_situation: str | None = None) -> Cancellation:
        """BR-0003: estudiante o tutor cancelan; Soporte solo con situación reportada."""
        if requester is Role.SUPPORT and not ReportedAbsence().is_satisfied_by(reported_situation):
            raise RuleViolation("Soporte solo cancela con una situación reportada (BR-0003)")
        self.machine.fire("cancel")
        self.cancellation = Cancellation(requester, self.schedule.start - now)
        self._record("SesionCancelada", id=self.id, requester=requester.value)
        return self.cancellation

    def mark_tutor_absent(self) -> None:
        self.machine.fire("tutor_absent")
        self._record("TutorAusente", id=self.id, tutor_id=self.tutor_id)

    def mark_student_absent(self) -> None:
        """BR-0008: solo se cobra si el tutor confirmó su presencia en el sistema."""
        if Role.TUTOR.value not in self.presence:
            raise RuleViolation("El tutor debe confirmar su presencia para registrar la ausencia (BR-0008)")
        self.machine.fire("student_absent")
        self._record("EstudianteAusente", id=self.id)

    # ---- BR-0012: extensión ----
    def propose_extension(self, by: Role, minutes: int) -> None:
        if self.state is not S.EN_CURSO:
            raise InvalidTransition("Solo se extiende una sesión en curso (BR-0012)")
        self._ensure_party(by)
        if minutes <= 0:
            raise RuleViolation("La extensión debe ser de al menos 1 minuto")
        self.pending_extension = {"minutes": minutes, "by": by.value, "accepted": [by.value]}
        self._record("ExtensionSolicitada", id=self.id, minutes=minutes)

    def accept_extension(self, by: Role) -> Money | None:
        """Devuelve el cargo extra si ambas partes ya aceptaron; None si falta la otra parte."""
        if not self.pending_extension:
            raise InvalidTransition("No hay extensión solicitada")
        self._ensure_party(by)
        if by.value not in self.pending_extension["accepted"]:
            self.pending_extension["accepted"].append(by.value)
        if not PARTIES <= set(self.pending_extension["accepted"]):
            return None
        minutes = self.pending_extension["minutes"]
        self.schedule = Schedule(self.schedule.start, self.schedule.end + timedelta(minutes=minutes))
        self.pending_extension = None
        extra = Money(self.hourly_rate.amount * minutes / 60)
        self._record("SesionExtendida", id=self.id, minutes=minutes, extra=str(extra.amount))
        return extra

    # ---- BR-0013: cambio de modalidad ----
    def propose_modality_change(self, by: Role, new: Modality, now: datetime) -> None:
        if self.state is not S.PROGRAMADA:
            raise InvalidTransition("Solo se cambia la modalidad de una sesión programada")
        self._ensure_party(by)
        self._ensure_modality_notice(now)
        if new is self.modality:
            raise RuleViolation("La sesión ya tiene esa modalidad")
        self.pending_modality = {"modality": new.value, "by": by.value, "accepted": [by.value]}
        self._record("CambioModalidadSolicitado", id=self.id, modality=new.value)

    def accept_modality_change(self, by: Role, now: datetime) -> bool:
        if not self.pending_modality:
            raise InvalidTransition("No hay cambio de modalidad solicitado")
        self._ensure_party(by)
        self._ensure_modality_notice(now)
        if by.value not in self.pending_modality["accepted"]:
            self.pending_modality["accepted"].append(by.value)
        if not PARTIES <= set(self.pending_modality["accepted"]):
            return False
        self.modality = Modality(self.pending_modality["modality"])
        self.pending_modality = None
        self._record("ModalidadCambiada", id=self.id, modality=self.modality.value)
        return True

    def _ensure_modality_notice(self, now: datetime) -> None:
        if self.schedule.start - now < self.MODALITY_NOTICE:
            raise RuleViolation("El cambio de modalidad requiere al menos 1 hora de anticipación (BR-0013)")

    # ---- calificación y cierre ----
    def rate(self, rating: Rating, now: datetime) -> None:
        if self.state is not S.REALIZADA:
            raise InvalidTransition("Solo se califica una sesión realizada")
        self._ensure_party(rating.by)
        self.ratings[rating.by.value] = rating
        if PARTIES <= set(self.ratings):
            self.close(now)                               # BR-0002: ambos calificaron

    def report_comment(self, author: Role) -> None:
        """BR-0016: marca como inapropiado el comentario que dejó `author`."""
        from dataclasses import replace
        r = self.ratings.get(author.value)
        if r is None or not r.comment:
            raise RuleViolation("No hay comentario que reportar")
        self.ratings[author.value] = replace(r, reported=True)
        self._record("ComentarioReportado", id=self.id, author=author.value)

    def close_if_overdue(self, now: datetime) -> bool:
        if self.state is S.REALIZADA and self.finished_at and now - self.finished_at >= self.AUTO_CLOSE:
            self.close(now)
            return True
        return False

    def close(self, now: datetime) -> None:
        self.machine.fire("close")
        self._record("SesionCerrada", id=self.id)

    @staticmethod
    def connection_cut_counts(duration: timedelta) -> bool:
        return ConnectionCounts().is_satisfied_by(duration)

    @staticmethod
    def _ensure_party(party: Role) -> None:
        if party.value not in PARTIES:
            raise RuleViolation("Solo estudiante o tutor participan en la sesión")
