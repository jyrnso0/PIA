"""Persistencia: los aggregates sobreviven al ciclo guardar/cargar y el outbox registra eventos."""
from sqlalchemy import select

from src.infrastructure.config import Settings
from src.infrastructure.container import build_container
from src.infrastructure.database import session_factory
from src.infrastructure.orm import OutboxRow

from .helpers import booked_session, setup_world


def test_domain_events_are_stored_in_outbox_in_same_transaction(client, container):
    setup_world(client)
    booked_session(client)
    with session_factory(container.engine)() as s:
        names = [n for (n,) in s.execute(select(OutboxRow.name))]
    for expected in ("ReservaCreada", "ReservaConfirmada", "PagoConfirmado", "ComisionCalculada",
                     "SesionProgramada", "DisponibilidadActualizada"):
        assert expected in names


def test_failed_transaction_leaves_no_partial_data(client, container):
    setup_world(client)
    r = client.post("/reservas", json={"student_id": "e1", "tutor_id": "t1", "subject": "Cálculo",
                                       "amount": "300", "start": "2026-11-03T22:00:00", "end": "2026-11-03T23:00:00"})
    assert r.status_code == 422
    with session_factory(container.engine)() as s:
        assert not [n for (n,) in s.execute(select(OutboxRow.name)) if n == "ReservaCreada"]


def test_data_persists_across_container_rebuilds(tmp_path, clock):
    url = f"sqlite:///{tmp_path}/t.db"
    c1 = build_container(Settings(database_url=url), clock)
    c1.tutors.register("t9", "Persistente")
    c1.engine.dispose()
    c2 = build_container(Settings(database_url=url), clock)
    assert c2.tutors.public_profile("t9")["name"] == "Persistente"
    c2.engine.dispose()


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    assert Settings.from_env().database_url == "postgresql+psycopg2://u:p@h/db"
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
    assert Settings.from_env().database_url.startswith("postgresql+psycopg2://")
    monkeypatch.delenv("DATABASE_URL")
    assert Settings.from_env().database_url.startswith("sqlite")
