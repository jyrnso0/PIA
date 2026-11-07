"""Datos de laboratorio (08_AulaPlus.zip) adaptados al dominio de AulaPlus.

actores -> estudiantes (activo/inactivo), catálogo -> materias con precio, acciones de transiciones_prueba ->
casos de la State Machine de la Sesión (completar, cancelar, repetir aprobación, saltar estado).
"""
import csv
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from .helpers import D3, booked_session, iso, run_session, setup_world

DATA = Path(__file__).resolve().parents[1] / "data"


def rows(name):
    with open(DATA / name, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def test_actors_active_flag_controls_who_can_book(client):
    setup_world(client)
    client.put("/tutores/t1/disponibilidad", json={
        "subject": "Python", "modalities": ["virtual"],
        "slots": [{"start": iso(D3.replace(hour=0)), "end": iso(D3.replace(hour=0) + timedelta(days=1))}]})
    actors = rows("actores.csv")
    assert len(actors) == 40
    hour, booked, blocked = 0, 0, 0
    for a in actors[:12]:
        client.post("/estudiantes", json={"id": a["actor_id"], "name": a["nombre"], "active": a["activo"] == "1"})
        r = client.post("/reservas", json={
            "student_id": a["actor_id"], "tutor_id": "t1", "subject": "Python", "amount": "405.00",
            "start": iso(D3.replace(hour=hour)), "end": iso(D3.replace(hour=hour) + timedelta(hours=1))})
        if a["activo"] == "1":
            assert r.status_code == 201, r.text
            hour, booked = hour + 1, booked + 1
        else:
            assert r.status_code == 422
            blocked += 1
    assert booked + blocked == 12


def test_catalog_prices_drive_commission(client):
    setup_world(client, subject="Python")
    items = [c for c in rows("catalogo.csv") if c["habilitado"] == "1"][:5]
    for n, item in enumerate(items):
        client.post("/estudiantes", json={"id": f"c{n}"})
        r = client.post("/reservas", json={
            "student_id": f"c{n}", "tutor_id": "t1", "subject": "Python", "amount": item["precio_mxn"],
            "start": iso(D3.replace(hour=8 + n)), "end": iso(D3.replace(hour=9 + n))})
        paid = client.post(f"/reservas/{r.json()['id']}/pago", json={"reference": f"T{n}", "amount": item["precio_mxn"]}).json()
        price = Decimal(item["precio_mxn"])
        assert Decimal(paid["commission"]) == (price * Decimal("0.20")).quantize(Decimal("0.01"), ROUND_HALF_UP)
        assert Decimal(paid["commission"]) + Decimal(paid["tutor_share"]) == price


def test_lab_transition_cases_map_to_state_machine(client, clock):
    actions = {r["accion_sugerida"] for r in rows("transiciones_prueba.csv")}
    assert {"completar", "cancelar", "repetir_aprobacion", "saltar_estado"} <= actions
    setup_world(client)
    client.post("/estudiantes", json={"id": "e2"})
    # completar: iniciar + checklist + finalizar
    _, s1 = booked_session(client, hour=9)
    clock.now = D3.replace(hour=9)
    assert run_session(client, s1)["state"] == "realizada"
    # repetir_aprobacion: finalizar dos veces -> 409
    assert client.post(f"/sesiones/{s1}/finalizar").status_code == 409
    # cancelar
    _, s2 = booked_session(client, hour=14, student="e2")
    clock.now = D3.replace(hour=1)
    assert client.post(f"/sesiones/{s2}/cancelar", json={"requester": "estudiante"}).json()["state"] == "cancelada"
    # saltar_estado: finalizar una sesión que no ha iniciado -> 409
    client.post("/estudiantes", json={"id": "e3"})
    _, s3 = booked_session(client, hour=16, student="e3")
    assert client.post(f"/sesiones/{s3}/finalizar").status_code == 409
