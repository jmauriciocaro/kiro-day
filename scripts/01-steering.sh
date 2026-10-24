#!/usr/bin/env bash
# =============================================================================
# ACTO 1 — "Las reglas de la casa" (Steering)
# =============================================================================
# Historia: tenemos la oficina montada (Acto 0). Antes de contratar
# especialistas, definimos CÓMO trabaja el equipo: qué construimos, con qué
# stack, con qué convenciones y en qué idioma. Si no lo fijamos, tendríamos que
# repetírselo a cada agente en cada conversación.
#
# Feature de Kiro: STEERING — archivos markdown en .kiro/steering/ que Kiro lee
# como contexto persistente. Soportan 4 modos de inclusión:
#   always     → se carga en TODA sesión (reglas universales del proyecto)
#   fileMatch  → se carga solo al tocar archivos que matchean un patrón
#   manual     → se carga a pedido, referenciándolo con #nombre
#   auto       → Kiro decide cargarlo según su 'description'
# =============================================================================

source "$(dirname "$0")/lib/common.sh"

title "ACTO 1 — Las reglas de la casa (Steering)"

story "Dónde vamos" \
  "La oficina (.kiro/) está lista, pero vacía." \
  "Si contratamos un arquitecto y 3 devs sin reglas comunes, cada uno" \
  "asumiría un stack distinto. Primero fijamos las reglas de la casa."

explain "¿Qué es Steering?" \
  "Archivos markdown en .kiro/steering/ que Kiro lee como conocimiento" \
  "PERSISTENTE del proyecto. Sin steering, repetirías en cada sesión:" \
  "'usamos React', 'responde en español', 'protege los datos sensibles'…" \
  "Con steering, lo escribes UNA vez y todos los agentes lo respetan."

explain "Los 4 modos de inclusión (frontmatter 'inclusion')" \
  "  always     → en TODA sesión. Para reglas universales del proyecto." \
  "  fileMatch  → solo al editar archivos que matchean un patrón (p. ej. *.tsx)." \
  "  manual     → a pedido, lo invocas con #nombre en el chat." \
  "  auto       → Kiro decide cargarlo según su 'description'." \
  "Objetivo: mantener el contexto LIGERO — no cargar todo siempre."

pause

STEERING="$KIRO_DIR/steering"
mkdirp "$STEERING"

# --- 1) producto.md — la visión de reporth (inclusion: always) --------------
explain "Archivo 1/3 — producto.md (inclusion: always)" \
  "La visión del negocio. Va 'always' porque TODO agente, haga lo que haga," \
  "debe entender qué estamos construyendo y para quién."

PRODUCTO="$STEERING/producto.md"
exists_note "$PRODUCTO"
step "Creando ${PRODUCTO}…"
cat > "$PRODUCTO" <<'MD'
---
inclusion: always
---

# Producto: reporth — central de reporte de deudas B2B

## El problema
En Colombia hay muchas empresas que prestan servicios por suscripción (jardines
infantiles privados, academias, gimnasios, servicios locales). No son lo
suficientemente grandes para pagar una suscripción a una central de riesgo, y
pierden mucho dinero: cuando un cliente no paga, simplemente cambia de
proveedor. Como los proveedores no se comunican entre sí, el siguiente les
presta el servicio sin saber que hay una deuda previa.

## Qué estamos construyendo
Una central de reporte de deudas **B2B** entre prestadores de servicios. Permite
reportar incumplimientos de pago y consultarlos antes de aceptar a un cliente
nuevo, llenando el vacío que dejan las centrales de riesgo tradicionales.

## Usuarios
- **Prestador de servicios (organización)**: el consumidor del sistema. Ejemplo:
  un jardín infantil privado. Reporta deudas, gestiona sus reportes y consulta
  antes de aceptar a un cliente.
- **Deudor reportado**: la persona (padre/acudiente) asociada a la deuda. No usa
  el sistema; recibe el cobro automático y puede ser dado de baja cuando paga.

## Funcionalidades núcleo (MVP)
1. **Reportar no pago / deuda** desde una organización: se registra el estudiante
   y se relaciona con el padre/acudiente responsable.
   - Estudiante: nombre + registro civil.
   - Padre/acudiente: nombre + cédula.
   - Más datos sensibles asociados a la deuda (monto, concepto, fechas).
2. **Consultar** a una persona antes de aceptarla, para decidir aceptar o denegar
   el servicio.
