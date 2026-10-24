#!/usr/bin/env bash
# Levanta la demo de reporth en local: crea venv, instala deps, siembra datos
# y arranca la API en http://localhost:8000
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

if [ ! -d .venv ]; then
  echo "▶ Creando entorno virtual…"
  "$PYTHON" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "▶ Instalando dependencias…"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "▶ Sembrando datos de ejemplo…"
python seed.py

echo "▶ Arrancando la API en http://localhost:8000  (Ctrl+C para parar)"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
