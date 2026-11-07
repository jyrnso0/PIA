# language: es
@US-20 @crítica
Característica: US-20 Bloqueo de cierre sin evidencia
  Como administrador de la plataforma
  quiero impedir que se finalicen disputas sin evidencia registrada
  para reducir a cero las resoluciones sin sustento desde el primer día

  Escenario: Cierre bloqueado
    Dada una disputa escalada sin evidencia
    Cuando Soporte intenta marcarla como resuelta
    Entonces el sistema responde 422 EVIDENCE_REQUIRED

  Escenario: Cierre permitido con evidencia
    Dada una disputa escalada con evidencia adjunta
    Cuando Soporte la resuelve con decisión y responsable
    Entonces la disputa queda resuelta
