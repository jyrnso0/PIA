import json
from datetime import timedelta
from pathlib import Path

from sqlalchemy import select

from src.infrastructure.orm import OutboxRow, PagoRow, ReservaRow, SesionRow

SUBJECT = "Cálculo"


def register_tutor_and_student(client, clock, tutor_id="tutor-1", student_id="student-1", active=True):
    tutor = client.post("/tutores", json={"id": tutor_id, "name": "Ana Tutor"})
    student = client.post(
        "/estudiantes",
        json={"id": student_id, "name": "Estudiante Uno", "active": active},
    )
    assert tutor.status_code == 201
    assert student.status_code == 201

    client.put(
        f"/tutores/{tutor_id}/disponibilidad",
        json={
            "subject": SUBJECT,
            "modalities": ["virtual", "presencial"],
            "slots": [
                {
                    "start": (clock.now + timedelta(hours=1)).isoformat(),
                    "end": (clock.now + timedelta(hours=8)).isoformat(),
                }
            ],
        },
    ).raise_for_status()
    return tutor_id, student_id


def create_reservation(client, clock, tutor_id="tutor-1", student_id="student-1", hours_after_now=1):
    start = clock.now + timedelta(hours=hours_after_now)
    response = client.post(
        "/reservas",
        json={
            "student_id": student_id,
            "tutor_id": tutor_id,
            "subject": SUBJECT,
            "topic": "Integrales",
            "modality": "virtual",
            "start": start.isoformat(),
            "end": (start + timedelta(hours=1)).isoformat(),
            "amount": "300.00",
        },
    )
    return response


def pay_for_reservation(client, reservation_id, reference="TXN-1"):
    return client.post(
        f"/reservas/{reservation_id}/pago",
        json={"reference": reference, "amount": "300.00"},
    )


def create_paid_session(client, clock, tutor_id="tutor-1", student_id="student-1", hours_after_now=1):
    reservation = create_reservation(client, clock, tutor_id, student_id, hours_after_now)
    assert reservation.status_code == 201, reservation.text
    payment = pay_for_reservation(client, reservation.json()["id"])
    assert payment.status_code == 200, payment.text
    return payment.json()["session_id"]


def test_core_api_auto_assigns_tutor_persists_payment_and_documents_openapi(client, container, clock):
    tutor_id, student_id = register_tutor_and_student(client, clock)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    profile = client.get(f"/tutores/{tutor_id}/perfil")
    assert profile.status_code == 200
    assert profile.json()["subjects"] == [SUBJECT]
    assert profile.json()["average_rating"] == 0.0

    start = clock.now + timedelta(hours=1)
    reservation = client.post(
        "/reservas",
        json={
            "student_id": student_id,
            "subject": SUBJECT,
            "topic": "Integrales",
            "modality": "virtual",
            "start": start.isoformat(),
            "end": (start + timedelta(hours=1)).isoformat(),
            "amount": "300.00",
        },
    )
    assert reservation.status_code == 201, reservation.text
    reservation_id = reservation.json()["id"]
    assert reservation.json()["tutor_id"] == tutor_id
    assert client.get(f"/reservas/{reservation_id}").json()["state"] == "pendiente"

    payment = pay_for_reservation(client, reservation_id)
    assert payment.status_code == 200, payment.text
    assert payment.json()["state"] == "confirmada"
    assert payment.json()["commission"] == "60.00"
    assert payment.json()["tutor_share"] == "240.00"
    session_id = payment.json()["session_id"]
    assert client.get(f"/sesiones/{session_id}").json()["state"] == "programada"

    with container.engine.connect() as connection:
        assert connection.scalar(
            select(ReservaRow.state).where(ReservaRow.id == reservation_id)
        ) == "confirmada"
        assert connection.scalar(select(PagoRow.state)) == "confirmado"
        assert connection.scalar(select(SesionRow.state)) == "programada"
        assert connection.scalar(select(OutboxRow.id)) is not None

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    assert "/reservas" in openapi.json()["paths"]
    checked_in_spec = json.loads(
        (Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.json").read_text(
            encoding="utf-8"
        )
    )
    assert openapi.json() == checked_in_spec
    assert client.get("/docs").status_code == 200


