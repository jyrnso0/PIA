# AulaPlus — Business Requirements Document (BRD)
**Caso 08 · Equipo 8 · Componentes en Lógica de Negocios (FIME-UANL)**
Integrantes: Ángel Adrián Velez Contreras (2145646) · Alonso Morales Quintanilla (2145757) · Jairany López Ramos (2145407)
Versión PIA: refinada a partir del BRD de la Unidad 2 y de la arquitectura de la Unidad 3 (misma empresa y mismas reglas).

## 1. Contexto
AulaPlus es una plataforma que conecta estudiantes con tutores particulares y cobra una comisión por cada sesión realizada.
Las tutorías pueden ser presenciales o en línea. El estudiante selecciona materia, tema, modalidad, fecha y horario; los tutores
registran su disponibilidad y las materias que imparten. Después de la sesión ambas partes se califican y la plataforma conserva
evidencia del estado de la sesión y gestiona el pago al tutor.

El proceso arranca con la búsqueda de tutoría y termina de dos formas: de manera normal (la sesión se da, se califica y se paga
al tutor) o anticipada (la sesión se cancela antes de realizarse). El documento resuelve los problemas actuales con disputas,
cancelaciones y reembolsos y es la base de las historias de usuario y del modelo de proceso.

## 2. Problemas y oportunidades
- Problemas sobre si la sesión realmente ocurrió, por falta de evidencia formal (BR-0011, BR-0014).
- Disponibilidad de tutores desactualizada: traslapes y sesiones que no se pueden cumplir (BR-0006, BR-0015).
- Cancelaciones manuales, sin política de anticipación ni penalización (BR-0003, BR-0004).
- Reembolsos y pagos decididos por WhatsApp según criterio personal, sin registro (BR-0017).

## 3. Stakeholders
| Stakeholder | Interés principal | Influencia | Rol en el proceso |
|---|---|---|---|
| Estudiante | Reservar y recibir la tutoría sin problemas; recuperar su dinero si algo falla | Media | Solicita, paga y califica la sesión |
| Tutor | Recibir su pago completo y a tiempo; no perder ingresos por disputas injustas | Media | Ofrece disponibilidad, imparte la sesión y es calificado |
| Plataforma / Administración | Maximizar comisión, minimizar disputas y mantener la confianza | Alta | Define reglas, cobra comisión, supervisa indicadores |
| Soporte | Resolver disputas rápido y con evidencia clara | Media | Escala y resuelve incidentes (disputas, cancelaciones especiales) |

## 4. Alcance
**Dentro:** reserva con confirmación de pago y liberación automática; disponibilidad por materia, día, horario y modalidad;
bloqueo de traslapes; cancelaciones con política de anticipación y penalización; evidencia de sesión (checklist y timestamps);
disputas con escalamiento y resolución con evidencia; comisión y pago al tutor; reembolsos automáticos y manuales; suspensión
automática de tutores; dashboard gerencial.

**Fuera:** procesamiento de pagos con proveedores externos más allá de confirmar el cobro; contabilidad y facturación electrónica;
verificación de identidad/antecedentes de tutores.

