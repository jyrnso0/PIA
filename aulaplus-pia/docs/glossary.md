# Glosario de dominio (lenguaje ubicuo)

| Término | Definición | Representación en el código |
|---|---|---|
| **Tutoría** | Servicio de enseñanza que un tutor imparte a un estudiante, presencial o en línea. | `Sesion / Reserva` |
| **Modalidad** | Forma de realizar la tutoría: presencial o en línea. | `Modality (enum)` |
| **Reserva** | Solicitud del estudiante para apartar un horario con un tutor; vive 15 min esperando pago. | `Reserva (aggregate)` |
| **Disponibilidad** | Días, horarios, materias y modalidad que un tutor registra para dar clases. | `Tutor.availability / SubjectAvailability` |
| **Asignación de tutor** | Proceso con el que la plataforma determina qué tutor atiende una reserva. | `BookingService._assign` |
| **Sesión** | Encuentro de tutoría ya confirmado y con horario definido. | `Sesion (aggregate)` |
| **Checklist de confirmación** | Registro donde estudiante y tutor marcan que la sesión se llevó a cabo. | `Sesion.checklist` |
| **Evidencia de sesión** | Checklist y marcas de tiempo que respaldan que la sesión ocurrió. | `Sesion.checklist, started_at, finished_at` |
| **Ausencia** | El estudiante o el tutor no se presenta a una sesión programada. | `SesionState.AUSENCIA_*` |
| **Cancelación** | Dejar sin efecto una sesión programada, por estudiante o tutor. | `Cancellation (Value Object)` |
| **Penalización** | Cargo (50 %) a quien cancela con menos de 4 horas. | `Penalty (Value Object)` |
| **Disputa** | Desacuerdo sobre si la sesión se realizó o en qué condiciones; se turna a Soporte. | `Disputa (aggregate)` |
| **Soporte** | Área que atiende incidencias y resuelve disputas. | `Role.SUPPORT` |
| **Incidencia** | Situación que interrumpe o afecta el desarrollo normal de una sesión. | `reported_situation / corte de conexión` |
| **Reembolso** | Devolución del dinero pagado cuando lo determinan las reglas. | `Pago.refund, RefundCalculator` |
| **Pago** | Transacción del estudiante para cubrir el costo de una sesión. | `Pago (aggregate)` |
| **Comisión** | Porcentaje (20 %) que retiene AulaPlus sobre cada sesión pagada. | `PaymentBreakdown` |
| **Suspensión** | Bloqueo temporal de la cuenta del tutor por demasiadas ausencias. | `AccountState.SUSPENDIDO` |
| **Calificación** | Evaluación mutua de estudiante y tutor tras la sesión. | `Rating (Value Object)` |
| **Dashboard** | Panel semanal de comisión, cancelaciones, disputas y calificaciones. | `SqlDashboardReadModel` |
| **Materia** | Área de conocimiento sobre la que el estudiante pide ayuda. | `Reserva.subject` |
| **Tema** | Contenido puntual dentro de una materia. | `Reserva.topic` |
| **Fecha / Horario** | Día y rango de tiempo asignado a la sesión. | `Schedule (Value Object)` |
| **Estudiante** | Persona que solicita y recibe una tutoría. | `Estudiante` |
| **Tutor** | Persona que ofrece e imparte tutorías particulares. | `Tutor (aggregate)` |
| **AulaPlus** | Plataforma que conecta estudiantes con tutores y cobra comisión por sesión. | `—` |
| **Extensión** | Tiempo adicional acordado por ambas partes durante la sesión, cobrado proporcionalmente. | `Sesion.propose_extension` |
