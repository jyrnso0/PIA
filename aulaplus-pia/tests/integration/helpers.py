from datetime import datetime, timedelta

SOP = {"X-Role": "soporte"}
ADM = {"X-Role": "administrador"}
D3 = datetime(2026, 11, 3)


def iso(dt):
    return dt.isoformat()


def setup_world(client, tutor="t1", student="e1", subject="Cálculo", modalities=("virtual", "presencial")):
    assert client.post("/tutores", json={"id": tutor, "name": "Ana"}).status_code == 201
    assert client.post("/estudiantes", json={"id": student, "name": "Luis"}).status_code == 201
    r = client.put(f"/tutores/{tutor}/disponibilidad", json={
        "subject": subject, "modalities": list(modalities),
        "slots": [{"start": iso(D3.replace(hour=8)), "end": iso(D3.replace(hour=20))}]})
    assert r.status_code == 200, r.text


def book(client, hour=10, hours=1, tutor="t1", student="e1", subject="Cálculo", amount="300.00", modality="virtual"):
    body = {"student_id": student, "subject": subject, "modality": modality, "amount": amount,
            "start": iso(D3.replace(hour=hour)), "end": iso(D3.replace(hour=hour) + timedelta(hours=hours))}
    if tutor:
        body["tutor_id"] = tutor
    return client.post("/reservas", json=body)


def booked_session(client, **kw):
    """Reserva + pago -> devuelve (reserva_id, session_id)."""
    r = book(client, **kw)
    assert r.status_code == 201, r.text
    rid = r.json()["id"]
    p = client.post(f"/reservas/{rid}/pago", json={"reference": "TXN-1", "amount": kw.get("amount", "300.00")})
    assert p.status_code == 200, p.text
    return rid, p.json()["session_id"]


def run_session(client, sid):
    """Presencia, inicio, checklist de ambos y fin."""
    assert client.post(f"/sesiones/{sid}/iniciar").status_code == 200
    for party in ("tutor", "estudiante"):
        assert client.post(f"/sesiones/{sid}/checklist", json={"party": party}).status_code == 200
    r = client.post(f"/sesiones/{sid}/finalizar")
    assert r.status_code == 200, r.text
    return r.json()
