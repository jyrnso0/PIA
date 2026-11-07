from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.domain.disputa import Disputa
from src.domain.errors import DeadlineExpired, EvidenceRequired, InvalidTransition, RuleViolation, ScheduleUnavailable
from src.domain.pago import Pago
from src.domain.reserva import Reserva
from src.domain.services import OverlapValidator, RefundCalculator
from src.domain.sesion import Sesion
from src.domain.state_machine import StateMachine
from src.domain.tutor import Tutor
from src.domain.value_objects import (
    AccountState,
    Cancellation,
    DisputaState,
    Modality,
    Money,
    PagoState,
    Rating,
    ReservaState,
    Role,
    Schedule,
    SesionState,
)

T0 = datetime(2026, 11, 2, 9, 0)


def sched(h=10, hours=1, day=3):
    s = datetime(2026, 11, day, h, 0)
    return Schedule(s, s + timedelta(hours=hours))


def reserva(now=T0):
    return Reserva("t1", "e1", "Cálculo", Modality.VIRTUAL, sched(), Money(300), now)


def sesion():
    return Sesion("r1", "t1", "e1", sched())


# ---- Value objects ----
def test_money_rounds_half_up_and_operates():
    assert Money("10.005").amount == Decimal("10.01")
    assert (Money(100).times("0.2") + Money(5)).amount == Decimal("25.00")
    assert (Money(100) - Money(30)).amount == Decimal("70.00")


def test_schedule_is_half_open_and_validates():
    a = sched(10)
    assert not a.overlaps(sched(11))
    assert a.overlaps(Schedule(a.start + timedelta(minutes=30), a.end + timedelta(minutes=30)))
    with pytest.raises(ValueError):
        Schedule(a.end, a.start)


def test_rating_range():
    with pytest.raises(ValueError):
        Rating(Role.STUDENT, 6)


# ---- State machine ----
def test_state_machine_rejects_undeclared_transitions():
    m = StateMachine("X", ReservaState.PENDIENTE, {ReservaState.PENDIENTE: {"pay": ReservaState.CONFIRMADA}})
    assert m.can("pay") and m.allowed() == ["pay"]
    m.fire("pay")
    assert not m.can("pay")
    with pytest.raises(InvalidTransition):
        m.fire("pay")


# ---- Reserva (BR-0001) ----
def test_reserva_confirms_within_15_minutes():
    r = reserva()
    r.confirm_payment(T0 + timedelta(minutes=15))
    assert r.state is ReservaState.CONFIRMADA
    assert [e.name for e in r.pull_events()] == ["ReservaCreada", "ReservaConfirmada"]
    assert r.pull_events() == []


def test_reserva_payment_after_15_minutes_fails_and_releases():
    r = reserva()
    with pytest.raises(DeadlineExpired):
        r.confirm_payment(T0 + timedelta(minutes=16))
    assert r.release_if_expired(T0 + timedelta(minutes=16)) is True
    assert r.state is ReservaState.LIBERADA
    assert r.release_if_expired(T0 + timedelta(minutes=17)) is False


def test_reserva_not_released_before_deadline_and_cancel_flow():
    r = reserva()
    assert r.release_if_expired(T0 + timedelta(minutes=5)) is False
    with pytest.raises(InvalidTransition):
        r.cancel()
    r.confirm_payment(T0)
    r.cancel()
    assert r.state is ReservaState.CANCELADA


# ---- Sesión ----
def started():
    s = sesion()
    s.start(s.schedule.start)
    return s


def test_session_full_lifecycle_with_checklist_and_ratings_closes():
    s = started()
    s.confirm_checklist(Role.TUTOR, s.schedule.start)
    with pytest.raises(RuleViolation):  # BR-0014
        s.finish(s.schedule.end)
    s.confirm_checklist(Role.STUDENT, s.schedule.start)
    s.finish(s.schedule.end)
    assert s.state is SesionState.REALIZADA
    s.rate(Rating(Role.STUDENT, 5), s.schedule.end)
    assert s.state is SesionState.REALIZADA
    s.rate(Rating(Role.TUTOR, 4), s.schedule.end)  # BR-0002
    assert s.state is SesionState.CERRADA


