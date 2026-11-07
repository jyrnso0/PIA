"""Puertos de la capa de aplicación: Unit of Work, pasarela de pago, reloj y read models."""
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Callable

from ..domain.repositories import (
    DisputaRepository,
    EstudianteRepository,
    PagoRepository,
    ReservaRepository,
    SesionRepository,
    TutorRepository,
)

Clock = Callable[[], datetime]


class UnitOfWork(ABC):
    """Frontera transaccional: o se guarda todo, o no se guarda nada."""

    reservas: ReservaRepository
    sesiones: SesionRepository
    tutores: TutorRepository
    pagos: PagoRepository
    disputas: DisputaRepository
    estudiantes: EstudianteRepository

    @abstractmethod
    def __enter__(self) -> "UnitOfWork": ...
    @abstractmethod
    def __exit__(self, *exc) -> None: ...
    @abstractmethod
    def commit(self) -> None: ...
    @abstractmethod
    def rollback(self) -> None: ...


class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, reference: str, amount) -> str:
        """Cobra y devuelve la referencia del comprobante."""


class DashboardReadModel(ABC):
    @abstractmethod
    def weekly(self, since: date, until: date) -> dict: ...
