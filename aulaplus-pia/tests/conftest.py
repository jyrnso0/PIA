import os
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.infrastructure.config import Settings
from src.infrastructure.container import build_container
from src.infrastructure.orm import Base


class FixedClock:
    def __init__(self, now: datetime):
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kw) -> None:
        self.now += timedelta(**kw)


@pytest.fixture
def clock():
    return FixedClock(datetime(2026, 11, 2, 9, 0))


@pytest.fixture
def container(clock):
    # En CI/Docker Compose se prueba contra PostgreSQL (TEST_DATABASE_URL); en local, SQLite en memoria.
    c = build_container(Settings(database_url=os.getenv("TEST_DATABASE_URL", "sqlite://")), clock)
    yield c
    Base.metadata.drop_all(c.engine)
    c.engine.dispose()


@pytest.fixture
def client(container, clock):
    return TestClient(create_app(container, clock))
