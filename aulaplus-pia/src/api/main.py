"""API REST de AulaPlus (FastAPI). Swagger en /docs, OpenAPI en /openapi.json."""
from datetime import date, datetime
from typing import Callable

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
form fastapi.middleware.cors import CORSMiddleware
from ..domain import errors as E
from ..domain.value_objects import Role, Schedule
from ..infrastructure.config import Settings
from ..infrastructure.container import Container, build_container
from . import schemas as S

TAGS = [
    {"name": "Tutores", "description": "Alta, disponibilidad por materia (BR-0015), perfil público (BR-0016), suspensión (BR-0018)"},
    {"name": "Reservas", "description": "Reserva, pago en 15 min y liberación (BR-0001, BR-0005, BR-0006)"},
    {"name": "Sesiones", "description": "Ciclo de vida, cancelación, ausencias, extensión, modalidad, calificación"},
    {"name": "Disputas", "description": "Reporte, evidencia, escalamiento y resolución (BR-0007, 0011, 0017, 0020)"},
    {"name": "Dashboard", "description": "Indicadores semanales para Administración (BR-0019)"},
    {"name": "Sistema", "description": "Salud del servicio y notificaciones"},
]

STATUS = {E.NotFound: 404, E.InvalidTransition: 409, E.DeadlineExpired: 409,
          E.ScheduleUnavailable: 409, E.EvidenceRequired: 422, E.RuleViolation: 422}


def require(*allowed: Role):
    """Control de acceso por rol (RNF). El rol llega en la cabecera X-Role (simulación de autenticación)."""
    def dep(x_role: str | None = Header(default=None, description="soporte | administrador | estudiante | tutor")):
        if x_role is None:
            raise HTTPException(status_code=401, detail="Falta la cabecera X-Role")
        if x_role not in {r.value for r in allowed}:
            raise HTTPException(status_code=403, detail=f"Rol '{x_role}' sin permiso para esta operación")
        return x_role
    return Depends(dep)