## 5. Necesidades, requerimientos funcionales e historias
| ID | Necesidad | Requerimiento | Historia | Prioridad |
|---|---|---|---|---|
| N1 | Confirmar el pago para iniciar formalmente la sesión; la reserva se libera automáticamente si no se paga en 15 minutos. (BR-0001) | FR-01 | US-01 | Alta |
| N2 | Dar por cerrado el proceso 48 horas después de la sesión si nadie puso un desacuerdo, o antes si ya calificaron los dos. (BR-0002) | FR-02 | US-02 | Media |
| N3 | Permitir que estudiante o tutor cancelen desde la app; Soporte solo cancela en nombre de alguien ante una situación reportada. (BR-0003) | FR-03 | US-03 | Alta |
| N4 | Cobrar el 50 % de la sesión a quien cancele con menos de 4 horas de anticipación. (BR-0004) | FR-04 | US-04 | Alta |
| N5 | Calcular automáticamente el 20 % de comisión de la plataforma sobre cada sesión pagada. (BR-0005) | FR-05 | US-05 | Crítica |
| N6 | Bloquear la reserva de un tutor si ya tiene otra sesión confirmada en un horario traslapado. (BR-0006) | FR-06 | US-06 | Alta |
| N7 | Dar 24 horas después de la sesión para reportar una disputa; pasado ese tiempo la sesión se da por válida. (BR-0007) | FR-07 | US-07 | Alta |
| N8 | Cobrar el 100 % de la sesión al estudiante que no se presentó, siempre que el tutor haya confirmado su presencia. (BR-0008) | FR-08 | US-08 | Media |
| N9 | Reembolsar automáticamente al 100 % al estudiante cuando el tutor no se presente y registrar la falta en su perfil. (BR-0009) | FR-09 | US-09 | Alta |
| N10 | Determinar si una sesión con falla de conexión cuenta como realizada según el tiempo antes del corte (mínimo 15 minutos). (BR-0010) | FR-10 | US-10 | Media |
| N11 | Mandar a Soporte los casos donde ambas partes tienen versiones distintas, para resolverlos en máximo 48 horas con evidencia. (BR-0011) | FR-11 | US-11 | Crítica |
| N12 | Permitir extender una sesión en curso solo con aceptación de ambas partes, cobrando el tiempo extra de forma proporcional. (BR-0012) | FR-12 | US-12 | Baja |
| N13 | Permitir el cambio de modalidad solo si ambas partes lo confirman con al menos 1 hora de anticipación. (BR-0013) | FR-13 | US-13 | Baja |
| N14 | Registrar evidencia mediante checklist de ambas partes y timestamps de inicio/fin generados por el sistema. (BR-0014) | FR-14 | US-14 | Alta |
| N15 | Permitir al tutor registrar su disponibilidad por día, horario, materia y modalidad, de forma independiente por materia. (BR-0015) | FR-15 | US-15 | Media |
| N16 | Mostrar públicamente el promedio de calificación del tutor y permitir reportar comentarios inapropiados. (BR-0016) | FR-16 | US-16 | Baja |
| N17 | Sustituir la resolución informal de reembolsos (WhatsApp) por un flujo formal con evidencia y responsable asignado. (BR-0017) | FR-17 | US-17 | Alta |
| N18 | Suspender automáticamente a un tutor con más de 2 ausencias en 30 días, hasta revisión de Administración. (BR-0018) | FR-18 | US-18 | Media |
| N19 | Generar un dashboard semanal con comisión, tasa de cancelación, tasa de disputas y calificación promedio por tutor. (BR-0019) | FR-19 | US-19 | Media |
| N20 | Bajar a cero las disputas resueltas sin ninguna evidencia. (BR-0020) | FR-20 | US-20 | Crítica |

Los requerimientos FR-01…FR-20 corresponden uno a uno con las necesidades N1…N20 (texto completo en el BRD de la Unidad 2) y se
detallan como historias con criterios Gherkin en [user_stories.md](user_stories.md).

## 6. Requerimientos no funcionales
| RNF | Descripción | Implementación en el PIA |
|---|---|---|
| Trazabilidad | Guardar quién autorizó cada reembolso o excepción y cuándo | `Pago.refund_responsible`, `refunded_at`; eventos en outbox |
| Notificaciones | Avisar plazos de pago, disputa y SLA por vencer | `GET /notificaciones` (`NotificationService`) |
| Control de acceso por rol | Solo Soporte cierra disputas; solo Administración ve el dashboard | Cabecera `X-Role` verificada en la API (401/403) |
| Disponibilidad | Uso en cualquier momento | Servicio contenerizado, `GET /health`, despliegue en la nube |
| Consistencia de cálculos | Mismo resultado para el mismo caso | `Money` con `Decimal` y redondeo `ROUND_HALF_UP` |

