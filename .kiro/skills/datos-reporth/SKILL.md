---
name: datos-reporth
description: Modela los datos de reporth (organizaciones, deudas, estudiante y padre/acudiente) en almacenamiento local, con aislamiento estricto por organización. Úsala al diseñar el esquema de datos, las relaciones o las consultas de la central de deudas.
---

# Modelado de datos de reporth (local, con aislamiento por organización)

## Patrones de acceso (primero esto, SIEMPRE)
1. Una organización reporta una deuda (crea estudiante + padre/acudiente + deuda).
2. Una organización lista SOLO las deudas que ella misma reportó.
3. Consultar a una persona (por cédula del padre, o registro civil del
   estudiante) para decidir aceptar/denegar — devolviendo el mínimo necesario.
4. Dar de baja (quitar) un reporte de deuda.
5. Listar deudas pendientes para el cobro automático por correo.

## Entidades
| Entidad        | Identidad                       | Datos sensibles                  |
|----------------|---------------------------------|----------------------------------|
| Organización   | id, nombre                      | —                                |
| Estudiante     | nombre + registro civil         | registro civil (menor)           |
| Padre/acudiente| nombre + cédula                 | cédula, correo                   |
| Deuda          | id, org_id, monto, concepto, fechas, estado | monto, concepto      |

Relaciones: Deuda → Estudiante → Padre/acudiente. Toda Deuda pertenece a una
Organización (`org_id`).

## Aislamiento por organización (REGLA CRÍTICA)
- TODA consulta de lectura filtra por `org_id` del solicitante. Se valida en el
  backend, nunca solo en la UI.
- En la CONSULTA de una persona, el que consulta NO ve los reportes detallados
  de otras organizaciones: solo lo necesario para aceptar/denegar (p. ej. un
  veredicto "tiene deudas reportadas: sí/no" y, si acaso, conteo/severidad).
- Datos personales (cédula, registro civil) cifrados o protegidos en reposo;
  nunca en logs.

## Opciones de almacenamiento local (emulable, sin nube)
- SQLite: simple, relacional, perfecto para la demo. Filtrar por `org_id` en
  cada query y aplicar índices por cédula / registro civil para la consulta.
- DynamoDB Local / LocalStack si se prefiere NoSQL: `PK = ORG#<orgId>` para
  garantizar el aislamiento natural por partición.

## Antipatrones a evitar
- Exponer el `org_id` de otra organización o mezclar sus datos en una respuesta.
- Devolver el detalle completo de la deuda en la consulta de aceptar/denegar.
- Guardar datos sensibles en claro en logs o en la URL.
