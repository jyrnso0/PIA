"""Repositorios SQL: traducen entre filas y aggregates (rehidratación sin ejecutar reglas)."""
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain import repositories as ports
from ..domain.disputa import Disputa
from ..domain.errors import NotFound
from ..domain.estudiante import Estudiante
from ..domain.pago import Pago
from ..domain.reserva import Reserva
from ..domain.sesion import Sesion
from ..domain.tutor import SubjectAvailability, Tutor
from ..domain.value_objects import (
    AccountState,
    Cancellation,
    DisputaState,
    Evidence,
    Modality,
    Money,
    PagoState,
    PaymentBreakdown,
    PaymentDeadline,
    Penalty,
    Rating,
    ReservaState,
    Role,
    Schedule,
    SesionState,
)
from .orm import DisputaRow, EstudianteRow, PagoRow, ReservaRow, SesionRow, TutorRow

ISO = datetime.fromisoformat


class _Base:
    def __init__(self, session: Session, seen: list):
        self.s, self.seen = session, seen

    def _track(self, agg):
        self.seen.append(agg)
        return agg


class SqlEstudianteRepository(_Base, ports.EstudianteRepository):
    def get(self, id):
        r = self.s.get(EstudianteRow, id)
        if not r:
            raise NotFound(f"Estudiante {id} no existe")
        return Estudiante(r.id, r.name, r.active)

    def save(self, e):
        self.s.merge(EstudianteRow(id=e.id, name=e.name, active=e.active))


class SqlTutorRepository(_Base, ports.TutorRepository):
    def get(self, id):
        r = self.s.get(TutorRow, id)
        if not r:
            raise NotFound(f"Tutor {id} no existe")
        t = Tutor(r.id, r.name)
        t.state = AccountState(r.state)
        t.availability = {
            subj: SubjectAvailability(subj, [Schedule(ISO(a), ISO(b)) for a, b in v["slots"]],
                                      [Modality(m) for m in v["modalities"]])
            for subj, v in (r.availability or {}).items()}
        t.absences = [(sid, ISO(ts)) for sid, ts in (r.absences or [])]
        t.rating_sum, t.rating_count = r.rating_sum, r.rating_count
        return self._track(t)

    def all(self):
        return [self.get(r.id) for r in self.s.scalars(select(TutorRow).order_by(TutorRow.id)).all()]

    def save(self, t):
        self._track(t)
        self.s.merge(TutorRow(
            id=t.id, name=t.name, state=t.state.value,
            availability={k: {"slots": [[x.start.isoformat(), x.end.isoformat()] for x in v.slots],
                              "modalities": [m.value for m in v.modalities]} for k, v in t.availability.items()},
            absences=[[sid, ts.isoformat()] for sid, ts in t.absences],
            rating_sum=t.rating_sum, rating_count=t.rating_count))


class SqlReservaRepository(_Base, ports.ReservaRepository):
    @staticmethod
    def _build(r: ReservaRow) -> Reserva:
        res = Reserva(r.tutor_id, r.student_id, r.subject, Modality(r.modality), Schedule(r.start, r.end),
                      Money(r.amount), r.expires_at - timedelta(minutes=Reserva.PAYMENT_MINUTES), id=r.id, topic=r.topic or "")
        res.deadline = PaymentDeadline(r.expires_at)
        res.machine.restore(ReservaState(r.state))
        res.pull_events()
        return res

    def get(self, id):
        r = self.s.get(ReservaRow, id)
        if not r:
            raise NotFound(f"Reserva {id} no existe")
        return self._track(self._build(r))

    def save(self, x):
        self._track(x)
        self.s.merge(ReservaRow(id=x.id, tutor_id=x.tutor_id, student_id=x.student_id, subject=x.subject, topic=x.topic,
                                modality=x.modality.value, start=x.schedule.start, end=x.schedule.end,
                                amount=x.amount.amount, expires_at=x.deadline.expires_at, state=x.state.value))

    def pending_expired(self, now):
        rows = self.s.scalars(select(ReservaRow).where(ReservaRow.state == "pendiente",
                                                       ReservaRow.expires_at < now)).all()
        return [self._track(self._build(r)) for r in rows]


