# language: es
@US-02 @media
Característica: US-02 Cierre automático de la sesión
  Como administrador de la plataforma
  quiero cerrar automáticamente el proceso conforme al plazo y las calificaciones
  para identificar las sesiones cuyo seguimiento ha concluido

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
