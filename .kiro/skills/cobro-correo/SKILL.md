---
name: cobro-correo
description: Implementa el cobro automático por correo de reporth a las personas adeudadas, usando un servidor SMTP LOCAL emulado (MailHog/mailpit), sin enviar correos reales. Úsala al construir el envío de cobros, recordatorios o notificaciones por email.
---

# Cobro automático por correo (SMTP local emulado)

## Objetivo
Enviar un recordatorio/cobro por correo a cada padre/acudiente con deuda
pendiente. En el taller NO se envían correos reales: usamos un SMTP local.

## SMTP local para la demo
- MailHog o mailpit: capturan todo el correo saliente y lo muestran en una UI
  web (típico `http://localhost:8025`). SMTP escuchando en `localhost:1025`.
- Levantarlo con Docker, p. ej. `docker run ... mailhog/mailhog` o `axllent/mailpit`.
- El backend envía por SMTP a `localhost:1025`; nada sale a internet.

## Envío desde FastAPI (Python)
- Usar `smtplib` + `email.message.EmailMessage` apuntando al host/puerto local.
- Configurar host/puerto por variables de entorno (no hardcodear), p. ej.
  `SMTP_HOST`, `SMTP_PORT`.
- Enviar en segundo plano (BackgroundTasks) para no bloquear la respuesta HTTP.

## Contenido y privacidad
- El correo va SOLO al adeudado de esa deuda; nunca a terceros.
- Incluir lo mínimo: concepto, monto y organización acreedora. Evitar incluir
  datos sensibles de más (p. ej. el registro civil del menor en el cuerpo).
- Plantilla clara y en español; asunto con el nombre de la organización.

## Disparo automático
- Un endpoint o tarea que recorre las deudas en estado "pendiente" y envía el
  cobro. Para la demo puede dispararse manualmente o con un scheduler local.

## Antipatrones a evitar
- Enviar a un SMTP real durante el taller (usa siempre el local).
- Poner credenciales SMTP en el código o el repo (van en variables de entorno).
