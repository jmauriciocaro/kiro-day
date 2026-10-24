#!/usr/bin/env bash
# =============================================================================
# ACTO 5 — "Conocimiento experto bajo demanda" (Skills)
# =============================================================================
# Historia: el equipo (Actos 2-3) sabe construir, pero hay conocimiento de
# dominio muy puntual que no queremos cargar en TODAS las conversaciones: cómo
# modelar los datos de reporth (con aislamiento por organización), o cómo
# enviar el cobro por correo con un SMTP local. Eso lo empaquetamos como
# SKILLS: manuales que Kiro carga solo cuando hacen falta.
#
# Feature de Kiro: SKILLS — carpetas con un SKILL.md (frontmatter name +
# description) en .kiro/skills/. Kiro lee SOLO el name+description al arrancar
# (costo de contexto mínimo); carga el contenido completo cuando tu pregunta
# coincide con la description, o cuando la invocas con "/" en el chat.
# =============================================================================

source "$(dirname "$0")/lib/common.sh"

title "ACTO 5 — Conocimiento experto bajo demanda (Skills)"

story "Dónde vamos" \
  "Dos problemas concretos de reporth necesitan conocimiento especializado:" \
  "  1) ¿Cómo modelamos deudas y aislamos los datos por organización? (datos)" \
  "  2) ¿Cómo enviamos el cobro automático por correo con un SMTP local?" \
  "No queremos ese detalle en cada charla: lo empacamos como skills."

explain "¿Qué es una Skill?" \
  "Un paquete de conocimiento portátil. Kiro lee SOLO el nombre y la" \
  "descripción al arrancar (contexto barato). Cuando tu pregunta coincide" \
  "con la descripción, carga el contenido completo. También la invocas a" \
  "mano escribiendo '/' en el chat."

explain "Skill vs Steering — ¿cuál es la diferencia?" \
  "  Steering  → reglas del proyecto, SIEMPRE o por archivo (always/fileMatch)." \
  "  Skill     → conocimiento que se activa SOLO cuando la conversación lo pide." \
  "Regla práctica: si aplica siempre, es steering; si es experticia puntual," \
  "es skill. Las descripciones ESPECÍFICAS activan mejor que las genéricas."

pause

SKILLS="$KIRO_DIR/skills"
mkdirp "$SKILLS"

# --- Skill 1: modelado de datos de reporth -----------------------------------
explain "Skill 1/2 — modelado de datos con aislamiento por organización" \
  "Carpeta: .kiro/skills/datos-reporth/  con su SKILL.md." \
  "Descripción específica: 'modelar deudas, personas y el aislamiento por" \
  "organización de reporth'. Así Kiro la activa cuando toque el modelo de datos."

DATA_DIR="$SKILLS/datos-reporth"
mkdirp "$DATA_DIR"
DATA="$DATA_DIR/SKILL.md"
exists_note "$DATA"
step "Creando ${DATA}…"
cat > "$DATA" <<'MD'
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
MD
ok "Creado: $DATA"
show_file "$DATA"
pause

# --- Skill 2: cobro automático por correo (SMTP local) -----------------------
explain "Skill 2/2 — cobro automático por correo" \
  "Carpeta: .kiro/skills/cobro-correo/  con su SKILL.md." \
  "Conocimiento de cómo enviar el cobro a los adeudados usando un servidor SMTP" \
  "LOCAL emulado (MailHog/mailpit). Se activa al preguntar por 'cobro' o 'correo'."

MAIL_DIR="$SKILLS/cobro-correo"
mkdirp "$MAIL_DIR"
MAIL="$MAIL_DIR/SKILL.md"
exists_note "$MAIL"
step "Creando ${MAIL}…"
cat > "$MAIL" <<'MD'
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
MD
ok "Creado: $MAIL"
show_file "$MAIL"
pause

# --- Resultado ---------------------------------------------------------------
explain "Skills creadas en .kiro/skills/:"
find "$SKILLS" -name SKILL.md | sed "s|$WORKSHOP_ROOT/||" | sort | sed 's/^/   /'

explain "Cómo se activan" \
  "Automática: pregunta en el chat algo como" \
  "  'Diseña el modelo de datos de reporth'           → activa datos-reporth" \
  "  'Cómo envío el cobro por correo a los adeudados'  → activa cobro-correo" \
  "Manual: escribe '/' en el chat y elige la skill por su nombre." \
  "Kiro solo pagó el costo de name+description hasta que la necesitaste."

title "Acto 5 completado ✅"
explain "El equipo ya tiene reglas, especialistas y manuales expertos. Ahora" \
  "automaticemos el proceso: que ciertas acciones se disparen solas (tests," \
  "validaciones) sin pedírselo. Eso son los Hooks." \
  "" \
  "➡  Siguiente: ./scripts/06-hooks.sh (automatización por eventos)"
