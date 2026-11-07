# language: es
@US-12 @baja
Característica: US-12 Extensión de sesión
  Como estudiante
  quiero solicitar una extensión de la sesión en curso con aceptación del tutor
  para continuar la tutoría con un cargo proporcional al tiempo extra

  Escenario: Extensión aceptada por ambas partes
    Dada una sesión en curso con tarifa de $300 por hora
    Cuando el estudiante propone 30 minutos más y el tutor acepta
    Entonces la sesión se extiende 30 minutos
    Y se cobran $150 adicionales

  Escenario: Una sola parte no basta
    Dada una extensión propuesta por el estudiante
    Cuando solo el estudiante la acepta
    Entonces la sesión no se extiende