def test_session_auto_close_after_48h():
    s = started()
    s.confirm_checklist(Role.TUTOR, T0)
    s.confirm_checklist(Role.STUDENT, T0)
    s.finish(s.schedule.end)
    assert s.close_if_overdue(s.schedule.end + timedelta(hours=47)) is False
    assert s.close_if_overdue(s.schedule.end + timedelta(hours=48)) is True
    assert s.state is SesionState.CERRADA


def test_session_invalid_transitions():
    s = sesion()
    with pytest.raises(InvalidTransition):
        s.finish(T0)          # saltar estado
    with pytest.raises(InvalidTransition):
        s.confirm_checklist(Role.TUTOR, T0)
    with pytest.raises(InvalidTransition):
        s.rate(Rating(Role.STUDENT, 5), T0)
    s.start(T0)
    with pytest.raises(InvalidTransition):
        s.start(T0)           # repetir
    with pytest.raises(InvalidTransition):
        s.cancel(Role.STUDENT, T0)


def test_cancel_support_requires_reported_situation_br0003():
    s = sesion()
    with pytest.raises(RuleViolation):
        s.cancel(Role.SUPPORT, T0)
    c = s.cancel(Role.SUPPORT, T0, "Falla eléctrica")
    assert c.requester is Role.SUPPORT and s.state is SesionState.CANCELADA


def test_absences():
    s = sesion()
    with pytest.raises(RuleViolation):
        s.mark_student_absent()                               # BR-0008: tutor sin confirmar presencia
    s.confirm_presence(Role.TUTOR, T0)
    s.mark_student_absent()
    assert s.state is SesionState.AUSENCIA_ESTUDIANTE
    t = sesion()
    t.mark_tutor_absent()
    assert t.state is SesionState.AUSENCIA_TUTOR


def test_connection_cut_threshold_br0010():
    assert Sesion.connection_cut_counts(timedelta(minutes=15))
    assert not Sesion.connection_cut_counts(timedelta(minutes=14))


# ---- Tutor ----
def test_tutor_suspended_after_more_than_two_absences_in_30_days():
    t = Tutor("t1")
    assert not t.register_absence("s1", T0)
    assert not t.register_absence("s2", T0 + timedelta(days=1))
    assert t.register_absence("s3", T0 + timedelta(days=2))
    assert t.state is AccountState.SUSPENDIDO
    assert not t.register_absence("s4", T0 + timedelta(days=3))  # ya suspendido


def test_old_absences_do_not_count():
    t = Tutor("t1")
    t.register_absence("s1", T0)
    t.register_absence("s2", T0 + timedelta(days=1))
    assert not t.register_absence("s3", T0 + timedelta(days=40))


def test_tutor_availability_and_rating():
    t = Tutor("t1", "Ana")
    with pytest.raises(RuleViolation):
        t.set_availability("Cálculo", [], [])
    t.set_availability("Cálculo", [sched()], [Modality.VIRTUAL])
    assert "Cálculo" in t.availability
    assert t.average_rating == 0.0
    t.add_rating(5)
    t.add_rating(4)
    assert t.average_rating == 4.5


# ---- Pago ----
def test_pago_commission_20_80_br0005():
    p = Pago("r1", Money(300))
    p.confirm("RCPT-1")
    assert p.breakdown.commission.amount == Decimal("60.00")
    assert p.breakdown.tutor_share.amount == Decimal("240.00")
    with pytest.raises(InvalidTransition):
        p.confirm("again")
    p.settle()
    assert p.state is PagoState.LIQUIDADO


def test_pago_late_cancellation_penalty_50_br0004():
    p = Pago("r1", Money(100))
    late = Cancellation(Role.STUDENT, timedelta(hours=3))
    assert p.penalty_for(late).amount.amount == Decimal("50.00")
    ontime = Cancellation(Role.STUDENT, timedelta(hours=4))
    assert p.penalty_for(ontime) is None


