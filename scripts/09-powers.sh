#!/usr/bin/env bash
# =============================================================================
# ACTO 9 — "Empaquetar y compartir el equipo" (Powers)
# =============================================================================
# Historia: montamos a mano reglas (steering), especialistas (agents), manuales
# (skills), automatización (hooks) y una herramienta externa (MCP de draw.io).
# ¿Y si quisiéramos reusar todo eso en OTRO proyecto, o compartirlo con otra
# persona que arranca su propia central de reportes? ¿O instalar el "equipo de
# un experto" sin armarlo pieza por pieza? Para eso están los POWERS: bundles
# instalables.
#
# Feature de Kiro: POWERS — paquetes que agrupan documentación/steering + MCP
# servers + workflows en una unidad que Kiro activa POR KEYWORDS (como una skill
# pero empaquetando también MCP). Un power es un directorio con:
#   POWER.md   (requerido) → frontmatter + instrucciones de steering/workflows
#   mcp.json   (opcional)  → servers MCP que trae el power
# Se instalan con:  /powers install <nombre|ruta>   (y /powers uninstall).
# =============================================================================

source "$(dirname "$0")/lib/common.sh"

title "ACTO 9 — Empaquetar y compartir el equipo (Powers)"

story "Dónde vamos" \
  "Nuestro equipo reporth vive suelto en .kiro/ (steering, agents, skills…)." \
  "Dos necesidades reales:" \
  "  1) Reusar todo esto en otro proyecto o compartirlo con un colega." \
  "  2) Instalar 'equipos' ya armados por expertos (Stripe, Figma, AWS…)." \
  "Los Powers resuelven ambas: empaquetan capacidades instalables."

explain "¿Qué es un Power?" \
  "Un bundle que agrupa en UNA unidad: documentación/steering, workflows y" \
  "—si hace falta— servers MCP. Kiro lo activa POR KEYWORDS, como una skill," \
  "pero un power puede traer TAMBIÉN sus herramientas MCP y buenas prácticas." \
  "Sirve para empaquetar TU conocimiento y para instalar el de terceros."

explain "Power vs Skill vs MCP — ¿en qué se diferencian?" \
  "  Skill → conocimiento (texto) que se carga on-demand." \
  "  MCP   → herramientas externas (tools) que Kiro puede invocar." \
  "  Power → EMPAQUETA ambos + workflows + onboarding en algo instalable y" \
  "          compartible. Es la unidad de distribución de capacidades." \
  "Pensalo así: un power es 'una skill con pilas incluidas' que puedes repartir."

explain "¿Por qué importa? (el problema que resuelven)" \
  "Conectar 5 MCP sueltos puede cargar 100+ definiciones de tools y comerse" \
  "~40% del contexto ANTES de tu primer prompt. Los powers cargan solo lo" \
  "relevante según la conversación: mantienen el agente enfocado."

pause

POWERS="$KIRO_DIR/powers"
mkdirp "$POWERS"

# --- Creamos un power propio: 'reporth-kit' ----------------------------------
explain "Creamos nuestro propio power: 'reporth-kit'" \
  "Empaqueta el conocimiento de reporth + el MCP de diagramas, para instalarlo" \
  "en cualquier proyecto nuevo. Estructura: una carpeta con POWER.md y mcp.json."

REPORTH_KIT="$POWERS/reporth-kit"
mkdirp "$REPORTH_KIT"

# POWER.md — metadata + steering/workflows del power
POWER_MD="$REPORTH_KIT/POWER.md"
exists_note "$POWER_MD"
step "Creando ${POWER_MD}…"
cat > "$POWER_MD" <<'MD'
---
name: "reporth-kit"
displayName: "reporth Starter Kit"
description: "Equipo y buenas prácticas para construir reporth, una central de reporte de deudas B2B entre prestadores de servicios: producto, stack local, privacidad de datos y diagramas."
keywords: ["reporth", "deudas", "morosos", "reporte", "central de riesgo", "b2b", "suscripcion", "cobro"]
---

# Onboarding

## Paso 1: Define tu caso
Al activarse este power, Kiro te ayudará a concretar: qué servicio prestas (p. ej.
jardín infantil privado), qué deudas reportas, qué datos sensibles manejas y qué
reglas de privacidad entre organizaciones necesitas.

