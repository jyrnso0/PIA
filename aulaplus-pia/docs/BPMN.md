# Proceso BPMN — AulaPlus

El diagrama fuente completo está en [BPMN_AulaPlus.pdf](./source/BPMN_AulaPlus.pdf).

## Participantes y flujo

1. **Estudiante:** selecciona materia, tema, modalidad, fecha y horario; crea una reserva, paga y, al final, califica la sesión.
2. **Plataforma / Administración:** valida la reserva y el pago, asigna un tutor compatible, notifica a ambas partes y registra la sesión. Si no encuentra disponibilidad, comunica alternativas.
3. **Tutor:** revisa la solicitud, acepta o rechaza, imparte la tutoría y registra asistencia y estado de la sesión.
4. **Datos de la plataforma:** conserva comprobante de pago, estado de sesión y evidencia.
5. **Soporte:** atiende las incidencias que se presenten, brinda soporte técnico o de proceso y cierra el ticket.

## Decisiones y resultados

- Si el tutor no está disponible, la plataforma informa al estudiante y sugiere cambiar tutor u horario.
- Si no hay incidencia, el flujo normal continúa hasta cerrar la sesión y recopilar las calificaciones.
- Si hay incidencia, se abre la atención de Soporte; la evidencia y la resolución quedan asociadas al caso.
- Los estados y plazos detallados en la implementación se validan en `src/domain` y se prueban mediante la suite automatizada.

## Trazabilidad de implementación

| Actividad BPMN | Componente |
|---|---|
| Buscar tutor / comprobar disponibilidad | `BookingService`, `TutorService`, `can_receive_booking` |
| Reservar y confirmar pago | `BookingService.reserve`, `BookingService.pay` |
| Registrar y dar seguimiento a sesión | `SessionService` y agregado `Sesion` |
| Atender incidencias / resolver disputas | `DisputeService` y agregado `Disputa` |
| Consultar métricas | `DashboardService` y `SqlDashboardReadModel` |
