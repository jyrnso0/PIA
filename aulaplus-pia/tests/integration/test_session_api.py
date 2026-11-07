"""US-02, 03, 04, 08, 09, 10, 12, 13, 14, 16, 17, 18: ciclo de vida de la sesión."""

import pytest

from .helpers import ADM, D3, SOP, booked_session, run_session, setup_world


def pay_of(container, rid):
    with container.bookings._uow as uow:
        return uow.pagos.by_reserva(rid)


def test_full_lifecycle_with_evidence_and_auto_close_when_both_rate(client, clock, container):
    setup_world(client)
    rid, sid = booked_session(client)
    clock.now = D3.replace(hour=10)
    s = run_session(client, sid)
    assert s["state"] == "realizada" and s["started_at"] and s["finished_at"]       # BR-0014
    assert set(s["checklist"]) == {"tutor", "estudiante"}
    r = client.post(f"/sesiones/{sid}/calificaciones", json={"by": "estudiante", "stars": 5, "comment": "Excelente"})
    assert r.json()["state"] == "realizada"
    r = client.post(f"/sesiones/{sid}/calificaciones", json={"by": "tutor", "stars": 4})
    assert r.json()["state"] == "cerrada"                                           # BR-0002
    assert pay_of(container, rid).state.value == "liquidado"
    profile = client.get("/tutores/t1/perfil").json()
    assert profile["average_rating"] == 5.0 and profile["comments"][0]["comment"] == "Excelente"
    assert "state" not in profile and "absences" not in profile                      # BR-0016: sin datos internos


def test_finish_requires_both_checklists(client):
    setup_world(client)
    _, sid = booked_session(client)
    client.post(f"/sesiones/{sid}/iniciar")
    client.post(f"/sesiones/{sid}/checklist", json={"party": "tutor"})
    r = client.post(f"/sesiones/{sid}/finalizar")
    assert r.status_code == 422                                                      # BR-0014
    assert client.post(f"/sesiones/{sid}/checklist", json={"party": "soporte"}).status_code == 422


@pytest.mark.parametrize("action,expected", [("finalizar", 409), ("checklist", 409)])
def test_state_machine_blocks_invalid_transitions(client, action, expected):
    setup_world(client)
    _, sid = booked_session(client)
    body = {"party": "tutor"} if action == "checklist" else None
    assert client.post(f"/sesiones/{sid}/{action}", json=body).status_code == expected
    client.post(f"/sesiones/{sid}/iniciar")
    assert client.post(f"/sesiones/{sid}/iniciar").status_code == 409                # repetir inicio
    assert client.post(f"/sesiones/{sid}/cancelar", json={"requester": "estudiante"}).status_code == 409


def test_auto_close_after_48h_without_dispute(client, clock):
    setup_world(client)
    _, sid = booked_session(client)
    clock.now = D3.replace(hour=10)
    run_session(client, sid)
    clock.advance(hours=47)
    assert client.post("/sesiones/cerrar-vencidas").json() == {"closed": 0}
    clock.advance(hours=1, minutes=1)
    assert client.post("/sesiones/cerrar-vencidas").json() == {"closed": 1}
    assert client.get(f"/sesiones/{sid}").json()["state"] == "cerrada"


def test_open_dispute_blocks_auto_close(client, clock):
    setup_world(client)
    _, sid = booked_session(client)
    clock.now = D3.replace(hour=10)
    run_session(client, sid)
    clock.now = D3.replace(hour=12)
    assert client.post("/disputas", json={"session_id": sid, "party": "estudiante"}).status_code == 201
    clock.advance(hours=60)
    assert client.post("/sesiones/cerrar-vencidas").json() == {"closed": 0}


def test_cancel_late_penalty_50_br0004(client, clock, container):
    setup_world(client)
    rid, sid = booked_session(client)
    clock.now = D3.replace(hour=7, minute=30)                       # 2.5 h antes
    r = client.post(f"/sesiones/{sid}/cancelar", json={"requester": "estudiante"}).json()
    assert r["state"] == "cancelada" and r["late"] is True
    assert r["penalty"] == "150.00" and r["refund"] == "150.00"
    assert client.get(f"/reservas/{rid}").json()["state"] == "cancelada"
    p = pay_of(container, rid)
    assert p.refund_responsible == "estudiante" and p.refunded_at == clock.now      # RNF trazabilidad


