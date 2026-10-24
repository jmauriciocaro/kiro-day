#!/usr/bin/env bash
# =============================================================================
# ACTO 10 — "El encargado del control de versiones" (git-flow agent)
# =============================================================================
# Historia: el equipo ya construye reporth. En un hackathon queremos que el
# trabajo quede VERSIONADO en una rama propia (no en main) y que se vaya
# guardando con commits cada vez que hay un avance significativo. En vez de
# acordarnos de hacerlo a mano, "contratamos" un especialista de control de
# versiones: git-flow.
#
# Feature de Kiro: Custom Agents + PERMISOS acotados. git-flow solo usa git
# (crea la rama hackaton-kiro, commitea avances) y tiene PROHIBIDO lo
# destructivo (push --force, reset --hard, branch -D, rm -rf, sudo).
# =============================================================================

source "$(dirname "$0")/lib/common.sh"

title "ACTO 10 — El encargado del control de versiones (git-flow)"

story "Dónde vamos" \
  "Estamos en un hackathon: el equipo avanza rápido y no queremos perder nada." \
  "Creamos un especialista, git-flow, que:" \
  "  1) Trabaja SIEMPRE sobre una rama propia: hackaton-kiro (nunca en main)." \
  "  2) Hace un commit cada vez que hay un avance significativo." \
  "  3) Usa solo git, con lo destructivo bloqueado por sus permisos."

explain "Qué hace especial a este agente" \
  "  • Convención de rama: si no existe hackaton-kiro, la crea; si existe, se" \
  "    cambia a ella. Jamás commitea en main." \
  "  • Commits frecuentes: tras cada hito (un acto, una feature, un fix) crea" \
  "    un commit con un mensaje claro en español." \
  "  • Permisos: allow de 'git *' cotidiano; DENY de comandos peligrosos," \
  "    aunque alguien se los pida. deny gana sobre allow."

pause

AGENTS="$KIRO_DIR/agents"
mkdirp "$AGENTS"

# --- git-flow.json -----------------------------------------------------------
explain "Creamos el agente git-flow" \
  "  tools         → fs_read/grep/glob para entender el cambio + execute_bash" \
  "                  para correr git." \
  "  toolsSettings → el shell solo auto-permite comandos de git." \
  "  permissions   → deny de push --force / reset --hard / branch -D / clean" \
  "                  -fd / rm -rf / sudo; allow del resto de git."

GF="$AGENTS/git-flow.json"
exists_note "$GF"
step "Creando ${GF}…"
cat > "$GF" <<'JSON'
{
  "name": "git-flow",
  "description": "Encargado del control de versiones de reporth. Trabaja siempre en la rama hackaton-kiro y commitea cada avance significativo. Solo usa git; nada destructivo.",
  "prompt": "Eres el encargado del control de versiones del proyecto reporth durante un hackathon. Tu primera acción SIEMPRE es asegurar la rama de trabajo: si no existe la rama 'hackaton-kiro', créala con 'git checkout -b hackaton-kiro'; si ya existe, cámbiate a ella con 'git checkout hackaton-kiro'. NUNCA commitees en main. A partir de ahí, cada vez que haya un avance significativo (un acto del taller completado, una feature, un fix), creas un commit: revisas 'git status' y 'git diff', agregas los archivos relevantes por nombre (evita 'git add -A' si hay cosas no relacionadas), y escribes un mensaje de commit claro y conciso en español que explique el avance. Explicas en español cada paso antes de ejecutarlo. Nunca ejecutas comandos destructivos (git push --force, git reset --hard, git branch -D, git clean -fd, rm -rf, sudo) ni modificas la configuración de git; si algo lo requiere, lo reportas en vez de forzarlo. No tocas archivos de secretos (.env, *.pem, *.key).",
  "tools": ["fs_read", "grep", "glob", "execute_bash"],
  "allowedTools": ["fs_read", "grep", "glob"],
  "toolsSettings": {
    "shell": {
      "allowedCommands": [
        "git .*"
      ],
      "autoAllowReadonly": true
    }
  },
  "permissions": {
    "rules": [
      {
        "capability": "fs_read",
        "match": ["**/.env", "**/.env.*", "**/*.pem", "**/*.key", "secrets/**"],
        "effect": "deny"
      },
      {
        "capability": "shell",
        "match": [
          "git push --force*",
          "git push -f*",
          "git reset --hard*",
          "git branch -D*",
          "git clean -fd*",
          "rm -rf *",
          "sudo *"
        ],
        "effect": "deny"
      },
      {
        "capability": "shell",
        "match": ["git *"],
        "effect": "allow"
      },
      {
        "capability": "fs_read",
        "effect": "allow"
      }
    ],
    "policies": ["read-only-shell"]
  }
}
JSON
ok "Creado: $GF"
show_file "$GF"

step "Validando el JSON del agente…"
python3 -c "import json; json.load(open('$GF')); print('JSON OK')" \
  && ok "git-flow.json es válido." \
  || warn "git-flow.json tiene un error de JSON."

pause

explain "Leamos las reglas de git-flow como política de seguridad" \
  "  deny  shell push --force / reset --hard / branch -D / clean -fd / rm / sudo" \
  "        → NO puede reescribir historia ni destruir nada." \
  "  allow shell git *  → SÍ puede crear ramas, hacer add/commit, ver estado." \
  "  deny  fs_read .env/.pem/.key/secrets → NO lee secretos." \
  "Como deny gana sobre allow, un 'git push --force' queda BLOQUEADO aunque" \
  "'git *' esté permitido."

explain "Cómo usarlo en el chat" \
  "  kiro-cli --v3 chat --agent git-flow" \
  "Pídele algo como:" \
  "  'Crea la rama hackaton-kiro si no existe y commitea el avance actual con" \
  "   un mensaje que describa lo que cambió.'" \
  "Repite el commit después de cada hito importante del taller."

title "Acto 10 completado ✅"
explain "Ya tenemos quién versione el trabajo del hackathon de forma segura:" \
  "rama propia (hackaton-kiro) y commits por cada avance significativo." \
  "" \
  "➡  Último paso — EN VIVO (sin script): los Specs."
