# language: es
@US-17 @alta
Característica: US-17 Reembolso formal
  Como agente de Soporte
  quiero gestionar los reembolsos mediante un expediente con evidencia y responsable
  para justificar cada decisión y sustituir la resolución informal por WhatsApp

  Escenario: Reembolso con responsable
    Dada una disputa escalada con evidencia
    Cuando Soporte la resuelve con un reembolso del 50 %
    Entonces queda registrado el motivo, el responsable y la fecha del reembolso

  Escenario: Reembolso sin responsable
    Dado un pago confirmado
    Cuando se intenta reembolsar sin motivo o responsable
    Entonces el sistema lo rechaza