def create_app(container: Container | None = None, clock: Callable[[], datetime] = datetime.utcnow) -> FastAPI:
    app = FastAPI(title="AulaPlus API", version="1.0.0", openapi_tags=TAGS,
                  description="Plataforma de tutorías académicas: reservas, pagos, sesiones y disputas.")
    c = container or build_container(Settings.from_env(), clock)
    app.state.container = c

    @app.exception_handler(E.DomainError)
    async def domain_error(_: Request, exc: E.DomainError):
        status = next((s for t, s in STATUS.items() if isinstance(exc, t)), 400)
        return JSONResponse(status_code=status, content={"error": exc.code, "detail": str(exc)})

    def schedule(start, end) -> Schedule:
        try:
            return Schedule(start, end)
        except ValueError as e:
            raise E.RuleViolation(str(e)) from e

    @app.get("/health", tags=["Sistema"])
    def health():
        return {"status": "ok"}

    @app.get("/notificaciones", tags=["Sistema"], summary="Avisos de plazos por vencer")
    def notifications():
        return c.notifications.upcoming()

    # ---- Tutores / estudiantes ------------------------------------------------------------
    @app.post("/tutores", status_code=201, tags=["Tutores"])
    def register_tutor(body: S.TutorIn):
        return c.tutors.register(body.id, body.name)

    @app.post("/estudiantes", status_code=201, tags=["Tutores"])
    def register_student(body: S.StudentIn):
        return c.tutors.register_student(body.id, body.name, body.active)

    @app.put("/tutores/{tutor_id}/disponibilidad", tags=["Tutores"])
    def availability(tutor_id: str, body: S.AvailabilityIn):
        slots = [schedule(s.start, s.end) for s in body.slots]
        return c.tutors.set_availability(tutor_id, body.subject, slots, body.modalities)

    @app.get("/tutores/{tutor_id}/perfil", tags=["Tutores"])
    def profile(tutor_id: str):
        return c.tutors.public_profile(tutor_id)

    @app.get("/tutores/{tutor_id}/estado", tags=["Tutores"], dependencies=[require(Role.ADMIN)])
    def tutor_status(tutor_id: str):
        return c.tutors.status(tutor_id)

    @app.post("/tutores/{tutor_id}/reactivar", tags=["Tutores"], dependencies=[require(Role.ADMIN)])
    def reactivate(tutor_id: str, body: S.ReactivateIn):
        return c.tutors.reactivate(tutor_id, body.responsible)

    # ---- Reservas ---------------------------------------------------------------------------
    @app.post("/reservas", status_code=201, tags=["Reservas"])
    def reserve(body: S.ReservaIn):
        return c.bookings.reserve(body.student_id, body.tutor_id, body.subject, body.modality,
                                  schedule(body.start, body.end), body.amount, body.topic)

    @app.get("/reservas/{reserva_id}", tags=["Reservas"])
    def get_reserva(reserva_id: str):
        return c.bookings.get(reserva_id)

    @app.post("/reservas/{reserva_id}/pago", tags=["Reservas"])
    def pay(reserva_id: str, body: S.PagoIn):
        return c.bookings.pay(reserva_id, body.reference, body.amount)

    @app.post("/reservas/liberar-vencidas", tags=["Reservas"])
    def release():
        return {"released": c.bookings.release_expired()}

    # ---- Sesiones ---------------------------------------------------------------------------
    @app.get("/sesiones/{sid}", tags=["Sesiones"])
    def get_session(sid: str):
        return c.sessions.get(sid)

    @app.post("/sesiones/{sid}/presencia", tags=["Sesiones"], summary="Confirmar presencia (BR-0008)")
    def presence(sid: str, body: S.PartyIn):
        return c.sessions.confirm_presence(sid, body.party)

    @app.post("/sesiones/{sid}/iniciar", tags=["Sesiones"])
    def start(sid: str):
        return c.sessions.start(sid)

    @app.post("/sesiones/{sid}/checklist", tags=["Sesiones"])
    def checklist(sid: str, body: S.PartyIn):
        return c.sessions.confirm_checklist(sid, body.party)

    @app.post("/sesiones/{sid}/finalizar", tags=["Sesiones"])
    def finish(sid: str):
        return c.sessions.finish(sid)

    @app.post("/sesiones/{sid}/corte-conexion", tags=["Sesiones"], summary="Falla de conexión (BR-0010)")
    def connection_cut(sid: str, body: S.ConnectionCutIn):
        return c.sessions.connection_cut(sid, body.minutes)

    @app.post("/sesiones/{sid}/cancelar", tags=["Sesiones"])
    def cancel(sid: str, body: S.CancelIn):
        return c.sessions.cancel(sid, body.requester, body.reported_situation, body.responsible)

    @app.post("/sesiones/{sid}/ausencia-tutor", tags=["Sesiones"], dependencies=[require(Role.SUPPORT, Role.SYSTEM)])
    def tutor_absence(sid: str, body: S.TutorAbsenceIn):
        return c.sessions.report_tutor_absence(sid, body.responsible)

    @app.post("/sesiones/{sid}/ausencia-estudiante", tags=["Sesiones"])
    def student_absence(sid: str):
        return c.sessions.report_student_absence(sid)

    @app.post("/sesiones/{sid}/extension", tags=["Sesiones"], summary="Solicitar extensión (BR-0012)")
    def propose_extension(sid: str, body: S.ExtensionIn):
        return c.sessions.propose_extension(sid, body.by, body.minutes)

    @app.post("/sesiones/{sid}/extension/aceptar", tags=["Sesiones"])
    def accept_extension(sid: str, body: S.AcceptIn):
        return c.sessions.accept_extension(sid, body.by)

    @app.post("/sesiones/{sid}/modalidad", tags=["Sesiones"], summary="Solicitar cambio de modalidad (BR-0013)")
    def propose_modality(sid: str, body: S.ModalityIn):
        return c.sessions.propose_modality(sid, body.by, body.modality)

    @app.post("/sesiones/{sid}/modalidad/aceptar", tags=["Sesiones"])
    def accept_modality(sid: str, body: S.AcceptIn):
        return c.sessions.accept_modality(sid, body.by)

    @app.post("/sesiones/{sid}/calificaciones", tags=["Sesiones"])
    def rate(sid: str, body: S.RatingIn):
        return c.sessions.rate(sid, body.by, body.stars, body.comment)

    @app.post("/sesiones/{sid}/comentarios/reportar", tags=["Sesiones"], summary="Reportar comentario (BR-0016)")
    def report_comment(sid: str, body: S.ReportCommentIn):
        return c.sessions.report_comment(sid, body.author)

    @app.post("/sesiones/cerrar-vencidas", tags=["Sesiones"])
    def close_overdue():
        return {"closed": c.sessions.close_overdue()}

    # ---- Disputas -----------------------------------------------------------------------------
    @app.post("/disputas", status_code=201, tags=["Disputas"])
    def report(body: S.DisputeIn):
        return c.disputes.report(body.session_id, body.party)

    @app.get("/disputas/vencidas", tags=["Disputas"], dependencies=[require(Role.SUPPORT, Role.ADMIN)],
             summary="Disputas fuera del SLA de 48 h (BR-0011)")
    def overdue_disputes():
        return c.disputes.overdue()

    @app.get("/disputas/{did}", tags=["Disputas"])
    def get_dispute(did: str):
        return c.disputes.get(did)

    @app.post("/disputas/{did}/evidencia", tags=["Disputas"])
    def evidence(did: str, body: S.EvidenceIn):
        return c.disputes.attach_evidence(did, body.reference, body.author)

    @app.post("/disputas/{did}/escalar", tags=["Disputas"])
    def escalate(did: str):
        return c.disputes.escalate(did)

    @app.post("/disputas/{did}/resolver", tags=["Disputas"], dependencies=[require(Role.SUPPORT)],
              summary="Resolver disputa (solo Soporte; exige evidencia)")
    def resolve(did: str, body: S.ResolveIn):
        return c.disputes.resolve(did, body.responsible, body.decision, body.refund_percent)

    # ---- Dashboard ----------------------------------------------------------------------------
    @app.get("/dashboard/semanal", tags=["Dashboard"], dependencies=[require(Role.ADMIN)])
    def weekly(since: date | None = None, until: date | None = None):
        return c.dashboard.weekly(since, until)

    return app


def app_factory() -> FastAPI:  # uvicorn --factory src.api.main:app_factory
    return create_app()
