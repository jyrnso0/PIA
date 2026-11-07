# Historias de usuario con criterios de aceptación (Gherkin)

20 historias derivadas de las 20 necesidades del BRD. Cada una tiene su archivo `.feature` en `docs/gherkin/` y se verifica con las pruebas indicadas en la [matriz de trazabilidad](traceability.md).

## US-01 — Reserva y pago en 15 minutos (Crítica)
**Como** estudiante, **quiero** reservar una tutoría y confirmar mi pago dentro del plazo permitido, **para** asegurar mi sesión y evitar reservas pendientes indefinidas.  
Regla: BR-0001 · Necesidad: N1

```gherkin
Escenario: Pago dentro del plazo confirma la reserva
  Dada una reserva pendiente creada hace 10 minutos
  Cuando el estudiante confirma el pago
  Entonces la reserva queda confirmada
  Y se programa la sesión

Escenario: Reserva sin pago se libera
  Dada una reserva pendiente creada hace 16 minutos
  Cuando se ejecuta la liberación de vencidas
  Entonces la reserva queda liberada
  Y el horario vuelve a estar disponible

Escenario: Pago tardío se rechaza
  Dada una reserva pendiente creada hace 16 minutos
  Cuando el estudiante intenta pagar
  Entonces el sistema responde 409 DEADLINE_EXPIRED
```

## US-02 — Cierre automático de la sesión (Media)
**Como** administrador de la plataforma, **quiero** cerrar automáticamente el proceso conforme al plazo y las calificaciones, **para** identificar las sesiones cuyo seguimiento ha concluido.  
Regla: BR-0002 · Necesidad: N2

```gherkin
Escenario: Cierre por doble calificación
  Dada una sesión realizada
  Cuando estudiante y tutor la califican
  Entonces la sesión queda cerrada y el pago liquidado

Escenario: Cierre a las 48 horas sin disputa
  Dada una sesión realizada hace 48 horas sin disputas abiertas
  Cuando se ejecuta el cierre de vencidas
  Entonces la sesión queda cerrada

Escenario: Una disputa abierta impide el cierre automático
  Dada una sesión realizada con una disputa abierta
  Cuando pasan 48 horas
  Entonces la sesión no se cierra
```

## US-03 — Cancelación de sesión (Alta)
**Como** estudiante o tutor, **quiero** cancelar mi sesión directamente desde la aplicación, **para** gestionar la cancelación sin recurrir a un procedimiento informal.  
Regla: BR-0003 · Necesidad: N3

```gherkin
Escenario: El estudiante cancela desde la app
  Dada una sesión programada
  Cuando el estudiante la cancela
  Entonces la sesión queda cancelada
  Y se registra quién la solicitó

Escenario: Soporte sin situación reportada no puede cancelar
  Dada una sesión programada
  Cuando Soporte intenta cancelarla sin situación reportada
  Entonces el sistema responde 422

Escenario: Soporte cancela con situación reportada
  Dada una sesión programada
  Cuando Soporte la cancela indicando la situación reportada
  Entonces la sesión queda cancelada
```

## US-04 — Penalización por cancelación tardía (Alta)
**Como** administrador de la plataforma, **quiero** calcular automáticamente la penalización según la anticipación de la cancelación, **para** aplicar una regla consistente a quien cancela.  
Regla: BR-0004 · Necesidad: N4

```gherkin
Escenario: Cancelación con menos de 4 horas
  Dada una sesión pagada de $300 que inicia en 2.5 horas
  Cuando el estudiante cancela
  Entonces se cobra una penalización de $150 (50 %)

Escenario: Cancelación con 4 horas o más
  Dada una sesión pagada que inicia en 5 horas
  Cuando el estudiante cancela
  Entonces no hay penalización y se reembolsa el 100 %

Escenario: Cancelación tardía del tutor
  Dada una sesión pagada de $300 que inicia en 1 hora
  Cuando el tutor cancela
  Entonces la penalización de $150 se carga al tutor
  Y el estudiante recibe el 100 %
```

## US-05 — Comisión 20/80 (Crítica)
**Como** administrador de la plataforma, **quiero** calcular la comisión y registrar el importe correspondiente al tutor, **para** gestionar el pago de cada sesión con un desglose verificable.  
Regla: BR-0005 · Necesidad: N5

```gherkin
Escenario: Desglose del pago
  Dada una reserva de $300
  Cuando se confirma el pago
  Entonces la plataforma retiene $60 (20 %)
  Y se registran $240 (80 %) a favor del tutor
```

## US-06 — Bloqueo de traslapes (Alta)
**Como** estudiante, **quiero** reservar únicamente horarios sin traslapes con sesiones confirmadas del tutor, **para** evitar que mi tutor tenga dos compromisos simultáneos.  
Regla: BR-0006 · Necesidad: N6

