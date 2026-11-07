# language: es
@US-14 @alta
Característica: US-14 Checklist y timestamps
  Como estudiante o tutor
  quiero registrar las confirmaciones de la sesión con marcas de tiempo del sistema
  para contar con evidencia verificable de su realización

  Escenario: Evidencia completa
    Dada una sesión en curso
    Cuando estudiante y tutor completan su checklist y se finaliza
    Entonces se guardan los timestamps de inicio y fin
    Y la sesión queda realizada

  Escenario: Checklist incompleto
    Dada una sesión en curso con checklist solo del tutor
    Cuando se intenta finalizar
    Entonces el sistema responde 422
