"""Errores de negocio. `code` es estable y lo usa la API para responder 404/409/422."""


class DomainError(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, message: str = ""):
        super().__init__(message or self.code)


class NotFound(DomainError):
    code = "NOT_FOUND"


class InvalidTransition(DomainError):
    code = "INVALID_TRANSITION"


class DeadlineExpired(DomainError):
    code = "DEADLINE_EXPIRED"  # BR-0001, BR-0007


class ScheduleUnavailable(DomainError):
    code = "SCHEDULE_UNAVAILABLE"  # BR-0006


class EvidenceRequired(DomainError):
    code = "EVIDENCE_REQUIRED"  # BR-0020


class RuleViolation(DomainError):
    code = "RULE_VIOLATION"
