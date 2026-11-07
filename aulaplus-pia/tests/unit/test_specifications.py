from datetime import datetime, timedelta

from src.domain.estudiante import Estudiante
from src.domain.sesion import Sesion
from src.domain.specifications import (
    ConnectionCounts,
    LateCancellation,
    NoOverlap,
    ReportedAbsence,
    SlotWithinAvailability,
    StudentActive,
    TutorActive,
    TutorOffersSubject,
    WithinDisputeWindow,
    can_receive_booking,
)
from src.domain.tutor import Tutor
from src.domain.value_objects import Cancellation, Modality, Role, Schedule

T0 = datetime(2026, 11, 3, 10, 0)
SLOT = Schedule(T0, T0 + timedelta(hours=1))


class Always:
    def is_satisfied_by(self, c):  # no hereda: solo para probar operadores con las clases reales
        return True


def tutor():
    t = Tutor("t1")
    t.set_availability("Cálculo", [Schedule(T0 - timedelta(hours=2), T0 + timedelta(hours=8))], [Modality.VIRTUAL])
    return t


def test_and_or_not_composition():
    active, inactive = Estudiante("a", active=True), Estudiante("b", active=False)
    spec = StudentActive()
    assert spec.is_satisfied_by(active) and not spec.is_satisfied_by(inactive)
    assert (~spec).is_satisfied_by(inactive)
    assert (spec | ~spec).is_satisfied_by(inactive)
    assert not (spec & ~spec).is_satisfied_by(active)


def test_can_receive_booking_composite():
    t = tutor()
    assert can_receive_booking("Cálculo", SLOT).is_satisfied_by(t)
    assert not can_receive_booking("Física", SLOT).is_satisfied_by(t)                        # BR-0015
    outside = Schedule(T0 + timedelta(days=1), T0 + timedelta(days=1, hours=1))
    assert not can_receive_booking("Cálculo", outside).is_satisfied_by(t)
    t.register_absence("s1", T0), t.register_absence("s2", T0), t.register_absence("s3", T0)
    assert not TutorActive().is_satisfied_by(t)                                               # BR-0018
    assert TutorOffersSubject("Cálculo").is_satisfied_by(t)
    assert not SlotWithinAvailability("Nada", SLOT).is_satisfied_by(t)


def test_no_overlap():
    s = Sesion("r", "t", "e", SLOT)
    assert not NoOverlap(SLOT).is_satisfied_by([s])
    assert NoOverlap(Schedule(SLOT.end, SLOT.end + timedelta(hours=1))).is_satisfied_by([s])


def test_late_cancellation_boundary():
    assert LateCancellation().is_satisfied_by(Cancellation(Role.STUDENT, timedelta(hours=3, minutes=59)))
    assert not LateCancellation().is_satisfied_by(Cancellation(Role.STUDENT, timedelta(hours=4)))


def test_dispute_window_boundary():
    s = Sesion("r", "t", "e", SLOT)
    assert WithinDisputeWindow(SLOT.end + timedelta(hours=24)).is_satisfied_by(s)
    assert not WithinDisputeWindow(SLOT.end + timedelta(hours=24, minutes=1)).is_satisfied_by(s)


def test_reported_absence_and_connection():
    assert ReportedAbsence().is_satisfied_by("falla") and not ReportedAbsence().is_satisfied_by(None)
    assert ConnectionCounts().is_satisfied_by(timedelta(minutes=15))
