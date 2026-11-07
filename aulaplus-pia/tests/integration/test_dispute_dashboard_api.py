"""US-07, 11, 17, 19, 20: disputas, evidencia, reembolso formal y dashboard."""
from .helpers import ADM, D3, SOP, booked_session, run_session, setup_world


def finished_session(client, clock, **kw):
    rid, sid = booked_session(client, **kw)
    clock.now = D3.replace(hour=10)
    run_session(client, sid)
    clock.now = D3.replace(hour=12)
    return rid, sid


def test_dispute_full_flow_with_evidence_and_refund_br0017_br0020(client, clock, container):
    setup_world(client)
    rid, sid = finished_session(client, clock)
    d = client.post("/disputas", json={"session_id": sid, "party": "estudiante"})
    assert d.status_code == 201 and d.json()["state"] == "abierta"
    did = d.json()["id"]
    assert client.post(f"/disputas/{did}/escalar").json()["state"] == "escalada"       # BR-0011
    body = {"responsible": "soporte-1", "decision": "Reembolso parcial", "refund_percent": 50}
    r = client.post(f"/disputas/{did}/resolver", json=body, headers=SOP)
    assert r.status_code == 422 and r.json()["error"] == "EVIDENCE_REQUIRED"             # BR-0020
    assert client.post(f"/disputas/{did}/evidencia", json={"reference": "captura.png", "author": "e1"}).status_code == 200
    r = client.post(f"/disputas/{did}/resolver", json=body, headers=SOP)
    assert r.status_code == 200 and r.json()["state"] == "resuelta" and r.json()["responsible"] == "soporte-1"
    with container.bookings._uow as uow:
        p = uow.pagos.by_reserva(rid)
    assert p.refunded.amount == 150 and p.refund_responsible == "soporte-1" and p.refund_reason == "disputa"
    assert p.refund_evidence == ["captura.png"]                                          # BR-0017: evidencia
    assert client.post(f"/disputas/{did}/resolver", json=body, headers=SOP).status_code == 409   # ya resuelta


def test_only_support_can_resolve_disputes(client, clock):
    setup_world(client)
    _, sid = finished_session(client, clock)
    did = client.post("/disputas", json={"session_id": sid, "party": "tutor"}).json()["id"]
    client.post(f"/disputas/{did}/evidencia", json={"reference": "x"})
    client.post(f"/disputas/{did}/escalar")
    body = {"responsible": "a", "decision": "ok"}
    assert client.post(f"/disputas/{did}/resolver", json=body).status_code == 401
    assert client.post(f"/disputas/{did}/resolver", json=body, headers=ADM).status_code == 403
    assert client.post(f"/disputas/{did}/resolver", json=body, headers=SOP).status_code == 200


def test_dispute_window_24h_br0007(client, clock):
    setup_world(client)
    _, sid = finished_session(client, clock)
    clock.now = D3.replace(hour=11) + __import__("datetime").timedelta(hours=24)
    assert client.post("/disputas", json={"session_id": sid, "party": "estudiante"}).status_code == 201
    clock.advance(minutes=1)
    r = client.post("/disputas", json={"session_id": sid, "party": "estudiante"})
    assert r.status_code == 409 and r.json()["error"] == "DEADLINE_EXPIRED"
    assert client.post("/disputas", json={"session_id": "nope", "party": "tutor"}).status_code == 404


def test_overdue_disputes_after_48h_br0011(client, clock):
    setup_world(client)
    _, sid = finished_session(client, clock)
    did = client.post("/disputas", json={"session_id": sid, "party": "estudiante"}).json()["id"]
    client.post(f"/disputas/{did}/escalar")
    assert client.get("/disputas/vencidas", headers=SOP).json() == []
    clock.advance(hours=37)
    assert [n["type"] for n in client.get("/notificaciones").json()] == ["SLA_SOPORTE_POR_VENCER"]
    clock.advance(hours=12)
    overdue = client.get("/disputas/vencidas", headers=SOP).json()
    assert len(overdue) == 1 and overdue[0]["overdue"] is True
    assert client.get("/disputas/vencidas").status_code == 401


def test_dispute_window_notification(client, clock):
    setup_world(client)
    _, sid = finished_session(client, clock)
    clock.now = D3.replace(hour=11) + __import__("datetime").timedelta(hours=22, minutes=30)
    assert "DISPUTA_POR_VENCER" in [n["type"] for n in client.get("/notificaciones").json()]


def test_refund_percent_validation(client, clock):
    setup_world(client)
    _, sid = finished_session(client, clock)
    did = client.post("/disputas", json={"session_id": sid, "party": "estudiante"}).json()["id"]
    client.post(f"/disputas/{did}/evidencia", json={"reference": "x"})
    client.post(f"/disputas/{did}/escalar")
    r = client.post(f"/disputas/{did}/resolver", json={"responsible": "s", "decision": "d", "refund_percent": 150},
                    headers=SOP)
    assert r.status_code == 422


def test_dashboard_br0019_requires_admin_and_reports_kpis(client, clock):
    setup_world(client)
    client.post("/estudiantes", json={"id": "e2"})
    client.post("/estudiantes", json={"id": "e3"})
    _, s1 = booked_session(client, hour=9)
    clock.now = D3.replace(hour=9)
    run_session(client, s1)
    client.post(f"/sesiones/{s1}/calificaciones", json={"by": "estudiante", "stars": 5})
    client.post(f"/sesiones/{s1}/calificaciones", json={"by": "tutor", "stars": 5})
    clock.now = D3.replace(hour=1)
    _, s2 = booked_session(client, hour=12, student="e2")
    client.post(f"/sesiones/{s2}/cancelar", json={"requester": "estudiante"})
    clock.now = D3.replace(hour=13)
    client.post("/disputas", json={"session_id": s1, "party": "tutor"})
    assert client.get("/dashboard/semanal").status_code == 401
    assert client.get("/dashboard/semanal", headers={"X-Role": "tutor"}).status_code == 403
    r = client.get("/dashboard/semanal", params={"since": "2026-11-01", "until": "2026-11-07"}, headers=ADM)
    d = r.json()
    assert r.status_code == 200
    assert d["sessions_total"] == 2 and d["cancellations"] == 1 and d["cancellation_rate"] == 0.5
    assert d["sessions_completed"] == 1 and d["disputes"]["abierta"] == 1 and d["dispute_rate"] == 0.5
    assert d["average_rating"] == 5.0 and d["average_rating_by_tutor"] == {"t1": 5.0}
    assert float(d["total_commission"]) >= 60.0
    default = client.get("/dashboard/semanal", headers=ADM)
    assert default.status_code == 200
