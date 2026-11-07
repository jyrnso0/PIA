# language: es
@US-07 @alta
Característica: US-07 Reporte de disputa en 24 horas
  Como estudiante o tutor
  quiero reportar un desacuerdo dentro del plazo posterior a la sesión
  para solicitar la revisión formal de lo ocurrido

  Escenario: Disputa dentro de 24 horas
    Dada una sesión finalizada hace 12 horas
    Cuando el estudiante reporta un desacuerdo
    Entonces se registra la disputa

  Escenario: Disputa fuera de plazo
    Dada una sesión finalizada hace 24 horas y 1 minuto
    Cuando el estudiante reporta un desacuerdo
    Entonces el sistema responde 409 y la sesión se da por válida
