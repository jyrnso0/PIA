"""Contratos HTTP (Pydantic). Validan forma y tipos; las reglas de negocio las aplica el dominio."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

from ..domain.value_objects import Modality, Role


def _naive_utc(v: datetime) -> datetime:
    return v.astimezone(timezone.utc).replace(tzinfo=None) if v.tzinfo else v


UtcDatetime = Annotated[datetime, AfterValidator(_naive_utc)]


class TutorIn(BaseModel):
    id: str = Field(min_length=1, examples=["tutor-1"])
    name: str = ""


class StudentIn(BaseModel):
    id: str = Field(min_length=1, examples=["est-1"])
    name: str = ""
    active: bool = True


class SlotIn(BaseModel):
    start: UtcDatetime
    end: UtcDatetime


class AvailabilityIn(BaseModel):
    subject: str = Field(min_length=1, examples=["Cálculo"])
    modalities: list[Modality] = [Modality.VIRTUAL]
    slots: list[SlotIn] = Field(min_length=1)


class ReservaIn(BaseModel):
    student_id: str
    tutor_id: str | None = Field(default=None, description="Si se omite, la plataforma asigna un tutor disponible")
    subject: str
    topic: str = ""
    modality: Modality = Modality.VIRTUAL
    start: UtcDatetime
    end: UtcDatetime
    amount: Decimal = Field(gt=0, examples=["300.00"])


class PagoIn(BaseModel):
    reference: str = Field(min_length=1, examples=["TXN-0001"])
    amount: Decimal = Field(gt=0)


class ChecklistIn(BaseModel):
    party: Role


class CancelIn(BaseModel):
    requester: Role
    reported_situation: str | None = None
    responsible: str = "soporte-1"


class TutorAbsenceIn(BaseModel):
    responsible: str = Field(min_length=1)


class PartyIn(BaseModel):
    party: Role


class ConnectionCutIn(BaseModel):
    minutes: int = Field(ge=0, description="Minutos transcurridos antes del corte")


class ExtensionIn(BaseModel):
    by: Role
    minutes: int = Field(gt=0, le=240)


class AcceptIn(BaseModel):
    by: Role


class ModalityIn(BaseModel):
    by: Role
    modality: Modality


class ReportCommentIn(BaseModel):
    author: Role = Role.STUDENT


class RatingIn(BaseModel):
    by: Role
    stars: int = Field(ge=1, le=5)
    comment: str = ""


class DisputeIn(BaseModel):
    session_id: str
    party: Role


class EvidenceIn(BaseModel):
    reference: str = Field(min_length=1)
    author: str = ""


class ResolveIn(BaseModel):
    responsible: str
    decision: str
    refund_percent: int = Field(default=0, ge=0, le=100)


class ReactivateIn(BaseModel):
    responsible: str
