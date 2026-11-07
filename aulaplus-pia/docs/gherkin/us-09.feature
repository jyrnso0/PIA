# language: es
@US-09 @alta
Característica: US-09 Ausencia del tutor
  Como estudiante
  quiero recibir el reembolso total cuando mi tutor no se presente
  para recuperar el importe pagado por la tutoría no recibida

  Escenario: Reembolso automático
    Dada una sesión pagada de $300 a la que el tutor no se presentó
    Cuando Soporte registra la ausencia
    Entonces se genera un reembolso de $300 (100 %)
    Y se registra la falta en el perfil del tutor
