# language: es
@US-03 @alta
Característica: US-03 Cancelación de sesión
  Como estudiante o tutor
  quiero cancelar mi sesión directamente desde la aplicación
  para gestionar la cancelación sin recurrir a un procedimiento informal

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