```gherkin
Escenario: Horario traslapado se bloquea
  Dado que el tutor tiene una sesión confirmada de 10:00 a 11:00
  Cuando otro estudiante intenta reservar de 10:30 a 11:30
  Entonces el sistema bloquea la reserva (409)

Escenario: Horario contiguo se permite
  Dado que el tutor tiene una sesión confirmada de 10:00 a 11:00
  Cuando otro estudiante reserva de 11:00 a 12:00
  Entonces la reserva se crea

Escenario: Una reserva sin pagar no bloquea
  Dada una reserva pendiente de pago
  Cuando otro estudiante reserva el mismo horario
  Entonces la reserva se crea
```

## US-07 — Reporte de disputa en 24 horas (Alta)
**Como** estudiante o tutor, **quiero** reportar un desacuerdo dentro del plazo posterior a la sesión, **para** solicitar la revisión formal de lo ocurrido.  
Regla: BR-0007 · Necesidad: N7

```gherkin
Escenario: Disputa dentro de 24 horas
  Dada una sesión finalizada hace 12 horas
  Cuando el estudiante reporta un desacuerdo
  Entonces se registra la disputa

Escenario: Disputa fuera de plazo
  Dada una sesión finalizada hace 24 horas y 1 minuto
  Cuando el estudiante reporta un desacuerdo
  Entonces el sistema responde 409 y la sesión se da por válida
```

## US-08 — Ausencia del estudiante (Media)
**Como** tutor, **quiero** registrar mi presencia y la ausencia del estudiante, **para** respaldar el cobro cuando el estudiante no asiste.  
Regla: BR-0008 · Necesidad: N8

```gherkin
Escenario: Cobro al estudiante ausente
  Dado que el tutor confirmó su presencia
  Y el estudiante no asistió
  Cuando se registra la ausencia del estudiante
  Entonces se cobra el 100 % de la sesión
  Y el tutor recibe su 80 %

Escenario: Sin presencia del tutor no se cobra
  Dado que el tutor no confirmó su presencia
  Cuando se registra la ausencia del estudiante
  Entonces el sistema responde 422
```

## US-09 — Ausencia del tutor (Alta)
**Como** estudiante, **quiero** recibir el reembolso total cuando mi tutor no se presente, **para** recuperar el importe pagado por la tutoría no recibida.  
Regla: BR-0009 · Necesidad: N9

```gherkin
Escenario: Reembolso automático
  Dada una sesión pagada de $300 a la que el tutor no se presentó
  Cuando Soporte registra la ausencia
  Entonces se genera un reembolso de $300 (100 %)
  Y se registra la falta en el perfil del tutor
```

## US-10 — Corte de conexión (Media)
**Como** estudiante o tutor, **quiero** conocer si una sesión interrumpida por conexión cuenta como realizada, **para** tener una determinación basada en su duración registrada.  
Regla: BR-0010 · Necesidad: N10

```gherkin
Escenario: Cuenta con 15 minutos o más
  Dada una sesión en curso
  Cuando se corta la conexión a los 15 minutos
  Entonces la sesión cuenta como realizada

Escenario: No cuenta con menos de 15 minutos
  Dada una sesión en curso
  Cuando se corta la conexión a los 14 minutos
  Entonces la sesión queda interrumpida y no cuenta
```

## US-11 — Resolución en 48 horas (Crítica)
**Como** agente de Soporte, **quiero** revisar las versiones y evidencias de una disputa escalada, **para** resolver el desacuerdo dentro del tiempo establecido.  
Regla: BR-0011 · Necesidad: N11

```gherkin
Escenario: Resolución dentro del SLA
  Dada una disputa escalada con evidencia
  Cuando Soporte registra su resolución antes de 48 horas
  Entonces la disputa queda resuelta

Escenario: Disputa fuera de SLA se señala
  Dada una disputa escalada sin resolver hace 49 horas
  Cuando Soporte consulta las disputas vencidas
  Entonces la disputa aparece marcada como vencida
```

## US-12 — Extensión de sesión (Baja)
**Como** estudiante, **quiero** solicitar una extensión de la sesión en curso con aceptación del tutor, **para** continuar la tutoría con un cargo proporcional al tiempo extra.  
Regla: BR-0012 · Necesidad: N12

```gherkin
Escenario: Extensión aceptada por ambas partes
  Dada una sesión en curso con tarifa de $300 por hora
  Cuando el estudiante propone 30 minutos más y el tutor acepta
  Entonces la sesión se extiende 30 minutos
  Y se cobran $150 adicionales

Escenario: Una sola parte no basta
  Dada una extensión propuesta por el estudiante
  Cuando solo el estudiante la acepta
  Entonces la sesión no se extiende
```

## US-13 — Cambio de modalidad (Baja)
**Como** estudiante o tutor, **quiero** acordar un cambio entre tutoría presencial y en línea antes de la sesión, **para** adaptar la modalidad sin modificarla unilateralmente.  
Regla: BR-0013 · Necesidad: N13

```gherkin
Escenario: Cambio con 1 hora o más de anticipación
  Dada una sesión virtual que inicia en 1.5 horas
  Cuando ambas partes confirman el cambio a presencial
  Entonces la modalidad de la sesión es presencial

Escenario: Cambio con menos de 1 hora
  Dada una sesión que inicia en 50 minutos
  Cuando una parte propone cambiar la modalidad
  Entonces el sistema responde 422
```