def test_cancel_with_notice_has_no_penalty(client, clock):
    setup_world(client)
    _, sid = booked_session(client)
    clock.now = D3.replace(hour=5)
    r = client.post(f"/sesiones/{sid}/cancelar", json={"requester": "tutor"}).json()
    assert r["late"] is False and r["penalty"] == "0.00" and r["refund"] == "300.00"


def test_tutor_late_cancel_penalizes_tutor_and_refunds_student_fully(client, clock):
    setup_world(client)
    _, sid = booked_session(client)
    clock.now = D3.replace(hour=9)
    r = client.post(f"/sesiones/{sid}/cancelar", json={"requester": "tutor"}).json()
    assert r["penalty"] == "150.00" and r["refund"] == "300.00"


def test_support_cancel_requires_reported_situation_br0003(client):
    setup_world(client)
    _, sid = booked_session(client)
    r = client.post(f"/sesiones/{sid}/cancelar", json={"requester": "soporte"})
    assert r.status_code == 422
    ok = client.post(f"/sesiones/{sid}/cancelar", json={"requester": "soporte", "reported_situation": "Emergencia"})
    assert ok.status_code == 200 and ok.json()["state"] == "cancelada"


def test_tutor_absence_refund_100_and_suspension_after_three(client, clock, container):
    setup_world(client)
    for i, hour in enumerate((9, 10, 11)):
        client.post("/estudiantes", json={"id": f"x{i}"})
        _, sid = booked_session(client, hour=hour, student=f"x{i}")
        r = client.post(f"/sesiones/{sid}/ausencia-tutor", json={"responsible": "soporte-1"}, headers=SOP)
        assert r.status_code == 200 and r.json()["refund"] == "300.00"              # BR-0009
        assert r.json()["tutor_suspended"] is (i == 2)                              # BR-0018
    assert client.get("/tutores/t1/estado", headers=ADM).json() == {"id": "t1", "state": "suspendido", "absences": 3}
    client.post("/estudiantes", json={"id": "nuevo"})
    from .helpers import book
    assert book(client, hour=15, student="nuevo").status_code == 422               # suspendido no recibe reservas
    r = client.post("/tutores/t1/reactivar", json={"responsible": "admin-1"}, headers=ADM)
    assert r.json()["state"] == "activo"
    assert book(client, hour=15, student="nuevo").status_code == 201
    assert client.post("/tutores/t1/reactivar", json={"responsible": "a"}, headers=ADM).status_code == 422


def test_tutor_absence_requires_support_role(client):
    setup_world(client)
    _, sid = booked_session(client)
    body = {"responsible": "x"}
    assert client.post(f"/sesiones/{sid}/ausencia-tutor", json=body).status_code == 401
    assert client.post(f"/sesiones/{sid}/ausencia-tutor", json=body, headers={"X-Role": "estudiante"}).status_code == 403


def test_student_absence_charges_100_only_if_tutor_confirmed_presence_br0008(client, container):
    setup_world(client)
    rid, sid = booked_session(client)
    r = client.post(f"/sesiones/{sid}/ausencia-estudiante")
    assert r.status_code == 422                                                      # sin presencia del tutor
    assert client.post(f"/sesiones/{sid}/presencia", json={"party": "tutor"}).status_code == 200
    r = client.post(f"/sesiones/{sid}/ausencia-estudiante").json()
    assert r["state"] == "ausencia_estudiante" and r["charged"] == "300.00" and r["tutor_share"] == "240.00"
    assert pay_of(container, rid).state.value == "liquidado"


def test_connection_cut_br0010(client):
    setup_world(client)
    _, s1 = booked_session(client, hour=9)
    client.post(f"/sesiones/{s1}/iniciar")
    r = client.post(f"/sesiones/{s1}/corte-conexion", json={"minutes": 15}).json()
    assert r["counts_as_completed"] is True and r["state"] == "realizada"
    client.post("/estudiantes", json={"id": "e2"})
    _, s2 = booked_session(client, hour=12, student="e2")
    client.post(f"/sesiones/{s2}/iniciar")
    r = client.post(f"/sesiones/{s2}/corte-conexion", json={"minutes": 14}).json()
    assert r["counts_as_completed"] is False and r["state"] == "interrumpida"


