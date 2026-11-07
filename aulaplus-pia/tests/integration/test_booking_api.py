"""US-01, US-05, US-06, US-15: reserva, pago, comisión, traslapes y disponibilidad."""
from datetime import timedelta

from .helpers import D3, book, booked_session, iso, setup_world


def test_health_and_openapi(client):
    assert client.get("/health").json() == {"status": "ok"}
    spec = client.get("/openapi.json").json()
    assert spec["info"]["title"] == "AulaPlus API" and "/reservas" in spec["paths"]
    assert client.get("/docs").status_code == 200


def test_reserve_and_pay_creates_session_with_commission_20_80(client):
    setup_world(client)
    r = book(client)
    assert r.status_code == 201 and r.json()["state"] == "pendiente"
    rid = r.json()["id"]
    p = client.post(f"/reservas/{rid}/pago", json={"reference": "TXN-1", "amount": "300.00"})
    body = p.json()
    assert p.status_code == 200 and body["state"] == "confirmada"
    assert body["commission"] == "60.00" and body["tutor_share"] == "240.00"   # BR-0005
    assert client.get(f"/sesiones/{body['session_id']}").json()["state"] == "programada"
    assert client.get(f"/reservas/{rid}").json()["state"] == "confirmada"


def test_payment_after_15_minutes_is_rejected_and_slot_is_released(client, clock):
    setup_world(client)
    rid = book(client).json()["id"]
    clock.advance(minutes=16)
    r = client.post(f"/reservas/{rid}/pago", json={"reference": "TXN", "amount": "300"})
    assert r.status_code == 409 and r.json()["error"] == "DEADLINE_EXPIRED"
    assert client.post("/reservas/liberar-vencidas").json() == {"released": 1}
    assert client.get(f"/reservas/{rid}").json()["state"] == "liberada"
    assert book(client).status_code == 201     # el horario quedó libre (BR-0001)


def test_unpaid_reservation_does_not_block_other_students(client):
    setup_world(client)
    client.post("/estudiantes", json={"id": "e2"})
    assert book(client).status_code == 201
    assert book(client, student="e2").status_code == 201   # solo bloquea la sesión confirmada


def test_overlap_blocked_after_confirmed_session_br0006(client):
    setup_world(client)
    client.post("/estudiantes", json={"id": "e2"})
    booked_session(client)
    r = book(client, student="e2")
    assert r.status_code == 409 and r.json()["error"] == "SCHEDULE_UNAVAILABLE"
    assert book(client, hour=11, student="e2").status_code == 201     # contiguo permitido


def test_payment_revalidates_overlap_br0006(client):
    setup_world(client)
    client.post("/estudiantes", json={"id": "e2"})
    r1, r2 = book(client).json()["id"], book(client, student="e2").json()["id"]
    assert client.post(f"/reservas/{r1}/pago", json={"reference": "A", "amount": "300"}).status_code == 200
    r = client.post(f"/reservas/{r2}/pago", json={"reference": "B", "amount": "300"})
    assert r.status_code == 409 and r.json()["error"] == "SCHEDULE_UNAVAILABLE"


def test_payment_validations(client):
    setup_world(client)
    rid = book(client).json()["id"]
    assert client.post(f"/reservas/{rid}/pago", json={"reference": "X", "amount": "1"}).status_code == 422
    assert client.post(f"/reservas/{rid}/pago", json={"reference": "FAIL-1", "amount": "300"}).status_code == 422
    assert client.get(f"/reservas/{rid}").json()["state"] == "pendiente"      # rollback: nada quedó guardado
    assert client.post(f"/reservas/{rid}/pago", json={"reference": "OK", "amount": "300"}).status_code == 200
    r = client.post(f"/reservas/{rid}/pago", json={"reference": "OK2", "amount": "300"})
    assert r.status_code == 409                                                # doble pago
    assert client.post("/reservas/nope/pago", json={"reference": "A", "amount": "1"}).status_code == 404


