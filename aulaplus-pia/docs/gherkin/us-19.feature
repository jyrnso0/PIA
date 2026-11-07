# language: es
@US-19 @media
Característica: US-19 Dashboard semanal
  Como administrador de la plataforma
  quiero consultar un dashboard semanal de comisiones, cancelaciones, disputas y calificaciones
  para supervisar el desempeño del negocio sin elaborar reportes manuales

  Escenario: Indicadores de la semana
    Dado un período semanal con sesiones, cancelaciones y disputas
    Cuando Administración abre el dashboard
    Entonces ve comisión, tasa de cancelación, tasa de disputas y calificación promedio por tutor

  Escenario: Solo Administración
    Dado un usuario sin rol de administrador
    Cuando consulta el dashboard
    Entonces el sistema responde 403
