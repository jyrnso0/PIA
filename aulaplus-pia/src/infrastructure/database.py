from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .orm import Base


def make_engine(url: str) -> Engine:
    if url.startswith("sqlite") and (":memory:" in url or url.endswith("sqlite://")):
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


def init_schema(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    payment_columns = {column["name"] for column in inspect(engine).get_columns("pagos")}
    if "refund_evidence" not in payment_columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE pagos ADD COLUMN refund_evidence JSON NOT NULL DEFAULT '[]'")
            )


def session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False)
