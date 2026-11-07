# language: es
@US-01 @crítica
Característica: US-01 Reserva y pago en 15 minutos
  Como estudiante
  quiero reservar una tutoría y confirmar mi pago dentro del plazo permitido
  para asegurar mi sesión y evitar reservas pendientes indefinidas

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
