"""Eventos de dominio: hechos ya ocurridos. Cada aggregate root los acumula."""
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    name: str
    data: dict[str, Any] = field(default_factory=dict)


class EventSource:
    def _record(self, name: str, **data: Any) -> None:
        if not hasattr(self, "events"):
            self.events: list[DomainEvent] = []
        self.events.append(DomainEvent(name, data))

    def pull_events(self) -> list[DomainEvent]:
        events = list(getattr(self, "events", []))
        self.events = []
        return events
