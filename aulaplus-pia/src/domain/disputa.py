from datetime import datetime, timedelta
from uuid import uuid4

from .errors import EvidenceRequired
from .events import EventSource
from .state_machine import StateMachine
from .value_objects import DisputaState, Evidence, Role

S = DisputaState
_TABLE = {
    S.ABIERTA: {"escalate": S.ESCALADA},
    S.ESCALADA: {"resolve": S.RESUELTA},
}


class Disputa(EventSource):
    """Aggregate root. BR-0020: no se resuelve sin evidencia, decisión y responsable; BR-0011: ≤ 48 h."""

    SLA = timedelta(hours=48)

    def __init__(self, session_id: str, party: Role, now: datetime, id: str | None = None):
        self.id = id or str(uuid4())
        self.session_id, self.party = session_id, party
        self.opened_at = now
        self.machine = StateMachine("Disputa", S.ABIERTA, _TABLE)
        self.evidence: list[Evidence] = []
        self.decision: str | None = None
        self.responsible: str | None = None
        self._record("DisputaReportada", id=self.id, session_id=session_id)

    @property
    def state(self) -> DisputaState:
        return self.machine.state

    @property
    def due_at(self) -> datetime:
        return self.opened_at + self.SLA

    def overdue(self, now: datetime) -> bool:
        """BR-0011: sin resolver pasadas 48 h desde que se abrió."""
        return self.state is not DisputaState.RESUELTA and now > self.due_at

    def attach_evidence(self, reference: str, author: str = "") -> None:
        self.evidence.append(Evidence(reference, author))

    def escalate(self) -> None:
        self.machine.fire("escalate")
        self._record("DisputaEscalada", id=self.id)

    def resolve(self, decision: str, responsible: str) -> None:
        if not self.evidence or not decision or not responsible:
            raise EvidenceRequired("No se cierra sin evidencia, decisión y responsable (BR-0020)")
        self.machine.fire("resolve")
        self.decision, self.responsible = decision, responsible
        self._record("DisputaResuelta", id=self.id, responsible=responsible)