## 7. Restricciones
- Pago en 15 minutos o se libera el horario (BR-0001).
- Cancelar sin penalización requiere ≥ 4 h de anticipación; si no, 50 % a quien cancela (BR-0004).
- Comisión fija del 20 % por sesión cobrada, sin variar por materia o modalidad (BR-0005).
- 24 horas tras el fin de la sesión para disputar; después la sesión queda válida (BR-0007).
- Con falla de conexión la sesión cuenta solo si duró ≥ 15 minutos (BR-0010).
- Soporte tiene máximo 48 horas para resolver una disputa (BR-0011).
- Cambio de modalidad con confirmación de ambas partes y ≥ 1 hora de anticipación (BR-0013).
- Más de 2 inasistencias en 30 días suspende al tutor automáticamente (BR-0018).

## 8. Supuestos
- Una sola moneda: pesos mexicanos.
- El cobro lo procesa un proveedor externo ya integrado; aquí solo se registra la confirmación (en el PIA: `FakePaymentGateway`).
- No se trató el IVA; se asume la tasa vigente sobre el costo de la sesión (no se modela).
- No hay límite de disputas por estudiante; Soporte las revisa caso por caso.
- La verificación de identidad de tutores se hace fuera del sistema.

## 9. Criterio de éxito
- Cero disputas resueltas sin evidencia (BR-0020), gracias a checklist y timestamps obligatorios.
- Disputas resueltas en menos de 48 h, siempre con evidencia, sin WhatsApp (BR-0011, BR-0017).
- Cero traslapes de horario por tutor (BR-0006).
- Dashboard semanal disponible sin armado manual (BR-0019).

## 10. Refinamientos realizados en el PIA (decisiones sobre ambigüedades)
Estas decisiones **no cambian la empresa ni las reglas**; precisan puntos que el BRD dejaba abiertos para poder implementarlos.

| # | Punto ambiguo del BRD | Decisión adoptada |
|---|---|---|
| 1 | «Mismo día» en BR-0013 y «antes de la sesión» en US-13 | Se exige confirmación de ambas partes con ≥ 1 h de anticipación a la hora de inicio, sin limitar el día. |
| 2 | Importe del reembolso en una disputa (BR-0017) | Soporte indica el porcentaje (0–100 %) al resolver; queda registrado con motivo, responsable y fecha. |
| 3 | Qué pasa con una sesión interrumpida < 15 min (BR-0010) | Pasa a estado `INTERRUMPIDA` y no cuenta; cualquier reembolso se tramita por disputa. |
| 4 | Penalización cuando cancela el tutor (BR-0004) | Se carga el 50 % al tutor; el estudiante recibe el 100 % de su pago. |
| 5 | Cobro por extensión (BR-0012) | Tarifa por hora = importe de la reserva ÷ horas; cargo = tarifa × minutos / 60; la comisión del 20 % se recalcula sobre el total. |
| 6 | Cierre a las 48 h «si nadie puso un desacuerdo» (BR-0002) | Una disputa no resuelta sobre la sesión impide el cierre automático. |
| 7 | Asignación de tutor (BPMN) | Si la reserva no indica tutor, la plataforma asigna el primer tutor activo con disponibilidad, modalidad y sin traslape. |
| 8 | Presencia del tutor (BR-0008) | El tutor la confirma explícitamente en el sistema antes de poder cobrar la ausencia del estudiante. |
| 9 | Suspensión (BR-0018) | Dura hasta que Administración reactiva al tutor (`POST /tutores/{id}/reactivar`); al reactivar se reinicia el conteo. |
| 10 | Autenticación | Se simula con la cabecera `X-Role`; la autenticación real queda fuera de alcance del PIA. |

### Diferencias con el paquete de datos de laboratorio (`08_AulaPlus.zip`)
El paquete describe un modelo genérico de «inscripciones académicas» (estados PREINSCRITA→VALIDADA→INSCRITA, regla de beneficio
para clientes preferentes ≥ $1,500). Como indica su LEEME, es un modelo de prueba ilustrativo y **no reemplaza** los requerimientos
propios, por lo que no se adoptó su flujo de estados ni su regla de beneficio (AulaPlus no tiene esos conceptos en su BRD).
Sí se aprovechó: los actores activos/inactivos como estudiantes (regla `StudentActive`), el catálogo como materias con precio, y
las transiciones inválidas (`repetir_aprobacion`, `saltar_estado`) como casos de prueba de la State Machine
(`tests/integration/test_lab_data.py`).
