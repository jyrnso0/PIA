"""Value Objects y enumeraciones (inmutables, sin identidad)."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum


class Role(Enum):
    STUDENT = "estudiante"
    TUTOR = "tutor"
    SUPPORT = "soporte"
    ADMIN = "administrador"
    SYSTEM = "sistema"


class Modality(Enum):
    PRESENCIAL = "presencial"
    VIRTUAL = "virtual"


class ReservaState(Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    LIBERADA = "liberada"
    CANCELADA = "cancelada"


class SesionState(Enum):
    PROGRAMADA = "programada"
    EN_CURSO = "en_curso"
    REALIZADA = "realizada"
    CERRADA = "cerrada"
    INTERRUMPIDA = "interrumpida"
    CANCELADA = "cancelada"
    AUSENCIA_TUTOR = "ausencia_tutor"
    AUSENCIA_ESTUDIANTE = "ausencia_estudiante"


class PagoState(Enum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    REEMBOLSADO = "reembolsado"
    LIQUIDADO = "liquidado"


class DisputaState(Enum):
    ABIERTA = "abierta"
    ESCALADA = "escalada"
    RESUELTA = "resuelta"


class AccountState(Enum):
    ACTIVO = "activo"
    SUSPENDIDO = "suspendido"


@dataclass(frozen=True)
class Money:
    """Importe en MXN con precisión decimal (ROUND_HALF_UP a centavos)."""
    amount: Decimal

    def __post_init__(self):
        object.__setattr__(self, "amount", Decimal(str(self.amount)).quantize(Decimal("0.01"), ROUND_HALF_UP))

    def times(self, factor) -> "Money":
        return Money(self.amount * Decimal(str(factor)))

    def __add__(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount)

    def __sub__(self, other: "Money") -> "Money":
        return Money(self.amount - other.amount)


@dataclass(frozen=True)
class Schedule:
    """Intervalo [start, end): una sesión puede empezar justo cuando termina otra."""
    start: datetime
    end: datetime

    def __post_init__(self):
        if self.end <= self.start:
            raise ValueError("El fin del horario debe ser posterior al inicio")

    def overlaps(self, other: "Schedule") -> bool:
        return self.start < other.end and other.start < self.end


@dataclass(frozen=True)
class PaymentDeadline:
    """BR-0001: la reserva vive 15 minutos esperando el pago."""
    expires_at: datetime

    def expired(self, now: datetime) -> bool:
        return now > self.expires_at


@dataclass(frozen=True)
class PaymentBreakdown:
    """BR-0005: comisión del 20 % para la plataforma, 80 % para el tutor."""
    commission: Money
    tutor_share: Money


@dataclass(frozen=True)
class Penalty:
    amount: Money
    charged_to: Role


@dataclass
class Cancellation:
    """Quién cancela y con cuánta anticipación (BR-0004)."""
    requester: Role
    notice: timedelta
    penalty: Penalty | None = None


@dataclass(frozen=True)
class Evidence:
    reference: str
    author: str = ""


@dataclass(frozen=True)
class Rating:
    by: Role
    stars: int
    comment: str = ""
    reported: bool = False  # BR-0016: comentario reportado como inapropiado

    def __post_init__(self):
        if not 1 <= self.stars <= 5:
            raise ValueError("La calificación va de 1 a 5")
