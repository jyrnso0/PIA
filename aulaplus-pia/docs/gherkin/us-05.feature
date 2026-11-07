# language: es
@US-05 @crítica
Característica: US-05 Comisión 20/80
  Como administrador de la plataforma
  quiero calcular la comisión y registrar el importe correspondiente al tutor
  para gestionar el pago de cada sesión con un desglose verificable

  Escenario: Desglose del pago
    Dada una reserva de $300
    Cuando se confirma el pago
    Entonces la plataforma retiene $60 (20 %)
    Y se registran $240 (80 %) a favor del tutor
