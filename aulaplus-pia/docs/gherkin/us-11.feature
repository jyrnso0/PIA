# language: es
@US-11 @crítica
Característica: US-11 Resolución en 48 horas
  Como agente de Soporte
  quiero revisar las versiones y evidencias de una disputa escalada
  para resolver el desacuerdo dentro del tiempo establecido

  Escenario: Resolución dentro del SLA
    Dada una disputa escalada con evidencia
    Cuando Soporte registra su resolución antes de 48 horas
    Entonces la disputa queda resuelta

  Escenario: Disputa fuera de SLA se señala
    Dada una disputa escalada sin resolver hace 49 horas
    Cuando Soporte consulta las disputas vencidas
    Entonces la disputa aparece marcada como vencida
