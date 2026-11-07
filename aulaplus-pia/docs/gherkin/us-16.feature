# language: es
@US-16 @baja
Característica: US-16 Promedio público y reporte de comentarios
  Como estudiante
  quiero consultar el promedio público del tutor y reportar comentarios inapropiados
  para evaluar la experiencia del servicio y señalar contenido inadecuado

  Escenario: Promedio público
    Dado un tutor con calificaciones registradas
    Cuando se consulta su perfil
    Entonces se muestra su promedio sin datos internos

  Escenario: Reportar un comentario
    Dado un comentario inapropiado en una sesión
    Cuando se reporta
    Entonces deja de mostrarse en el perfil público