def test_pago_refund_requires_reason_and_responsible_br0017():
    p = Pago("r1", Money(100))
    p.confirm("x")
    with pytest.raises(InvalidTransition):
        p.refund(Money(100), "", "soporte", None, ["e"])
    with pytest.raises(InvalidTransition):
        p.refund(Money(100), "ausencia_tutor", "soporte-1")                # sin evidencia
    with pytest.raises(InvalidTransition):
        p.refund(Money(100), "ausencia_tutor", "soporte-1", None, [" "])
    p.refund(Money(100), "ausencia_tutor", "soporte-1", None, ["session:s1:tutor-absence"])
    assert p.refund_evidence == ["session:s1:tutor-absence"]
    assert p.state is PagoState.REEMBOLSADO


def test_pago_cannot_settle_before_confirm():
    with pytest.raises(InvalidTransition):
        Pago("r1", Money(10)).settle()


# ---- Refund policy ----
def test_refund_policies():
    calc = RefundCalculator()
    paid = Money(100)
    late_student = Cancellation(Role.STUDENT, timedelta(hours=1))
    assert calc.amount("cancelacion", late_student, paid).amount == Decimal("50.00")
    assert calc.amount("cancelacion", Cancellation(Role.TUTOR, timedelta(hours=1)), paid).amount == Decimal("100.00")
    assert calc.amount("cancelacion", Cancellation(Role.STUDENT, timedelta(hours=9)), paid).amount == Decimal("100.00")
    assert calc.amount("ausencia_tutor", None, paid).amount == Decimal("100.00")  # BR-0009
    with pytest.raises(ValueError):
        calc.amount("otra", None, paid)


# ---- Overlap ----
def test_overlap_validator_br0006():
    s = sesion()
    v = OverlapValidator()
    v.ensure_free(sched(11), [s])                 # contiguo: permitido
    with pytest.raises(ScheduleUnavailable):
        v.ensure_free(sched(10), [s])
    cancelled = sesion()
    cancelled.cancel(Role.TUTOR, T0)
    v.ensure_free(sched(10), [cancelled])         # una sesión cancelada libera el horario


# ---- Disputa ----
def test_dispute_requires_evidence_decision_and_responsible_br0020():
    d = Disputa("s1", Role.STUDENT, T0)
    assert d.due_at == T0 + timedelta(hours=48)   # BR-0011
    with pytest.raises(EvidenceRequired):
        d.resolve("Reembolso", "soporte-1")
    d.attach_evidence("captura.png", "est-1")
    with pytest.raises(InvalidTransition):
        d.resolve("x", "soporte-1")               # no escalada aún
    d.escalate()
    with pytest.raises(EvidenceRequired):
        d.resolve("", "soporte-1")
    d.resolve("Reembolso total", "soporte-1")
    assert d.state is DisputaState.RESUELTA
    with pytest.raises(InvalidTransition):
        d.resolve("otra vez", "soporte-1")


# ---- BR-0010 corte de conexión ----
def test_connection_cut_counts_as_completed_from_15_minutes():
    s = started()
    assert s.connection_cut(timedelta(minutes=15), T0) is True
    assert s.state is SesionState.REALIZADA


def test_connection_cut_under_15_minutes_does_not_count():
    s = started()
    assert s.connection_cut(timedelta(minutes=14), T0) is False
    assert s.state is SesionState.INTERRUMPIDA


# ---- BR-0012 extensión ----
def hourly_session():
    s = Sesion("r1", "t1", "e1", sched(), modality=Modality.VIRTUAL, hourly_rate=Money(300))
    s.start(s.schedule.start)
    return s


def test_extension_needs_both_parties_and_charges_proportionally():
    s = hourly_session()
    s.propose_extension(Role.STUDENT, 30)
    assert s.accept_extension(Role.STUDENT) is None            # el proponente solo no basta
    extra = s.accept_extension(Role.TUTOR)
    assert extra.amount == Decimal("150.00")                   # 30 min a 300/h
    assert s.schedule.end == sched().end + timedelta(minutes=30)
    assert s.pending_extension is None


