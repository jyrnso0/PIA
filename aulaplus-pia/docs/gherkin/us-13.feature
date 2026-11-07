# language: es
@US-13 @baja
Característica: US-13 Cambio de modalidad
  Como estudiante o tutor
  quiero acordar un cambio entre tutoría presencial y en línea antes de la sesión
  para adaptar la modalidad sin modificarla unilateralmente

  Escenario: Cambio con 1 hora o más de anticipación
    Dada una sesión virtual que inicia en 1.5 horas
    Cuando ambas partes confirman el cambio a presencial
    Entonces la modalidad de la sesión es presencial

  Escenario: Cambio con menos de 1 hora
    Dada una sesión que inicia en 50 minutos
    Cuando una parte propone cambiar la modalidad
    Entonces el sistema responde 422