def test_reserve_rule_violations(client):
    setup_world(client)
    assert book(client, student="ghost").status_code == 404
    assert book(client, subject="Física").status_code == 422                   # BR-0015: sin disponibilidad
    assert book(client, hour=22).status_code == 422                            # fuera de franja
    client.post("/estudiantes", json={"id": "inactivo", "active": False})
    assert book(client, student="inactivo").status_code == 422
    setup_world_virtual_only = client.put("/tutores/t1/disponibilidad", json={
        "subject": "Química", "modalities": ["virtual"],
        "slots": [{"start": iso(D3.replace(hour=8)), "end": iso(D3.replace(hour=20))}]})
    assert setup_world_virtual_only.status_code == 200
    assert book(client, subject="Química", modality="presencial").status_code == 422
    bad = client.post("/reservas", json={"student_id": "e1", "tutor_id": "t1", "subject": "Cálculo", "amount": "300",
                                         "start": iso(D3.replace(hour=11)), "end": iso(D3.replace(hour=10))})
    assert bad.status_code == 422
    assert client.post("/reservas", json={"student_id": "e1"}).status_code == 422   # validación Pydantic


def test_automatic_tutor_assignment(client):
    setup_world(client)
    client.post("/tutores", json={"id": "t0", "name": "Sin horario"})
    client.post("/tutores", json={"id": "t2", "name": "Beto"})
    client.put("/tutores/t2/disponibilidad", json={
        "subject": "Cálculo", "modalities": ["virtual"],
        "slots": [{"start": iso(D3.replace(hour=8)), "end": iso(D3.replace(hour=20))}]})
    client.post("/estudiantes", json={"id": "e2"})
    client.post("/estudiantes", json={"id": "e3"})
    a = book(client, tutor=None)
    assert a.status_code == 201 and a.json()["tutor_id"] == "t1"
    client.post(f"/reservas/{a.json()['id']}/pago", json={"reference": "A", "amount": "300"})
    b = book(client, tutor=None, student="e2")
    assert b.json()["tutor_id"] == "t2"                         # t1 ocupado -> asigna el siguiente
    client.post(f"/reservas/{b.json()['id']}/pago", json={"reference": "B", "amount": "300"})
    c = book(client, tutor=None, student="e3")
    assert c.status_code == 409 and c.json()["error"] == "SCHEDULE_UNAVAILABLE"


def test_availability_is_independent_per_subject_br0015(client):
    setup_world(client)
    client.put("/tutores/t1/disponibilidad", json={
        "subject": "Física", "modalities": ["presencial"],
        "slots": [{"start": iso(D3.replace(hour=14)), "end": iso(D3.replace(hour=16))}]})
    assert book(client, subject="Cálculo").status_code == 201
    assert book(client, hour=14, subject="Física", modality="presencial").status_code == 201
    assert book(client, hour=14, subject="Cálculo").status_code == 201    # Cálculo sigue intacta
    assert sorted(client.get("/tutores/t1/perfil").json()["subjects"]) == ["Cálculo", "Física"]


def test_availability_validations(client):
    setup_world(client)
    bad = client.put("/tutores/t1/disponibilidad", json={"subject": "X", "slots": [
        {"start": iso(D3.replace(hour=10)), "end": iso(D3.replace(hour=9))}]})
    assert bad.status_code == 422
    assert client.put("/tutores/t1/disponibilidad", json={"subject": "X", "slots": []}).status_code == 422
    assert client.put("/tutores/nadie/disponibilidad", json={"subject": "X", "slots": [
        {"start": iso(D3), "end": iso(D3 + timedelta(hours=1))}]}).status_code == 404


def test_payment_notifications_before_expiry(client, clock):
    setup_world(client)
    book(client)
    assert client.get("/notificaciones").json() == []
    clock.advance(minutes=11)
    notes = client.get("/notificaciones").json()
    assert notes[0]["type"] == "PAGO_POR_VENCER" and notes[0]["to"] == "e1"
