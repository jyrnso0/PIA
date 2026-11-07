# language: es
@US-06 @alta
Característica: US-06 Bloqueo de traslapes
  Como estudiante
  quiero reservar únicamente horarios sin traslapes con sesiones confirmadas del tutor
  para evitar que mi tutor tenga dos compromisos simultáneos

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
