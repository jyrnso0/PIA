# Architecture Decision Records (ADRs)

Formato: contexto → decisión → consecuencias. Las ADR-01…07 provienen del informe de la Unidad 3; ADR-08…13 son nuevas del PIA.

| ID | Decisión | Estado |
|---|---|---|
| ADR-01 | Aggregates DDD: Reserva, Sesion, Pago, Disputa, Tutor (+ Estudiante) como únicas fronteras de consistencia | Aceptada (U3) |
| ADR-02 | Service Layer (Application Services) entre la API y el dominio | Aceptada (U3) |
| ADR-03 | Patrón Repository con puertos en el dominio e implementaciones SQL en infraestructura | Aceptada (U3) |
| ADR-04 | Unit of Work: una transacción por caso de uso | Aceptada (U3) |
| ADR-05 | Eventos de dominio persistidos con patrón Outbox en la misma transacción | Aceptada (U3) |
| ADR-06 | CQRS-light: el dashboard lee de un read model sin pasar por los aggregates | Aceptada (U3) |
| ADR-07 | Pasarela de pago detrás de un puerto (Adapter); en PIA es simulada | Aceptada (U3) |
| ADR-08 | State Machine explícita y declarativa para Reserva, Sesión, Pago y Disputa | Aceptada (PIA) |
| ADR-09 | Specification (&, \|, ~) para reglas de elegibilidad y de plazo | Aceptada (PIA) |
| ADR-10 | FastAPI + OpenAPI/Swagger como contrato REST | Aceptada (PIA) |
| ADR-11 | SQLAlchemy 2.0; PostgreSQL en Compose/producción y SQLite en pruebas locales | Aceptada (PIA) |
| ADR-12 | Configuración 12-factor por variables de entorno | Aceptada (PIA) |
| ADR-13 | Control de acceso por rol con cabecera `X-Role` (autenticación real fuera de alcance) | Aceptada (PIA) |

## ADR-08 — State Machine explícita
**Contexto.** Las reglas del BRD dependen del estado (no se finaliza una sesión que no inició, no se resuelve una disputa no escalada).
**Decisión.** `StateMachine` recibe una tabla `{estado: {evento: destino}}` por aggregate; toda mutación pasa por `fire()`.
**Consecuencias.** Las transiciones inválidas responden `409 INVALID_TRANSITION`; la tabla es la documentación ejecutable de los diagramas de estado.

## ADR-09 — Specification
**Contexto.** Reglas como «tutor activo Y con disponibilidad en la materia Y en el horario» se combinan de distintas formas.
**Decisión.** Clase base `Specification` con operadores `&`, `|`, `~`; reglas concretas (`TutorActive`, `SlotWithinAvailability`, `NoOverlap`, `LateCancellation`, `WithinDisputeWindow`, `ConnectionCounts`, …).
**Consecuencias.** Las reglas se prueban aisladas y se reutilizan (Open/Closed); `can_receive_booking` las compone.

## ADR-10 — FastAPI/OpenAPI
Swagger UI en `/docs` y esquema en `/openapi.json` (copia en `docs/api/openapi.json`). Los errores de dominio se mapean en un único handler: 404, 409 (estado/plazo/traslape), 422 (regla de negocio), 401/403 (rol).

## ADR-11 — Persistencia
Tablas relacionales con columnas JSON para colecciones internas del aggregate (checklist, calificaciones, evidencia). La rehidratación no ejecuta reglas. Se verificó la suite completa contra PostgreSQL 16.

## ADR-12 — Configuración
`DATABASE_URL`, `APP_ENV`, `PORT` por entorno; `.env.example` sin secretos; `postgres://` de Render/Heroku se normaliza a `postgresql+psycopg2://`.

## ADR-13 — Roles
`X-Role` simula autenticación: solo `soporte` resuelve disputas y registra ausencia del tutor; solo `administrador` consulta el dashboard y reactiva tutores. Limitación conocida: no hay identidad real (JWT/OAuth).