3. **Quitar reportes** (dar de baja una deuda, p. ej. cuando el deudor paga).
4. **Cobro automático por correo** a las personas adeudadas.

## Reglas de privacidad de datos (CRÍTICAS)
- Cada organización **solo puede ver los datos que ella misma aportó**.
- Al consultar a una persona, el que consulta solo ve lo necesario para **aceptar
  o denegar** — no el detalle completo de los reportes de otras organizaciones.
- Los datos son sensibles (cédula, registro civil de menores, deudas): se tratan
  con el máximo cuidado. Nada de exponerlos fuera de su organización dueña.

## Principios
- Demo **funcional y sencilla**: primero el MVP, sin sobre-ingeniería.
- No hay criterios de evaluación rígidos; el objetivo es que funcione y se
  entienda. El PRD aún NO está listo para esta sesión.
- Español como idioma del producto y de la comunicación del equipo.
MD
ok "Creado: $PRODUCTO"
show_file "$PRODUCTO"
pause

# --- 2) tech.md — el stack (inclusion: always) -------------------------------
explain "Archivo 2/3 — tech.md (inclusion: always)" \
  "El stack tecnológico. También 'always': fija de entrada las decisiones" \
  "para que ningún agente proponga algo fuera del stack acordado." \
  "Regla de oro: TODO debe poder emularse/correr LOCALMENTE — sin despliegues."

TECH="$STEERING/tech.md"
exists_note "$TECH"
step "Creando ${TECH}…"
cat > "$TECH" <<'MD'
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
MD
ok "Creado: $TECH"
show_file "$TECH"
pause

# --- 3) frontend.md — reglas específicas (inclusion: fileMatch) --------------
explain "Archivo 3/3 — frontend.md (inclusion: fileMatch)" \
  "Reglas que SOLO importan al tocar código de frontend. Usamos 'fileMatch'" \
  "con patrones: este steering se carga únicamente cuando se editan .tsx/.jsx." \
  "Así no gastamos contexto con reglas de UI cuando trabajamos en el backend."

FRONTEND="$STEERING/frontend.md"
exists_note "$FRONTEND"
step "Creando ${FRONTEND}…"
cat > "$FRONTEND" <<'MD'
---
inclusion: fileMatch
fileMatchPattern: "**/*.{tsx,jsx,css}"
---

# Reglas de Frontend (reporth)

- Componentes funcionales con hooks; nada de componentes de clase.
- La UI debe ser clara para personal administrativo de una organización
  (p. ej. secretaría de un jardín): textos en español, flujos simples,
  confirmaciones antes de acciones irreversibles (quitar un reporte).
- Privacidad en la UI: nunca mostrar datos de otras organizaciones. En la
  consulta, mostrar solo el veredicto y el mínimo necesario para aceptar/denegar.
- Manejo cuidadoso de datos sensibles (cédula, registro civil): no cachearlos en
  el navegador más de lo necesario, no exponerlos en la URL.
- Accesibilidad: roles ARIA y foco de teclado en los formularios de reporte y
  consulta.
- Estado centralizado (un solo lugar de verdad) para la sesión de la organización.
MD
ok "Creado: $FRONTEND"
show_file "$FRONTEND"
pause

# --- Resultado ---------------------------------------------------------------
explain "Esto es lo que acabamos de crear en .kiro/steering/:"
find "$STEERING" -type f | sed "s|$WORKSHOP_ROOT/||" | sort | sed 's/^/   /'

explain "Cómo probarlo en el chat" \
  "Abre:  kiro-cli --v3 chat" \
  "Pregunta algo como:  'Según nuestro proyecto, ¿qué construimos, con qué" \
  "stack y en qué idioma respondes?'  → debería responder en español, describir" \
  "reporth (central de deudas B2B) y citar React/FastAPI + stack LOCAL SIN que" \
  "se lo digas: lo leyó del steering 'always'." \
  "" \
  "El steering 'manual' se invoca escribiendo #nombre en el chat." \
  "El 'fileMatch' se activa solo cuando edites un .tsx/.jsx."

title "Acto 1 completado ✅"
explain "Ya tenemos las reglas de la casa. El equipo sabe qué construir, con" \
  "qué stack local y qué reglas de privacidad respetar. Ahora sí: contratemos" \
  "al primer especialista." \
  "" \
  "➡  Siguiente: ./scripts/02-agents.sh (contratamos al arquitecto)"
