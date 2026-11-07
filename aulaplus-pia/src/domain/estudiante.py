from .events import EventSource


class Estudiante(EventSource):
    """Aggregate root mínimo: cuenta de estudiante (activa/inactiva)."""

    def __init__(self, id: str, name: str = "", active: bool = True):
        self.id, self.name, self.active = id, name, active
