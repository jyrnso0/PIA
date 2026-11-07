"""Máquina de estados explícita y reutilizable.

Cada aggregate declara su tabla de transiciones {estado: {evento: estado_destino}}.
Toda mutación de estado pasa por `fire`, que rechaza transiciones no declaradas.
"""
from enum import Enum
from typing import Generic, TypeVar

from .errors import InvalidTransition

S = TypeVar("S", bound=Enum)


class StateMachine(Generic[S]):
    def __init__(self, name: str, initial: S, table: dict[S, dict[str, S]]):
        self.name = name
        self.state = initial
        self._table = table

    def can(self, trigger: str) -> bool:
        return trigger in self._table.get(self.state, {})

    def allowed(self) -> list[str]:
        return sorted(self._table.get(self.state, {}))

    def fire(self, trigger: str) -> S:
        target = self._table.get(self.state, {}).get(trigger)
        if target is None:
            raise InvalidTransition(f"{self.name}: '{trigger}' no es válido desde {self.state.value}")
        self.state = target
        return target

    def restore(self, state: S) -> None:
        """Rehidratación desde persistencia (no es una transición de negocio)."""
        self.state = state