def test_payment_failure_rolls_back_and_overlapping_confirmed_session_is_rejected(client, clock):
    tutor_id, student_id = register_tutor_and_student(client, clock)
    client.post("/estudiantes", json={"id": "student-2", "name": "Estudiante Dos"}).raise_for_status()
    first = create_reservation(client, clock, tutor_id, student_id)
    assert first.status_code == 201, first.text
    reservation_id = first.json()["id"]

    mismatch = client.post(
        f"/reservas/{reservation_id}/pago",
        json={"reference": "TXN-BAD-AMOUNT", "amount": "299.00"},
    )
    assert mismatch.status_code == 422
    declined = pay_for_reservation(client, reservation_id, "FAIL-CARD")
    assert declined.status_code == 422
    successful = pay_for_reservation(client, reservation_id, "TXN-RETRY")
    assert successful.status_code == 200, successful.text

    second = create_reservation(client, clock, tutor_id, "student-2")
    assert second.status_code == 409


def test_unpaid_reservation_expires_and_warns_near_deadline(client, clock):
    tutor_id, student_id = register_tutor_and_student(client, clock)
    reservation = create_reservation(client, clock, tutor_id, student_id)
    assert reservation.status_code == 201, reservation.text
    reservation_id = reservation.json()["id"]

    clock.advance(minutes=11)
    notices = client.get("/notificaciones")
    assert notices.status_code == 200
    assert any(item["target"] == reservation_id for item in notices.json())

    clock.advance(minutes=6)
    late_payment = pay_for_reservation(client, reservation_id)
    assert late_payment.status_code == 409
    assert client.post("/reservas/liberar-vencidas").json() == {"released": 1}
    assert client.get(f"/reservas/{reservation_id}").json()["state"] == "liberada"


def test_session_checklists_ratings_automatic_close_and_public_comment_reporting(client, container, clock):
    tutor_id, student_id = register_tutor_and_student(client, clock)
    session_id = create_paid_session(client, clock, tutor_id, student_id)
    session_start = clock.now + timedelta(hours=1)
    clock.now = session_start

    assert client.post(f"/sesiones/{session_id}/iniciar").status_code == 200
    assert client.post(
        f"/sesiones/{session_id}/checklist", json={"party": "tutor"}
    ).status_code == 200
    missing_checklist = client.post(f"/sesiones/{session_id}/finalizar")
    assert missing_checklist.status_code == 422
    client.post(f"/sesiones/{session_id}/checklist", json={"party": "estudiante"}).raise_for_status()
    finished = client.post(f"/sesiones/{session_id}/finalizar")
    assert finished.status_code == 200
    assert finished.json()["state"] == "realizada"
    assert finished.json()["started_at"] == session_start.isoformat()
    assert finished.json()["finished_at"] == session_start.isoformat()

    client.post(
        f"/sesiones/{session_id}/calificaciones",
        json={"by": "estudiante", "stars": 5, "comment": "Muy buena tutoría"},
    ).raise_for_status()
    clock.advance(minutes=1)
    rated = client.post(
        f"/sesiones/{session_id}/calificaciones",
        json={"by": "tutor", "stars": 4, "comment": "Buena participación"},
    )
    assert rated.status_code == 200
    assert rated.json()["state"] == "cerrada"

    public_profile = client.get(f"/tutores/{tutor_id}/perfil").json()
    assert public_profile["average_rating"] == 5.0
    assert public_profile["comments"][0]["comment"] == "Muy buena tutoría"

    client.post(
        f"/sesiones/{session_id}/comentarios/reportar", json={"author": "estudiante"}
    ).raise_for_status()
    assert client.get(f"/tutores/{tutor_id}/perfil").json()["comments"] == []

    admin_headers = {"X-Role": "administrador"}
    assert client.get("/dashboard/semanal").status_code == 401
    assert client.get("/dashboard/semanal", headers=admin_headers).status_code == 200
    assert client.get("/tutores/tutor-1/estado", headers=admin_headers).status_code == 200
    assert client.get("/dashboard/semanal", headers={"X-Role": "soporte"}).status_code == 403

    with container.engine.connect() as connection:
        assert connection.scalar(select(PagoRow.state)) == "liquidado"