# Steering Instructions

Eres un acompañante experto para construir reporth, una central de reporte de
deudas B2B entre prestadores de servicios en Colombia. Explicas en español, con
lenguaje simple, y priorizas la PRIVACIDAD de los datos sensibles (cédula,
registro civil de menores, deudas). Respetas el stack: React + FastAPI con
TODO emulable LOCALMENTE (sin despliegues en la nube).

## Reglas de privacidad (no negociables)
- Cada organización solo accede a los datos que ella misma aportó.
- Al consultar a una persona, exponer el mínimo necesario para aceptar/denegar.
- Validar el aislamiento por organización en el backend, no solo en la UI.

## Workflow: De la idea al MVP
1. **Entender**: aclara el prestador de servicios y a quién reporta.
2. **Diseñar**: propone arquitectura local y, si ayuda, dibuja un diagrama.
3. **Modelar datos**: estudiante (nombre + registro civil) ↔ padre/acudiente
   (nombre + cédula) ↔ deuda, con aislamiento por organización.
4. **Implementar**: guía el MVP (reportar deuda, consultar, quitar reporte,
   cobro automático por correo vía SMTP emulado local).

## Best Practices
- Primero el MVP funcional y sencillo; los extras después.
- Confirmaciones antes de acciones irreversibles (quitar un reporte).
- Nada de secretos en el código ni en el repo; datos sensibles protegidos.
MD
ok "Creado: $POWER_MD"
show_file "$POWER_MD"
pause

# mcp.json — el power trae el MCP de diagramas
POWER_MCP="$REPORTH_KIT/mcp.json"
exists_note "$POWER_MCP"
step "Creando ${POWER_MCP}…"
cat > "$POWER_MCP" <<'JSON'
{
  "mcpServers": {
    "drawio": {
      "url": "https://mcp.draw.io/mcp",
      "disabled": false,
      "autoApprove": ["create_diagram", "get_drawio_reference"],
      "headers": {
        "X-AI-Source": "kiro-reporth-kit"
      }
    }
  }
}
JSON
ok "Creado: $POWER_MCP"
show_file "$POWER_MCP"

step "Validando el JSON del power…"
python3 -c "import json; json.load(open('$POWER_MCP')); print('JSON OK')" \
  && ok "mcp.json del power es válido." \
  || warn "mcp.json del power tiene un error."

pause

# --- Resultado ---------------------------------------------------------------
explain "Estructura del power que acabamos de crear:"
find "$REPORTH_KIT" -type f | sed "s|$WORKSHOP_ROOT/||" | sort | sed 's/^/   /'

explain "Instalar / usar powers (CLI v3)" \
  "  /powers list                 → ver powers instalados" \
  "  /powers install <nombre>     → instalar del catálogo oficial" \
  "  /powers install ./ruta       → instalar uno LOCAL (como nuestro reporth-kit)" \
  "  /powers uninstall <nombre>   → quitarlo" \
  "Kiro namespacea los MCP del power para evitar conflictos y los gestiona." \
  "Nuestro reporth-kit se instalaría con:  /powers install .kiro/powers/reporth-kit"

explain "Powers de terceros (catálogo oficial)" \
  "Hay powers listos de Stripe, Figma, Netlify, Supabase, Datadog, AWS Aurora," \
  "Strands SDK, Postman… Instalas uno y tu agente gana ese dominio al instante," \
  "sin configurar MCP ni steering a mano."

title "Acto 9 completado ✅"
explain "¡Y con esto cierra el recorrido scripteado del taller!" \
  "Ya tienes el equipo completo: reglas (steering), especialistas (agents)," \
  "un orquestador (sub-agents), conocimiento (skills), automatización (hooks)," \
  "herramientas externas (MCP), seguridad (permisos) y empaquetado (powers)." \
  "" \
  "➡  Último paso — EN VIVO (sin script): los Specs." \
  "   Pon a trabajar todo lo anterior para convertir la idea de reporth en un" \
  "   plan ejecutable: requisitos → diseño → tareas. Lo hacemos juntos en el" \
  "   taller. Arranca con:  kiro-cli --v3 chat --agent tech-lead" \
  "   y pídele un spec del MVP de reporth."
