---
inclusion: always
---

# Stack tecnológico

Regla de oro: **todo debe poder correr/emularse localmente**. No hay despliegues
a plataformas en la nube durante el taller.

- **Frontend**: React + Vite + TypeScript.
- **Backend**: Python 3.12 + FastAPI.
- **Datos**: almacenamiento local emulable (p. ej. SQLite, o DynamoDB Local /
  LocalStack si se necesita un modelo tipo NoSQL). Nada que requiera una cuenta
  cloud real.
- **Correo (cobro automático)**: servidor SMTP local emulado (p. ej. MailHog /
  mailpit) para probar los cobros sin enviar correos reales.
- **Ejecución**: todo levantable en el equipo con un `docker compose` o scripts
  locales; sin dependencias de plataformas externas.

## Convenciones
- Código y comentarios en inglés; comunicación con el usuario en español.
- Nombres descriptivos; funciones pequeñas y con una sola responsabilidad.
- Tests para la lógica de negocio (reportes, consultas, baja de reportes, cobro).
- Nada de secretos en el código ni en el repo.

## Seguridad y privacidad (dato sensible)
- Aislamiento por organización: una organización solo accede a los datos que
  ella aportó. Esto se valida en el backend, no solo en la UI.
- Al consultar, exponer el mínimo necesario para decidir aceptar/denegar.
- Datos personales (cédula, registro civil de menores) cifrados o protegidos en
  reposo; nunca en logs ni en respuestas que no correspondan.