## US-14 — Checklist y timestamps (Alta)
**Como** estudiante o tutor, **quiero** registrar las confirmaciones de la sesión con marcas de tiempo del sistema, **para** contar con evidencia verificable de su realización.  
Regla: BR-0014 · Necesidad: N14

```gherkin
Escenario: Evidencia completa
  Dada una sesión en curso
  Cuando estudiante y tutor completan su checklist y se finaliza
  Entonces se guardan los timestamps de inicio y fin
  Y la sesión queda realizada

Escenario: Checklist incompleto
  Dada una sesión en curso con checklist solo del tutor
  Cuando se intenta finalizar
  Entonces el sistema responde 422
```

## US-15 — Disponibilidad por materia (Media)
**Como** tutor, **quiero** registrar y actualizar mi disponibilidad por materia, día, horario y modalidad, **para** ofrecer horarios que reflejen cuándo puedo impartir cada tutoría.  
Regla: BR-0015 · Necesidad: N15

```gherkin
Escenario: Disponibilidad independiente
  Dado que el tutor imparte Cálculo y Física
  Cuando registra la disponibilidad de Física
  Entonces la disponibilidad de Cálculo no cambia

Escenario: Fuera de disponibilidad no se reserva
  Dado que el tutor solo ofrece Cálculo
  Cuando un estudiante reserva Física
  Entonces el sistema responde 422
```

## US-16 — Promedio público y reporte de comentarios (Baja)
**Como** estudiante, **quiero** consultar el promedio público del tutor y reportar comentarios inapropiados, **para** evaluar la experiencia del servicio y señalar contenido inadecuado.  
Regla: BR-0016 · Necesidad: N16

```gherkin
Escenario: Promedio público
  Dado un tutor con calificaciones registradas
  Cuando se consulta su perfil
  Entonces se muestra su promedio sin datos internos

Escenario: Reportar un comentario
  Dado un comentario inapropiado en una sesión
  Cuando se reporta
  Entonces deja de mostrarse en el perfil público
```

## US-17 — Reembolso formal (Alta)
**Como** agente de Soporte, **quiero** gestionar los reembolsos mediante un expediente con evidencia y responsable, **para** justificar cada decisión y sustituir la resolución informal por WhatsApp.  
Regla: BR-0017 · Necesidad: N17

```gherkin
Escenario: Reembolso con responsable
  Dada una disputa escalada con evidencia
  Cuando Soporte la resuelve con un reembolso del 50 %
  Entonces queda registrado el motivo, el responsable y la fecha del reembolso

Escenario: Reembolso sin responsable
  Dado un pago confirmado
  Cuando se intenta reembolsar sin motivo o responsable
  Entonces el sistema lo rechaza
```

## US-18 — Suspensión automática (Media)
**Como** administrador de la plataforma, **quiero** suspender automáticamente a los tutores que acumulen más de dos ausencias en 30 días, **para** proteger la confiabilidad del servicio.  
Regla: BR-0018 · Necesidad: N18

```gherkin
Escenario: Tercera ausencia suspende
  Dado un tutor con 2 ausencias en 30 días
  Cuando se registra una tercera ausencia
  Entonces el tutor queda suspendido
  Y no recibe nuevas reservas

Escenario: Reactivación por Administración
  Dado un tutor suspendido
  Cuando Administración revisa y lo reactiva
  Entonces el tutor vuelve a estar activo
```

## US-19 — Dashboard semanal (Media)
**Como** administrador de la plataforma, **quiero** consultar un dashboard semanal de comisiones, cancelaciones, disputas y calificaciones, **para** supervisar el desempeño del negocio sin elaborar reportes manuales.  
Regla: BR-0019 · Necesidad: N19

```gherkin
Escenario: Indicadores de la semana
  Dado un período semanal con sesiones, cancelaciones y disputas
  Cuando Administración abre el dashboard
  Entonces ve comisión, tasa de cancelación, tasa de disputas y calificación promedio por tutor

Escenario: Solo Administración
  Dado un usuario sin rol de administrador
  Cuando consulta el dashboard
  Entonces el sistema responde 403
```

## US-20 — Bloqueo de cierre sin evidencia (Crítica)
**Como** administrador de la plataforma, **quiero** impedir que se finalicen disputas sin evidencia registrada, **para** reducir a cero las resoluciones sin sustento desde el primer día.  
Regla: BR-0020 · Necesidad: N20

```gherkin
Escenario: Cierre bloqueado
  Dada una disputa escalada sin evidencia
  Cuando Soporte intenta marcarla como resuelta
  Entonces el sistema responde 422 EVIDENCE_REQUIRED

Escenario: Cierre permitido con evidencia
  Dada una disputa escalada con evidencia adjunta
  Cuando Soporte la resuelve con decisión y responsable
  Entonces la disputa queda resuelta
```
