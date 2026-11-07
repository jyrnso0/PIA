"""Modelo relacional (SQLAlchemy 2.0). Las tablas son un detalle de infraestructura."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EstudianteRow(Base):
    __tablename__ = "estudiantes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class TutorRow(Base):
    __tablename__ = "tutores"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    state: Mapped[str] = mapped_column(String(20))
    availability: Mapped[dict] = mapped_column(JSON, default=dict)
    absences: Mapped[list] = mapped_column(JSON, default=list)
    rating_sum: Mapped[int] = mapped_column(Integer, default=0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)


class ReservaRow(Base):
    __tablename__ = "reservas"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tutor_id: Mapped[str] = mapped_column(String(64), index=True)
    student_id: Mapped[str] = mapped_column(String(64), index=True)
    subject: Mapped[str] = mapped_column(String(80))
    topic: Mapped[str] = mapped_column(String(120), default="")
    modality: Mapped[str] = mapped_column(String(20))
    start: Mapped[datetime] = mapped_column(DateTime)
    end: Mapped[datetime] = mapped_column(DateTime)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    state: Mapped[str] = mapped_column(String(20), index=True)


class SesionRow(Base):
    __tablename__ = "sesiones"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    reserva_id: Mapped[str] = mapped_column(String(64), unique=True)
    tutor_id: Mapped[str] = mapped_column(String(64), index=True)
    student_id: Mapped[str] = mapped_column(String(64))
    start: Mapped[datetime] = mapped_column(DateTime)
    end: Mapped[datetime] = mapped_column(DateTime)
    state: Mapped[str] = mapped_column(String(24), index=True)
    modality: Mapped[str] = mapped_column(String(20), default="virtual")
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    presence: Mapped[dict] = mapped_column(JSON, default=dict)
    pending_extension: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    pending_modality: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    checklist: Mapped[dict] = mapped_column(JSON, default=dict)
    ratings: Mapped[dict] = mapped_column(JSON, default=dict)
    cancellation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PagoRow(Base):
    __tablename__ = "pagos"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    reserva_id: Mapped[str] = mapped_column(String(64), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    state: Mapped[str] = mapped_column(String(20), index=True)
    commission: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    tutor_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    receipt: Mapped[str | None] = mapped_column(String(120), nullable=True)
    refunded: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    refund_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    refund_responsible: Mapped[str | None] = mapped_column(String(64), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    refund_evidence: Mapped[list] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DisputaRow(Base):
    __tablename__ = "disputas"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    party: Mapped[str] = mapped_column(String(20))
    opened_at: Mapped[datetime] = mapped_column(DateTime)
    state: Mapped[str] = mapped_column(String(20), index=True)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    decision: Mapped[str | None] = mapped_column(String(500), nullable=True)
    responsible: Mapped[str | None] = mapped_column(String(64), nullable=True)


class OutboxRow(Base):
    """Eventos de dominio persistidos en la misma transacción (outbox)."""
    __tablename__ = "domain_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime)
