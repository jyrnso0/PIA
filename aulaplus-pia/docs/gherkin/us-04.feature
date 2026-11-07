# language: es
@US-04 @alta
Característica: US-04 Penalización por cancelación tardía
  Como administrador de la plataforma
  quiero calcular automáticamente la penalización según la anticipación de la cancelación
  para aplicar una regla consistente a quien cancela

  Escenario: Cancelación con menos de 4 horas
    Dada una sesión pagada de $300 que inicia en 2.5 horas
    Cuando el estudiante cancela
    Entonces se cobra una penalización de $150 (50 %)

  Escenario: Cancelación con 4 horas o más
    Dada una sesión pagada que inicia en 5 horas
    Cuando el estudiante cancela
    Entonces no hay penalización y se reembolsa el 100 %

  Escenario: Cancelación tardía del tutor
    Dada una sesión pagada de $300 que inicia en 1 hora
    Cuando el tutor cancela
    Entonces la penalización de $150 se carga al tutor
    Y el estudiante recibe el 100 %