def test_cancellation_requires_support_reason_and_applies_late_penalty(client, container, clock):
    tutor_id, student_id = register_tutor_and_student(client, clock)
    session_id = create_paid_session(client, clock, tutor_id, student_id)

    missing_reason = client.post(
        f"/sesiones/{session_id}/cancelar",
        json={"requester": "soporte"},
    )
    assert missing_reason.status_code == 422

    result = client.post(
        f"/sesiones/{session_id}/cancelar",
        json={"requester": "estudiante"},
    )
    assert result.status_code == 200, result.text
    assert result.json()["state"] == "cancelada"
    assert result.json()["penalty"] == "150.00"
    assert result.json()["refund"] == "150.00"
    with container.engine.connect() as connection:
        evidence = connection.scalar(
            select(PagoRow.refund_evidence)
            .join(SesionRow, SesionRow.reserva_id == PagoRow.reserva_id)
            .where(SesionRow.id == session_id)
        )
        assert evidence == [f"session:{session_id}:cancellation"]


def test_attendance_no_shows_refunds_and_repeated_tutor_absences_suspend_account(
    client, container, clock
):
    tutor_id, student_id = register_tutor_and_student(client, clock)
    first_session = create_paid_session(client, clock, tutor_id, student_id)
    clock.now += timedelta(hours=1)
    presence = client.post(
        f"/sesiones/{first_session}/presencia", json={"party": "tutor"}
    )
    assert presence.status_code == 200
    no_show = client.post(f"/sesiones/{first_session}/ausencia-estudiante")
    assert no_show.status_code == 200
    assert no_show.json()["charged"] == "300.00"

    for offset in (2, 3, 4):
        session_id = create_paid_session(
            client, clock, tutor_id, student_id, hours_after_now=offset
        )
        absence = client.post(
            f"/sesiones/{session_id}/ausencia-tutor",
            json={"responsible": "support-agent"},
            headers={"X-Role": "soporte"},
        )
        assert absence.status_code == 200, absence.text
        assert absence.json()["refund"] == "300.00"

    state = client.get(
        f"/tutores/{tutor_id}/estado", headers={"X-Role": "administrador"}
    )
    assert state.status_code == 200
    assert state.json()["state"] == "suspendido"
    assert state.json()["absences"] == 3
    with container.engine.connect() as connection:
        evidence = connection.scalar(
            select(PagoRow.refund_evidence)
            .join(SesionRow, SesionRow.reserva_id == PagoRow.reserva_id)
            .where(SesionRow.id == session_id)
        )
        assert evidence == [f"session:{session_id}:tutor-absence"]

    reactivated = client.post(
        f"/tutores/{tutor_id}/reactivar",
        json={"responsible": "admin-1"},
        headers={"X-Role": "administrador"},
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["state"] == "activo"


def test_connection_cut_threshold_and_student_absence_requires_tutor_presence(client, clock):
    tutor_id, student_id = register_tutor_and_student(client, clock)
    session_id = create_paid_session(client, clock, tutor_id, student_id)

    unconfirmed_absence = client.post(f"/sesiones/{session_id}/ausencia-estudiante")
    assert unconfirmed_absence.status_code == 422

    clock.now += timedelta(hours=1)
    client.post(f"/sesiones/{session_id}/iniciar").raise_for_status()
    cut_short = client.post(
        f"/sesiones/{session_id}/corte-conexion", json={"minutes": 14}
    )
    assert cut_short.status_code == 200
    assert cut_short.json()["state"] == "interrumpida"
    assert cut_short.json()["counts_as_completed"] is False


def test_dispute_requires_support_role_evidence_and_resolves_with_refund(client, container, clock):
    tutor_id, student_id = register_tutor_and_student(client, clock)
    session_id = create_paid_session(client, clock, tutor_id, student_id)
    clock.now += timedelta(hours=1)
    client.post(f"/sesiones/{session_id}/iniciar").raise_for_status()
    for party in ("tutor", "estudiante"):
        client.post(
            f"/sesiones/{session_id}/checklist", json={"party": party}
        ).raise_for_status()
    client.post(f"/sesiones/{session_id}/finalizar").raise_for_status()

    dispute = client.post(
        "/disputas", json={"session_id": session_id, "party": "estudiante"}
    )
    assert dispute.status_code == 201, dispute.text
    dispute_id = dispute.json()["id"]
    no_evidence = client.post(
        f"/disputas/{dispute_id}/resolver",
        json={"responsible": "support-1", "decision": "Reembolso", "refund_percent": 100},
        headers={"X-Role": "soporte"},
    )
    assert no_evidence.status_code == 422
    assert client.post(f"/disputas/{dispute_id}/escalar").status_code == 200
    assert client.post(
        f"/disputas/{dispute_id}/evidencia",
        json={"reference": "evidence://session-1", "author": student_id},
    ).status_code == 200

    unauthorized = client.post(
        f"/disputas/{dispute_id}/resolver",
        json={"responsible": "admin-1", "decision": "Resuelta"},
        headers={"X-Role": "administrador"},
    )
    assert unauthorized.status_code == 403
    resolved = client.post(
        f"/disputas/{dispute_id}/resolver",
        json={
            "responsible": "support-1",
            "decision": "Reembolso total autorizado con evidencia",
            "refund_percent": 100,
        },
        headers={"X-Role": "soporte"},
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["state"] == "resuelta"
    assert resolved.json()["responsible"] == "support-1"
    assert client.get(f"/disputas/{dispute_id}").json()["evidence"] == [
        "evidence://session-1"
    ]
    with container.engine.connect() as connection:
        evidence = connection.scalar(
            select(PagoRow.refund_evidence)
            .join(SesionRow, SesionRow.reserva_id == PagoRow.reserva_id)
            .where(SesionRow.id == session_id)
        )
        assert evidence == ["evidence://session-1"]

    clock.advance(hours=26)
    expired_window = client.post(
        "/disputas", json={"session_id": session_id, "party": "tutor"}
    )
    assert expired_window.status_code == 409


def test_extension_and_modality_change_need_both_parties(client, clock):
    tutor_id, student_id = register_tutor_and_student(client, clock)
    session_id = create_paid_session(
        client, clock, tutor_id, student_id, hours_after_now=2
    )

    proposal = client.post(
        f"/sesiones/{session_id}/modalidad",
        json={"by": "estudiante", "modality": "presencial"},
    )
    assert proposal.status_code == 200
    accepted = client.post(
        f"/sesiones/{session_id}/modalidad/aceptar", json={"by": "tutor"}
    )
    assert accepted.status_code == 200
    assert accepted.json()["modality"] == "presencial"

    clock.now += timedelta(hours=2)
    client.post(f"/sesiones/{session_id}/iniciar").raise_for_status()
    client.post(
        f"/sesiones/{session_id}/extension",
        json={"by": "estudiante", "minutes": 30},
    ).raise_for_status()
    partial = client.post(
        f"/sesiones/{session_id}/extension/aceptar", json={"by": "estudiante"}
    )
    assert partial.status_code == 200
    assert partial.json()["extended"] is False
    complete = client.post(
        f"/sesiones/{session_id}/extension/aceptar", json={"by": "tutor"}
    )
    assert complete.status_code == 200
    assert complete.json()["extended"] is True
    assert complete.json()["extra_charge"] == "150.00"


def test_api_validation_and_not_found_errors_are_explicit(client):
    assert client.get("/reservas/unknown").status_code == 404
    assert client.get("/sesiones/unknown").status_code == 404
    assert client.get("/disputas/unknown").status_code == 404

    invalid_reservation = client.post(
        "/reservas",
        json={
            "student_id": "student-1",
            "subject": SUBJECT,
            "start": "2026-11-03T11:00:00",
            "end": "2026-11-03T10:00:00",
            "amount": "300.00",
        },
    )
    assert invalid_reservation.status_code == 422

    assert client.get(
        "/disputas/vencidas", headers={"X-Role": "estudiante"}
    ).status_code == 403
    assert client.get(
        "/disputas/vencidas", headers={"X-Role": "soporte"}
    ).status_code == 200
