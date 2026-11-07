"""Application Services (Service Layer). Orquestan casos de uso; las reglas viven en el dominio."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from ..domain.disputa import Disputa
from ..domain.errors import DeadlineExpired, RuleViolation, ScheduleUnavailable
from ..domain.estudiante import Estudiante
from ..domain.pago import Pago
from ..domain.reserva import Reserva
from ..domain.services import OverlapValidator, RefundCalculator
from ..domain.sesion import Sesion
from ..domain.specifications import StudentActive, WithinDisputeWindow, can_receive_booking
from ..domain.tutor import Tutor
from ..domain.value_objects import Modality, Money, Rating, Role, Schedule
from .ports import Clock, DashboardReadModel, PaymentGateway, UnitOfWork


def _m(value) -> str:
    """Los importes salen como texto con 2 decimales (sin pérdida de precisión en JSON)."""
    return format(Decimal(value), ".2f")


class TutorService:
    def __init__(self, uow: UnitOfWork, clock: Clock | None = None):
        self._uow = uow
        self._clock = clock or datetime.utcnow

    def register(self, tutor_id: str, name: str) -> dict:
        with self._uow as uow:
            uow.tutores.save(Tutor(tutor_id, name))
            uow.commit()
        return {"id": tutor_id, "name": name, "state": "activo"}

    def register_student(self, student_id: str, name: str, active: bool = True) -> dict:
        with self._uow as uow:
            uow.estudiantes.save(Estudiante(student_id, name, active))
            uow.commit()
        return {"id": student_id, "name": name, "active": active}

    def set_availability(self, tutor_id: str, subject: str, slots: list[Schedule], modalities: list[Modality]) -> dict:
        with self._uow as uow:
            tutor = uow.tutores.get(tutor_id)
            tutor.set_availability(subject, slots, modalities)  # BR-0015: independiente por materia
            uow.tutores.save(tutor)
            uow.commit()
        return {"tutor_id": tutor_id, "subject": subject, "slots": len(slots)}

    def public_profile(self, tutor_id: str) -> dict:
        """BR-0016: promedio público y comentarios no reportados. Sin estado de cuenta, ausencias ni pagos."""
        with self._uow as uow:
            t = uow.tutores.get(tutor_id)
            comments = [{"session_id": s.id, "comment": r.comment, "stars": r.stars}
                        for s in uow.sesiones.by_tutor(tutor_id)
                        for r in s.ratings.values()
                        if r.by is Role.STUDENT and r.comment and not r.reported]
            return {"id": t.id, "name": t.name, "subjects": sorted(t.availability),
                    "average_rating": t.average_rating, "rating_count": t.rating_count, "comments": comments}

    def status(self, tutor_id: str) -> dict:
        """Vista interna (Administración): estado de cuenta y ausencias."""
        with self._uow as uow:
            t = uow.tutores.get(tutor_id)
            return {"id": t.id, "state": t.state.value, "absences": len(t.absences)}

    def reactivate(self, tutor_id: str, responsible: str) -> dict:
        """BR-0018: la suspensión se levanta tras revisión de Administración."""
        with self._uow as uow:
            t = uow.tutores.get(tutor_id)
            t.reactivate(responsible)
            uow.tutores.save(t)
            uow.commit()
            return {"id": t.id, "state": t.state.value}


class BookingService:
    def __init__(self, uow: UnitOfWork, gateway: PaymentGateway, clock: Clock):
        self._uow, self._gateway, self._clock = uow, gateway, clock
        self._overlap = OverlapValidator()

    def reserve(self, student_id: str, tutor_id: str | None, subject: str, modality: Modality,
                schedule: Schedule, amount: Decimal, topic: str = "") -> dict:
        """CU-01a. Si no se indica tutor, la plataforma lo asigna según su disponibilidad (glosario: Asignación)."""
        now = self._clock()
        with self._uow as uow:
            student = uow.estudiantes.get(student_id)
            if not StudentActive().is_satisfied_by(student):
                raise RuleViolation("La cuenta del estudiante no está activa")
            if tutor_id:
                tutor = uow.tutores.get(tutor_id)
                if not can_receive_booking(subject, schedule).is_satisfied_by(tutor):
                    raise RuleViolation("El tutor no está activo o no tiene disponibilidad para esa materia/horario")
                if modality not in tutor.availability[subject].modalities:
                    raise RuleViolation("El tutor no ofrece esa modalidad para la materia")
                self._overlap.ensure_free(schedule, uow.sesiones.by_tutor(tutor_id))  # BR-0006
            else:
                tutor = self._assign(uow, subject, modality, schedule)
            reserva = Reserva(tutor.id, student_id, subject, modality, schedule, Money(amount), now, topic=topic)
            uow.reservas.save(reserva)
            uow.commit()
            return self._dto(reserva)

    def _assign(self, uow: UnitOfWork, subject: str, modality: Modality, schedule: Schedule) -> Tutor:
        spec = can_receive_booking(subject, schedule)
        for tutor in uow.tutores.all():
            if not spec.is_satisfied_by(tutor) or modality not in tutor.availability[subject].modalities:
                continue
            try:
                self._overlap.ensure_free(schedule, uow.sesiones.by_tutor(tutor.id))
            except ScheduleUnavailable:
                continue
            return tutor
        raise ScheduleUnavailable("No hay tutor disponible para esa materia, modalidad y horario")

    def pay(self, reserva_id: str, reference: str, amount: Decimal) -> dict:
        """CU-01b: cobra, confirma, registra pago y programa la sesión en una transacción."""
        now = self._clock()
        with self._uow as uow:
            reserva = uow.reservas.get(reserva_id)
            reserva.confirm_payment(now)  # DeadlineExpired / InvalidTransition
            if Money(amount) != reserva.amount:
                raise RuleViolation("El importe no coincide con el de la reserva")
            self._overlap.ensure_free(reserva.schedule, uow.sesiones.by_tutor(reserva.tutor_id))  # BR-0006
            receipt = self._gateway.charge(reference, reserva.amount)
            pago = Pago(reserva.id, reserva.amount)
            pago.confirm(receipt)
            hours = Decimal((reserva.schedule.end - reserva.schedule.start).total_seconds()) / Decimal(3600)
            sesion = Sesion(reserva.id, reserva.tutor_id, reserva.student_id, reserva.schedule,
                            modality=reserva.modality, hourly_rate=Money(reserva.amount.amount / hours))
            uow.reservas.save(reserva)
            uow.pagos.save(pago)
            uow.sesiones.save(sesion)
            uow.commit()
            return self._dto(reserva, sesion.id, pago)

    def release_expired(self) -> int:
        """CU-01c: libera horarios con plazo vencido (BR-0001)."""
        now = self._clock()
        n = 0
        with self._uow as uow:
            for r in uow.reservas.pending_expired(now):
                if r.release_if_expired(now):
                    uow.reservas.save(r)
                    n += 1
            uow.commit()
        return n

    def get(self, reserva_id: str) -> dict:
        with self._uow as uow:
            return self._dto(uow.reservas.get(reserva_id))

    @staticmethod
    def _dto(r: Reserva, session_id: str | None = None, pago: Pago | None = None) -> dict:
        out: dict[str, Any] = {"id": r.id, "state": r.state.value, "amount": _m(r.amount.amount),
                               "expires_at": r.deadline.expires_at, "tutor_id": r.tutor_id,
                               "student_id": r.student_id, "subject": r.subject, "topic": r.topic,
                               "modality": r.modality.value, "session_id": session_id}
        if pago and pago.breakdown:
            out["commission"] = _m(pago.breakdown.commission.amount)
            out["tutor_share"] = _m(pago.breakdown.tutor_share.amount)
        return out


class SessionService:
    def __init__(self, uow: UnitOfWork, clock: Clock, refunds: RefundCalculator | None = None):
        self._uow, self._clock = uow, clock
        self._refunds = refunds or RefundCalculator()
        self._overlap = OverlapValidator()

    @staticmethod
    def _dto(s: Sesion, **extra) -> dict:
        return {"id": s.id, "state": s.state.value, "tutor_id": s.tutor_id, "student_id": s.student_id,
                "modality": s.modality.value, "starts_at": s.schedule.start, "ends_at": s.schedule.end,
                "started_at": s.started_at, "finished_at": s.finished_at,
                "checklist": {k: v for k, v in s.checklist.items()}, **extra}

    def get(self, session_id: str) -> dict:
        with self._uow as uow:
            return self._dto(uow.sesiones.get(session_id))

    def _apply(self, session_id: str, action) -> dict:
        with self._uow as uow:
            s = uow.sesiones.get(session_id)
            extra = action(uow, s) or {}
            uow.sesiones.save(s)
            uow.commit()
            return self._dto(s, **extra)

    def start(self, session_id: str) -> dict:
        return self._apply(session_id, lambda uow, s: s.start(self._clock()))

    def confirm_presence(self, session_id: str, party: Role) -> dict:
        return self._apply(session_id, lambda uow, s: s.confirm_presence(party, self._clock()))

    def confirm_checklist(self, session_id: str, party: Role) -> dict:
        return self._apply(session_id, lambda uow, s: s.confirm_checklist(party, self._clock()))

    def finish(self, session_id: str) -> dict:
        return self._apply(session_id, lambda uow, s: s.finish(self._clock()))

    def connection_cut(self, session_id: str, minutes: int) -> dict:
        """BR-0010."""
        def act(uow, s):
            counts = s.connection_cut(timedelta(minutes=minutes), self._clock())
            return {"counts_as_completed": counts}
        return self._apply(session_id, act)

    def cancel(self, session_id: str, requester: Role, reported_situation: str | None = None,
               responsible: str = "sistema") -> dict:
        """CU-03 (BR-0003, BR-0004, BR-0017)."""
        now = self._clock()

        def act(uow, s):
            cancellation = s.cancel(requester, now, reported_situation)
            pago = uow.pagos.by_reserva(s.reserva_id)
            pago.penalty_for(cancellation)
            refund = self._refunds.amount("cancelacion", cancellation, pago.amount)
            evidence = [f"session:{s.id}:cancellation"] + ([f"situation:{reported_situation}"] if reported_situation else [])
            pago.refund(refund, "cancelacion", responsible if requester is Role.SUPPORT else requester.value, now, evidence)
            reserva = uow.reservas.get(s.reserva_id)
            reserva.cancel()
            uow.reservas.save(reserva)
            uow.pagos.save(pago)
            return {"late": cancellation.penalty is not None,
                    "penalty": _m(cancellation.penalty.amount.amount if cancellation.penalty else Decimal("0")),
                    "refund": _m(refund.amount)}
        return self._apply(session_id, act)

    def report_tutor_absence(self, session_id: str, responsible: str) -> dict:
        """BR-0009 y BR-0018: reembolso 100 %, falta al tutor y posible suspensión."""
        now = self._clock()

        def act(uow, s):
            s.mark_tutor_absent()
            pago = uow.pagos.by_reserva(s.reserva_id)
            refund = self._refunds.amount("ausencia_tutor", None, pago.amount)
            pago.refund(refund, "ausencia_tutor", responsible, now, [f"session:{s.id}:tutor-absence"])
            tutor = uow.tutores.get(s.tutor_id)
            suspended = tutor.register_absence(s.id, now)
            uow.pagos.save(pago)
            uow.tutores.save(tutor)
            return {"refund": _m(refund.amount), "tutor_suspended": suspended}
        return self._apply(session_id, act)

    def report_student_absence(self, session_id: str) -> dict:
        """BR-0008: cobro del 100 % si el tutor confirmó su presencia en el sistema."""
        def act(uow, s):
            s.mark_student_absent()
            pago = uow.pagos.by_reserva(s.reserva_id)
            breakdown = pago.settle()
            uow.pagos.save(pago)
            return {"charged": _m(pago.amount.amount), "tutor_share": _m(breakdown.tutor_share.amount)}
        return self._apply(session_id, act)

    # ---- BR-0012 ----
    def propose_extension(self, session_id: str, by: Role, minutes: int) -> dict:
        return self._apply(session_id, lambda uow, s: s.propose_extension(by, minutes) or {"pending": True})

    def accept_extension(self, session_id: str, by: Role) -> dict:
        def act(uow, s):
            extra = s.accept_extension(by)
            if extra is None:
                return {"extended": False}
            others = [o for o in uow.sesiones.by_tutor(s.tutor_id) if o.id != s.id]
            self._overlap.ensure_free(s.schedule, others)          # BR-0006 sobre el nuevo horario
            pago = uow.pagos.by_reserva(s.reserva_id)
            pago.add_extra(extra)
            uow.pagos.save(pago)
            return {"extended": True, "extra_charge": _m(extra.amount), "new_total": _m(pago.amount.amount)}
        return self._apply(session_id, act)

    # ---- BR-0013 ----
    def propose_modality(self, session_id: str, by: Role, modality: Modality) -> dict:
        return self._apply(session_id, lambda uow, s: s.propose_modality_change(by, modality, self._clock())
                           or {"pending": True})

    def accept_modality(self, session_id: str, by: Role) -> dict:
        return self._apply(session_id, lambda uow, s: {"changed": s.accept_modality_change(by, self._clock())})

    # ---- Calificación (BR-0002, BR-0016) ----
    def rate(self, session_id: str, by: Role, stars: int, comment: str = "") -> dict:
        now = self._clock()

        def act(uow, s):
            try:
                rating = Rating(by, stars, comment)
            except ValueError as e:
                raise RuleViolation(str(e)) from e
            s.rate(rating, now)
            if by is Role.STUDENT:  # el promedio público es el que dan los estudiantes al tutor
                tutor = uow.tutores.get(s.tutor_id)
                tutor.add_rating(stars)
                uow.tutores.save(tutor)
            self._settle_if_closed(uow, s)
        return self._apply(session_id, act)

    def report_comment(self, session_id: str, author: Role) -> dict:
        return self._apply(session_id, lambda uow, s: s.report_comment(author) or {"reported": True})

    def close_overdue(self) -> int:
        """BR-0002: cierre automático a las 48 h si nadie levantó disputa."""
        now = self._clock()
        n = 0
        with self._uow as uow:
            for s in uow.sesiones.overdue_for_close(now):
                if uow.disputas.has_open_for_session(s.id):
                    continue
                if s.close_if_overdue(now):
                    self._settle_if_closed(uow, s)
                    uow.sesiones.save(s)
                    n += 1
            uow.commit()
        return n

    @staticmethod
    def _settle_if_closed(uow, s: Sesion) -> None:
        if s.state.value == "cerrada":
            pago = uow.pagos.by_reserva(s.reserva_id)
            if pago.state.value == "confirmado":
                pago.settle()
                uow.pagos.save(pago)


class DisputeService:
    def __init__(self, uow: UnitOfWork, clock: Clock):
        self._uow, self._clock = uow, clock

    def _dto(self, d: Disputa) -> dict:
        return {"id": d.id, "session_id": d.session_id, "state": d.state.value, "due_at": d.due_at,
                "overdue": d.overdue(self._clock()), "evidence": [e.reference for e in d.evidence],
                "decision": d.decision, "responsible": d.responsible}

    def report(self, session_id: str, party: Role) -> dict:
        """CU-04a: ventana de 24 h tras el fin de la sesión (BR-0007)."""
        now = self._clock()
        with self._uow as uow:
            s = uow.sesiones.get(session_id)
            if not WithinDisputeWindow(now).is_satisfied_by(s):
                raise DeadlineExpired("La ventana de 24 horas para disputar terminó (BR-0007)")
            d = Disputa(session_id, party, now)
            uow.disputas.save(d)
            uow.commit()
            return self._dto(d)

    def _mutate(self, dispute_id: str, action) -> dict:
        with self._uow as uow:
            d = uow.disputas.get(dispute_id)
            action(uow, d)
            uow.disputas.save(d)
            uow.commit()
            return self._dto(d)

    def attach_evidence(self, dispute_id: str, reference: str, author: str = "") -> dict:
        return self._mutate(dispute_id, lambda uow, d: d.attach_evidence(reference, author))

    def escalate(self, dispute_id: str) -> dict:
        """BR-0011: versiones distintas de ambas partes se envían a Soporte."""
        return self._mutate(dispute_id, lambda uow, d: d.escalate())

    def resolve(self, dispute_id: str, responsible: str, decision: str, refund_percent: int = 0) -> dict:
        """BR-0020 y BR-0017: resolución con evidencia y, si procede, reembolso con responsable."""
        now = self._clock()

        def act(uow, d):
            d.resolve(decision, responsible)
            if refund_percent:
                if not 0 < refund_percent <= 100:
                    raise RuleViolation("El porcentaje de reembolso debe estar entre 1 y 100")
                s = uow.sesiones.get(d.session_id)
                pago = uow.pagos.by_reserva(s.reserva_id)
                pago.refund(pago.amount.times(Decimal(refund_percent) / 100), "disputa", responsible, now,
                            [e.reference for e in d.evidence])
                uow.pagos.save(pago)
        return self._mutate(dispute_id, act)

    def get(self, dispute_id: str) -> dict:
        with self._uow as uow:
            return self._dto(uow.disputas.get(dispute_id))

    def overdue(self) -> list[dict]:
        now = self._clock()
        with self._uow as uow:
            return [self._dto(d) for d in uow.disputas.unresolved() if d.overdue(now)]


class NotificationService:
    """RNF Notificaciones: lista avisos próximos a vencer (pago, disputa, SLA de Soporte)."""

    PAYMENT_WARN = timedelta(minutes=5)
    DISPUTE_WARN = timedelta(hours=2)
    SLA_WARN = timedelta(hours=12)

    def __init__(self, uow: UnitOfWork, clock: Clock):
        self._uow, self._clock = uow, clock

    def upcoming(self) -> list[dict]:
        now = self._clock()
        out: list[dict] = []
        with self._uow as uow:
            for r in uow.reservas.pending_expired(now + self.PAYMENT_WARN):
                left = r.deadline.expires_at - now
                if timedelta(0) <= left <= self.PAYMENT_WARN:
                    out.append({"type": "PAGO_POR_VENCER", "target": r.id, "to": r.student_id,
                                "minutes_left": int(left.total_seconds() // 60)})
            for s in uow.sesiones.recently_finished(now - timedelta(hours=24) - self.DISPUTE_WARN):
                end = s.schedule.end + timedelta(hours=24)
                if timedelta(0) <= end - now <= self.DISPUTE_WARN:
                    out.append({"type": "DISPUTA_POR_VENCER", "target": s.id, "to": s.student_id})
            for d in uow.disputas.unresolved():
                if timedelta(0) <= d.due_at - now <= self.SLA_WARN:
                    out.append({"type": "SLA_SOPORTE_POR_VENCER", "target": d.id, "to": "soporte"})
        return out


class DashboardService:
    """BR-0019: consulta (CQRS-light) sobre un read model, sin pasar por los aggregates."""

    def __init__(self, read_model: DashboardReadModel, clock: Clock):
        self._rm, self._clock = read_model, clock

    def weekly(self, since: date | None = None, until: date | None = None) -> dict:
        until = until or self._clock().date()
        since = since or until - timedelta(days=7)
        return self._rm.weekly(since, until)
