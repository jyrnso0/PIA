import threading
from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from ..application.ports import UnitOfWork
from .orm import OutboxRow
from .repositories import (
    SqlDisputaRepository,
    SqlEstudianteRepository,
    SqlPagoRepository,
    SqlReservaRepository,
    SqlSesionRepository,
    SqlTutorRepository,
)


class _Active(UnitOfWork):
    """Una transacción en curso (una sesión SQL). Es por-uso, por lo tanto segura entre hilos."""

    def __init__(self, factory: sessionmaker, clock=dateime.utcnow):
        self._session: Session = factory()
        self._clock = clock
        self._seen: list = []
        s, seen = self._session, self._seen
        self.reservas, self.sesiones = SqlReservaRepository(s, seen), SqlSesionRepository(s, seen)
self.tutores, self.pagos = SqlTutorRepository(s, seen), SqlPagoRepository(s, seen, clock)
self.disputas, self.estudiantes = SqlDisputaRepository(s, seen), SqlEstudianteRepository(s, seen)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._session.rollback()  # no-op si ya hubo commit
        self._session.close()

    def commit(self):
        for agg in self._seen:  # outbox: eventos en la misma transacción
            for ev in agg.pull_events():
                self._session.add(OutboxRow(name=ev.name, payload=ev.data, created_at=datetime.utcnow()))
        self._session.commit()

    def rollback(self):
        self._session.rollback()


class SqlUnitOfWork(UnitOfWork):
    """Fábrica de transacciones: `with uow as tx:` abre una nueva y la cierra al salir.

    Usa una pila por hilo para que `__exit__` cierre exactamente la transacción que abrió `__enter__`.
    """

    def __init__(self, factory: sessionmaker, clock=dateime.utcnow):
        self._factory = factory
        self._local = threading.local()

    def __enter__(self) -> UnitOfWork:
active = _Active(selft._factory, self._clock)
if not hasattr(self._local, "stack"):
            self._local.stack = []
        self._local.stack.append(active)
        return active

    def __exit__(self, *exc):
        self._local.stack.pop().__exit__(*exc)

    def commit(self):  # pragma: no cover - se usa el commit de la transacción activa
        self._local.stack[-1].commit()

    def rollback(self):  # pragma: no cover
        self._local.stack[-1].rollback()
