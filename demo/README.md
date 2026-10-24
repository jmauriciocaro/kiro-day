# reporth — Demo funcional (local)

Central de reporte de deudas **B2B** entre prestadores de servicios. Demo
autocontenida que corre **100% en local**: FastAPI + SQLite + un servidor SMTP
de pruebas. Sin nube, sin despliegues.

## Qué hace

- **Organizaciones** (prestadores de servicios, p. ej. un jardín) se autentican
  con una API key.
- **Reportar una deuda**: registra un estudiante (nombre + registro civil) y su
  padre/acudiente responsable (nombre + cédula + correo), con monto y concepto.
- **Consultar una persona** (por cédula del padre o registro civil del
  estudiante) para decidir **aceptar o denegar**: devuelve solo un veredicto y el
  mínimo necesario, nunca el detalle de los reportes de otras organizaciones.
- **Quitar un reporte** (p. ej. cuando el deudor paga). Una organización solo
  puede quitar los reportes que ella misma creó.
- **Cobro automático por correo** a los adeudados, usando un SMTP local de
  pruebas (no se envían correos reales).

## Privacidad (reglas clave)

- Cada organización **solo ve los datos que ella aportó** (aislamiento por
  `org_id`, validado en el backend).
- La consulta expone lo mínimo para aceptar/denegar; no el detalle de terceros.

## Cómo levantarlo

Requisitos: Python 3.11+.

```bash
cd demo
./run.sh
```

El script crea un entorno virtual, instala dependencias, siembra datos de
ejemplo y levanta la API en http://localhost:8000. Abre esa URL en el navegador
para usar la interfaz.

### SMTP local para el cobro (opcional)

Para ver los correos de cobro, levanta un SMTP de pruebas en otra terminal:

```bash
# Opción A: mailpit (si lo tienes)  ->  UI en http://localhost:8025
mailpit

# Opción B: servidor SMTP de depuración de Python (imprime el correo en consola)
python -m aiosmtpd -n -l localhost:1025
```

El backend envía a `localhost:1025` por defecto (configurable con `SMTP_HOST` /
`SMTP_PORT`). Si no hay ningún SMTP escuchando, el cobro se registra igual y el
correo se guarda como "no entregado" sin romper la demo.

## Datos de ejemplo (seed)

Dos organizaciones con sus API keys:

| Organización        | API key              |
|---------------------|----------------------|
| Jardín Los Pitufos  | `org-pitufos-key`    |
| Academia El Saber   | `org-saber-key`      |

Envía la API key en el header `X-API-Key`.