def test_extension_validations():
    s = sesion()
    with pytest.raises(InvalidTransition):
        s.propose_extension(Role.STUDENT, 15)                  # no está en curso
    s = hourly_session()
    with pytest.raises(RuleViolation):
        s.propose_extension(Role.STUDENT, 0)
    with pytest.raises(RuleViolation):
        s.propose_extension(Role.SUPPORT, 15)
    with pytest.raises(InvalidTransition):
        s.accept_extension(Role.TUTOR)                         # sin propuesta


def test_pago_extra_recalculates_commission():
    p = Pago("r1", Money(300))
    p.confirm("x")
    p.add_extra(Money(150))
    assert p.amount.amount == Decimal("450.00")
    assert p.breakdown.commission.amount == Decimal("90.00")
    with pytest.raises(InvalidTransition):
        Pago("r2", Money(1)).add_extra(Money(1))


# ---- BR-0013 cambio de modalidad ----
def test_modality_change_requires_both_and_one_hour_notice():
    s = sesion()  # empieza 3-nov 10:00
    s.propose_modality_change(Role.STUDENT, Modality.PRESENCIAL, s.schedule.start - timedelta(hours=2))
    assert s.accept_modality_change(Role.STUDENT, s.schedule.start - timedelta(hours=2)) is False
    assert s.accept_modality_change(Role.TUTOR, s.schedule.start - timedelta(hours=2)) is True
    assert s.modality is Modality.PRESENCIAL


def test_modality_change_rejected_with_less_than_one_hour():
    s = sesion()
    with pytest.raises(RuleViolation):
        s.propose_modality_change(Role.STUDENT, Modality.PRESENCIAL, s.schedule.start - timedelta(minutes=59))
    s.propose_modality_change(Role.STUDENT, Modality.PRESENCIAL, s.schedule.start - timedelta(hours=2))
    with pytest.raises(RuleViolation):
        s.accept_modality_change(Role.TUTOR, s.schedule.start - timedelta(minutes=30))
    with pytest.raises(RuleViolation):
        s.propose_modality_change(Role.TUTOR, Modality.VIRTUAL, s.schedule.start - timedelta(hours=3))  # ya es virtual


def test_modality_state_guards():
    s = sesion()
    with pytest.raises(InvalidTransition):
        s.accept_modality_change(Role.TUTOR, T0)
    s.start(T0)
    with pytest.raises(InvalidTransition):
        s.propose_modality_change(Role.STUDENT, Modality.PRESENCIAL, T0)


# ---- BR-0016 comentarios ----
def test_report_comment_marks_rating():
    s = started()
    s.confirm_checklist(Role.TUTOR, T0)
    s.confirm_checklist(Role.STUDENT, T0)
    s.finish(T0)
    s.rate(Rating(Role.STUDENT, 1, "grosero"), T0)
    s.report_comment(Role.STUDENT)
    assert s.ratings["estudiante"].reported is True
    with pytest.raises(RuleViolation):
        s.report_comment(Role.TUTOR)                           # no hay comentario del tutor


# ---- Tutor reactivación / presencia / SLA ----
def test_tutor_reactivation_by_admin_review():
    t = Tutor("t1")
    with pytest.raises(RuleViolation):
        t.reactivate("admin")
    for i in range(3):
        t.register_absence(f"s{i}", T0)
    t.reactivate("admin-1")
    assert t.state is AccountState.ACTIVO and t.absences == []


def test_presence_rules():
    s = sesion()
    with pytest.raises(RuleViolation):
        s.confirm_presence(Role.SUPPORT, T0)
    s.cancel(Role.TUTOR, T0)
    with pytest.raises(InvalidTransition):
        s.confirm_presence(Role.TUTOR, T0)


def test_dispute_overdue_sla_br0011():
    d = Disputa("s1", Role.STUDENT, T0)
    assert d.overdue(T0 + timedelta(hours=48)) is False
    assert d.overdue(T0 + timedelta(hours=48, minutes=1)) is True
    d.attach_evidence("e"), d.escalate(), d.resolve("ok", "soporte-1")
    assert d.overdue(T0 + timedelta(days=9)) is False