def test_extension_both_accept_charges_proportionally_br0012(client, container):
    setup_world(client)
    rid, sid = booked_session(client)                                               # 300/h
    client.post(f"/sesiones/{sid}/iniciar")
    assert client.post(f"/sesiones/{sid}/extension", json={"by": "estudiante", "minutes": 30}).status_code == 200
    r = client.post(f"/sesiones/{sid}/extension/aceptar", json={"by": "estudiante"}).json()
    assert r["extended"] is False
    r = client.post(f"/sesiones/{sid}/extension/aceptar", json={"by": "tutor"}).json()
    assert r["extended"] is True and r["extra_charge"] == "150.00" and r["new_total"] == "450.00"
    assert r["ends_at"].startswith("2026-11-03T11:30")
    p = pay_of(container, rid)
    assert p.breakdown.commission.amount == 90                                       # 20 % del total nuevo


def test_extension_rules(client):
    setup_world(client)
    _, sid = booked_session(client)
    assert client.post(f"/sesiones/{sid}/extension", json={"by": "estudiante", "minutes": 30}).status_code == 409
    client.post(f"/sesiones/{sid}/iniciar")
    assert client.post(f"/sesiones/{sid}/extension/aceptar", json={"by": "tutor"}).status_code == 409
    assert client.post(f"/sesiones/{sid}/extension", json={"by": "estudiante", "minutes": 0}).status_code == 422


def test_extension_blocked_if_it_overlaps_next_session(client):
    setup_world(client)
    client.post("/estudiantes", json={"id": "e2"})
    _, s1 = booked_session(client, hour=10)
    booked_session(client, hour=11, student="e2")                                    # sesión contigua
    client.post(f"/sesiones/{s1}/iniciar")
    client.post(f"/sesiones/{s1}/extension", json={"by": "tutor", "minutes": 30})
    r = client.post(f"/sesiones/{s1}/extension/aceptar", json={"by": "estudiante"})
    assert r.status_code == 409 and r.json()["error"] == "SCHEDULE_UNAVAILABLE"      # BR-0006 sobre la extensión


def test_modality_change_br0013(client, clock):
    setup_world(client)
    _, sid = booked_session(client)
    clock.now = D3.replace(hour=8, minute=30)                                        # 1.5 h antes
    assert client.post(f"/sesiones/{sid}/modalidad", json={"by": "estudiante", "modality": "presencial"}).status_code == 200
    assert client.post(f"/sesiones/{sid}/modalidad/aceptar", json={"by": "estudiante"}).json()["changed"] is False
    r = client.post(f"/sesiones/{sid}/modalidad/aceptar", json={"by": "tutor"}).json()
    assert r["changed"] is True and r["modality"] == "presencial"
    clock.now = D3.replace(hour=9, minute=30)                                        # < 1 h
    r = client.post(f"/sesiones/{sid}/modalidad", json={"by": "tutor", "modality": "virtual"})
    assert r.status_code == 422


def test_modality_requires_pending_request(client, clock):
    setup_world(client)
    _, sid = booked_session(client)
    assert client.post(f"/sesiones/{sid}/modalidad/aceptar", json={"by": "tutor"}).status_code == 409


def test_report_inappropriate_comment_hides_it_br0016(client, clock):
    setup_world(client)
    _, sid = booked_session(client)
    clock.now = D3.replace(hour=10)
    run_session(client, sid)
    client.post(f"/sesiones/{sid}/calificaciones", json={"by": "estudiante", "stars": 1, "comment": "texto ofensivo"})
    assert len(client.get("/tutores/t1/perfil").json()["comments"]) == 1
    assert client.post(f"/sesiones/{sid}/comentarios/reportar", json={"author": "estudiante"}).status_code == 200
    assert client.get("/tutores/t1/perfil").json()["comments"] == []
    assert client.post(f"/sesiones/{sid}/comentarios/reportar", json={"author": "tutor"}).status_code == 422


def test_rating_rules(client, clock):
    setup_world(client)
    _, sid = booked_session(client)
    assert client.post(f"/sesiones/{sid}/calificaciones", json={"by": "estudiante", "stars": 5}).status_code == 409
    clock.now = D3.replace(hour=10)
    run_session(client, sid)
    assert client.post(f"/sesiones/{sid}/calificaciones", json={"by": "estudiante", "stars": 6}).status_code == 422
    assert client.post(f"/sesiones/{sid}/calificaciones", json={"by": "soporte", "stars": 5}).status_code == 422


def test_unknown_session_and_tutor_404(client):
    assert client.get("/sesiones/nope").status_code == 404
    assert client.get("/tutores/nope/perfil").status_code == 404
    assert client.get("/reservas/nope").status_code == 404
    assert client.get("/disputas/nope").status_code == 404
