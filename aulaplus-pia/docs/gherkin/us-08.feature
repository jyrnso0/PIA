# language: es
@US-08 @media
Característica: US-08 Ausencia del estudiante
  Como tutor
  quiero registrar mi presencia y la ausencia del estudiante
  para respaldar el cobro cuando el estudiante no asiste

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
