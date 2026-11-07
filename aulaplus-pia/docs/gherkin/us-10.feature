# language: es
@US-10 @media
Característica: US-10 Corte de conexión
  Como estudiante o tutor
  quiero conocer si una sesión interrumpida por conexión cuenta como realizada
  para tener una determinación basada en su duración registrada

  Escenario: Cuenta con 15 minutos o más
    Dada una sesión en curso
    Cuando se corta la conexión a los 15 minutos
    Entonces la sesión cuenta como realizada

  Escenario: No cuenta con menos de 15 minutos
    Dada una sesión en curso
    Cuando se corta la conexión a los 14 minutos
    Entonces la sesión queda interrumpida y no cuenta