class SqlSesionRepository(_Base, ports.SesionRepository):
    @staticmethod
    def _build(r: SesionRow) -> Sesion:
        s = Sesion(r.reserva_id, r.tutor_id, r.student_id, Schedule(r.start, r.end), id=r.id,
                   modality=Modality(r.modality), hourly_rate=Money(r.hourly_rate))
        s.presence = {k: ISO(v) for k, v in (r.presence or {}).items()}
        s.pending_extension, s.pending_modality = r.pending_extension, r.pending_modality
        s.machine.restore(SesionState(r.state))
        s.checklist = {k: ISO(v) for k, v in (r.checklist or {}).items()}
        s.ratings = {k: Rating(Role(k), v["stars"], v.get("comment", ""), v.get("reported", False)) for k, v in (r.ratings or {}).items()}
        c = r.cancellation
        if c:
            s.cancellation = Cancellation(Role(c["requester"]), timedelta(seconds=c["notice_s"]),
                                          Penalty(Money(c["penalty"]), Role(c["requester"])) if c.get("penalty") else None)
        s.started_at, s.finished_at = r.started_at, r.finished_at
        s.pull_events()
        return s

    def get(self, id):
        r = self.s.get(SesionRow, id)
        if not r:
            raise NotFound(f"Sesión {id} no existe")
        return self._track(self._build(r))

    def by_reserva(self, reserva_id):
        r = self.s.scalars(select(SesionRow).where(SesionRow.reserva_id == reserva_id)).first()
        if not r:
            raise NotFound(f"No hay sesión para la reserva {reserva_id}")
        return self._track(self._build(r))

    def save(self, x):
        self._track(x)
        c = x.cancellation
        self.s.merge(SesionRow(
            id=x.id, reserva_id=x.reserva_id, tutor_id=x.tutor_id, student_id=x.student_id,
            start=x.schedule.start, end=x.schedule.end, state=x.state.value,
            checklist={k: v.isoformat() for k, v in x.checklist.items()},
            ratings={k: {"stars": v.stars, "comment": v.comment, "reported": v.reported} for k, v in x.ratings.items()},
            modality=x.modality.value, hourly_rate=x.hourly_rate.amount,
            presence={k: v.isoformat() for k, v in x.presence.items()},
            pending_extension=x.pending_extension, pending_modality=x.pending_modality,
            cancellation=None if not c else {"requester": c.requester.value, "notice_s": c.notice.total_seconds(),
                                             "penalty": str(c.penalty.amount.amount) if c.penalty else None},
            started_at=x.started_at, finished_at=x.finished_at))

    def by_tutor(self, tutor_id):
        rows = self.s.scalars(select(SesionRow).where(SesionRow.tutor_id == tutor_id)).all()
        return [self._build(r) for r in rows]

    def recently_finished(self, since):
        rows = self.s.scalars(select(SesionRow).where(SesionRow.end >= since,
                                                      SesionRow.state.in_(["realizada", "cerrada"]))).all()
        return [self._build(r) for r in rows]

    def overdue_for_close(self, now):
        rows = self.s.scalars(select(SesionRow).where(SesionRow.state == "realizada")).all()
        return [self._track(self._build(r)) for r in rows]


class SqlPagoRepository(_Base, ports.PagoRepository):
    def by_reserva(self, reserva_id):
        r = self.s.scalars(select(PagoRow).where(PagoRow.reserva_id == reserva_id)).first()
        if not r:
            raise NotFound(f"No hay pago para la reserva {reserva_id}")
        p = Pago(r.reserva_id, Money(r.amount), id=r.id)
        p.machine.restore(PagoState(r.state))
        if r.commission is not None:
            p.breakdown = PaymentBreakdown(Money(r.commission), Money(r.tutor_share))
        p.receipt, p.refunded = r.receipt, Money(r.refunded or 0)
        p.refund_reason, p.refund_responsible, p.refunded_at = r.refund_reason, r.refund_responsible, r.refunded_at
        p.refund_evidence = list(r.refund_evidence or [])
        return self._track(p)

    def __init__(self, session, seen, clock=datetime.utcnow):
        super().__init__(session, seen)
        self._clock = clock

    def save(self, p):
        self._track(p)
        self.s.merge(PagoRow(
            id=p.id, reserva_id=p.reserva_id, amount=p.amount.amount, state=p.state.value,
            commission=p.breakdown.commission.amount if p.breakdown else None,
            tutor_share=p.breakdown.tutor_share.amount if p.breakdown else None,
            receipt=p.receipt, refunded=p.refunded.amount, refund_reason=p.refund_reason,
            refund_responsible=p.refund_responsible, refunded_at=p.refunded_at,
            refund_evidence=p.refund_evidence, updated_at=self._clock()))


class SqlDisputaRepository(_Base, ports.DisputaRepository):
    def get(self, id):
        r = self.s.get(DisputaRow, id)
        if not r:
            raise NotFound(f"Disputa {id} no existe")
        d = Disputa(r.session_id, Role(r.party), r.opened_at, id=r.id)
        d.machine.restore(DisputaState(r.state))
        d.evidence = [Evidence(e["reference"], e.get("author", "")) for e in (r.evidence or [])]
        d.decision, d.responsible = r.decision, r.responsible
        d.pull_events()
        return self._track(d)

    def unresolved(self):
        rows = self.s.scalars(select(DisputaRow).where(DisputaRow.state != "resuelta")).all()
        return [self.get(r.id) for r in rows]

    def has_open_for_session(self, session_id):
        return self.s.scalars(select(DisputaRow.id).where(DisputaRow.session_id == session_id,
                                                          DisputaRow.state != "resuelta")).first() is not None

    def save(self, d):
        self._track(d)
        self.s.merge(DisputaRow(id=d.id, session_id=d.session_id, party=d.party.value, opened_at=d.opened_at,
                                state=d.state.value,
                                evidence=[{"reference": e.reference, "author": e.author} for e in d.evidence],
                                decision=d.decision, responsible=d.responsible))
