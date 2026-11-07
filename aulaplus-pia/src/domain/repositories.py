"""Puertos de persistencia (Repository). Viven en el dominio y no conocen SQL."""
from abc import ABC, abstractmethod
from datetime import datetime

from .disputa import Disputa
from .pago import Pago
from .reserva import Reserva
from .sesion import Sesion
from .tutor import Tutor


class ReservaRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> Reserva: ...
    @abstractmethod
    def save(self, reserva: Reserva) -> None: ...
    @abstractmethod
    def pending_expired(self, now: datetime) -> list[Reserva]: ...


class SesionRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> Sesion: ...
    @abstractmethod
    def save(self, sesion: Sesion) -> None: ...
    @abstractmethod
    def by_tutor(self, tutor_id: str) -> list[Sesion]: ...
    @abstractmethod
    def overdue_for_close(self, now: datetime) -> list[Sesion]: ...
    @abstractmethod
    def by_reserva(self, reserva_id: str) -> Sesion: ...
    @abstractmethod
    def recently_finished(self, since: datetime) -> list[Sesion]: ...


class TutorRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> Tutor: ...
    @abstractmethod
    def all(self) -> list[Tutor]: ...
    @abstractmethod
    def save(self, tutor: Tutor) -> None: ...


class PagoRepository(ABC):
    @abstractmethod
    def by_reserva(self, reserva_id: str) -> Pago: ...
    @abstractmethod
    def save(self, pago: Pago) -> None: ...


class DisputaRepository(ABC):
    @abstractmethod
    def get(self, id: str) -> Disputa: ...
    @abstractmethod
    def unresolved(self) -> list[Disputa]: ...
    @abstractmethod
    def has_open_for_session(self, session_id: str) -> bool: ...
    @abstractmethod
    def save(self, disputa: Disputa) -> None: ...


class EstudianteRepository(ABC):
    @abstractmethod
    def get(self, id: str): ...
    @abstractmethod
    def save(self, estudiante) -> None: ...
