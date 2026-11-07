from sqlalchemy import inspect, text

from src.infrastructure.database import init_schema, make_engine


def test_init_schema_adds_refund_evidence_to_existing_database():
    engine = make_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE pagos (
                    id VARCHAR(64) PRIMARY KEY,
                    reserva_id VARCHAR(64) UNIQUE NOT NULL,
                    amount NUMERIC(12, 2) NOT NULL,
                    state VARCHAR(20) NOT NULL,
                    commission NUMERIC(12, 2),
                    tutor_share NUMERIC(12, 2),
                    receipt VARCHAR(120),
                    refunded NUMERIC(12, 2) NOT NULL DEFAULT 0,
                    refund_reason VARCHAR(120),
                    refund_responsible VARCHAR(64),
                    refunded_at DATETIME,
                    updated_at DATETIME
                )
            """))
            connection.execute(text("""
                INSERT INTO pagos (id, reserva_id, amount, state)
                VALUES ('p-1', 'r-1', 300, 'confirmado')
            """))

        init_schema(engine)

        columns = {column["name"] for column in inspect(engine).get_columns("pagos")}
        assert "refund_evidence" in columns
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT refund_evidence FROM pagos WHERE id = 'p-1'")) == "[]"
    finally:
        engine.dispose()
