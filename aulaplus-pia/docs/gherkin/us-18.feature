# language: es
@US-18 @media
Característica: US-18 Suspensión automática
  Como administrador de la plataforma
  quiero suspender automáticamente a los tutores que acumulen más de dos ausencias en 30 días
  para proteger la confiabilidad del servicio

  Escenario: Tercera ausencia suspende
    Dado un tutor con 2 ausencias en 30 días
    Cuando se registra una tercera ausencia
    Entonces el tutor queda suspendido
    Y no recibe nuevas reservas

  Escenario: Reactivación por Administración
    Dado un tutor suspendido
    Cuando Administración revisa y lo reactiva
    Entonces el tutor vuelve a estar activo
