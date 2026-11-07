from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from ..application.ports import DashboardReadModel
from .orm import DisputaRow, PagoRow, SesionRow


class SqlDashboardReadModel(DashboardReadModel):
    """BR-0019: dashboard semanal leído directo de las tablas (lado Query de CQRS-light)."""

    def __init__(self, factory: sessionmaker):
        self._factory = factory

    def weekly(self, since: date, until: date) -> dict:
        a, b = datetime.combine(since, time.min), datetime.combine(until, time.max)
        with self._factory() as s:
            commissions = s.scalar(select(func.coalesce(func.sum(PagoRow.commission), 0))
                                   .where(PagoRow.updated_at.between(a, b), PagoRow.state.in_(["confirmado", "liquidado"]))
                                   ) or Decimal("0")
            sessions = s.execute(select(SesionRow.state, SesionRow.tutor_id, SesionRow.ratings)
                                 .where(SesionRow.start.between(a, b))).all()
            disp = dict(s.execute(select(DisputaRow.state, func.count()).where(DisputaRow.opened_at.between(a, b))
                                  .group_by(DisputaRow.state)).all())
        total = len(sessions)
        by_state: dict[str, int] = {}
        per_tutor: dict[str, list[int]] = {}
        for state, tutor_id, ratings in sessions:
            by_state[state] = by_state.get(state, 0) + 1
            for r in (ratings or {}).values():
                per_tutor.setdefault(tutor_id, []).append(r["stars"])
        all_ratings = [x for v in per_tutor.values() for x in v]
        n_disputes = sum(disp.values())
        return {
            "since": since, "until": until,
            "total_commission": format(Decimal(commissions).quantize(Decimal("0.01")), ".2f"),
            "sessions_total": total,
            "sessions_completed": by_state.get("realizada", 0) + by_state.get("cerrada", 0),
            "cancellations": by_state.get("cancelada", 0),
            "cancellation_rate": round(by_state.get("cancelada", 0) / total, 4) if total else 0.0,
            "tutor_absences": by_state.get("ausencia_tutor", 0),
            "disputes": {"abierta": disp.get("abierta", 0), "escalada": disp.get("escalada", 0),
                         "resuelta": disp.get("resuelta", 0), "total": n_disputes},
            "dispute_rate": round(n_disputes / total, 4) if total else 0.0,
            "average_rating": round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else 0.0,
            "average_rating_by_tutor": {t: round(sum(v) / len(v), 2) for t, v in sorted(per_tutor.items())},
        }
