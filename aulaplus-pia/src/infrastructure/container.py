"""Raíz de composición: aquí (y solo aquí) se eligen las implementaciones concretas."""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.engine import Engine

from ..application.ports import Clock
from ..application.services import (
    BookingService,
    DashboardService,
    DisputeService,
    NotificationService,
    SessionService,
    TutorService,
)
from .config import Settings
from .database import init_schema, make_engine, session_factory
from .payment_gateway import FakePaymentGateway
from .read_model import SqlDashboardReadModel
from .unit_of_work import SqlUnitOfWork


@dataclass
class Container:
    engine: Engine
    tutors: TutorService
    bookings: BookingService
    sessions: SessionService
    disputes: DisputeService
    dashboard: DashboardService
    notifications: NotificationService


def build_container(settings: Settings | None = None, clock: Clock = datetime.utcnow) -> Container:
    settings = settings or Settings.from_env()
    engine = make_engine(settings.database_url)
    init_schema(engine)
    factory = session_factory(engine)
    uow = SqlUnitOfWork(factory, clock)
    return Container(
        engine=engine,
        tutors=TutorService(uow, clock),
        bookings=BookingService(uow, FakePaymentGateway(), clock),
        sessions=SessionService(uow, clock),
        disputes=DisputeService(uow, clock),
        dashboard=DashboardService(SqlDashboardReadModel(factory), clock),
        notifications=NotificationService(uow, clock),
    )
