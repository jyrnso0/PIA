# language: es
@US-15 @media
Característica: US-15 Disponibilidad por materia
  Como tutor
  quiero registrar y actualizar mi disponibilidad por materia, día, horario y modalidad
  para ofrecer horarios que reflejen cuándo puedo impartir cada tutoría

  Escenario: Disponibilidad independiente
    Dado que el tutor imparte Cálculo y Física
    Cuando registra la disponibilidad de Física
    Entonces la disponibilidad de Cálculo no cambia

  Escenario: Fuera de disponibilidad no se reserva
    Dado que el tutor solo ofrece Cálculo
    Cuando un estudiante reserva Física
    Entonces el sistema responde 422
