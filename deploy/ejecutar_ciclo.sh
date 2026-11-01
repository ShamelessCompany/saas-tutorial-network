#!/usr/bin/env bash
# Un ciclo del agente, lanzado por tutoriales.timer.
# Reglas de seguridad que agent_worker.py no trae por sí solo:
#  - Sin PUBLICAR=1 en .env, siempre corre con --dry-run.
#  - Con la cola vacía y PUBLICAR=1 no hace nada: agent_worker volvería a publicar la plantilla
#    de demo una y otra vez, y YouTube lo trata como contenido repetitivo.
#  - En simulación no toca la cola: agent_worker archiva el workflow en completed/ aunque sea
#    --dry-run, y se perdería sin haberse publicado. La simulación usa solo la plantilla de demo.
set -euo pipefail

APP="${APP:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
PYTHON="${PYTHON:-/opt/tutoriales/venv/bin/python}"
cd "$APP"

PUBLICAR=0
DIAS_OUTPUT=7
if [[ -f .env ]]; then
  # Solo se leen estas dos claves; el .env no se ejecuta como script
  v=$(grep -E '^PUBLICAR=' .env | tail -n1 | cut -d= -f2 | tr -d '[:space:]' || true)
  [[ -n "$v" ]] && PUBLICAR=$v
  v=$(grep -E '^DIAS_OUTPUT=' .env | tail -n1 | cut -d= -f2 | tr -d '[:space:]' || true)
  [[ "$v" =~ ^[0-9]+$ ]] && DIAS_OUTPUT=$v
fi

# Limpieza de renders viejos
if [[ -d output ]]; then
  find output -mindepth 1 -maxdepth 1 -mtime +"$DIAS_OUTPUT" -exec rm -rf {} +
fi

pendientes=$(find workflows/queue -maxdepth 1 \( -name '*.yaml' -o -name '*.yml' \) 2>/dev/null | wc -l)

if [[ "$PUBLICAR" == "1" ]]; then
  if [[ "$pendientes" -eq 0 ]]; then
    echo "Cola vacía: no se publica nada (no se recicla la plantilla de demo). Añade workflows a workflows/queue/."
    exit 0
  fi
  echo "Publicando $pendientes workflow(s) en YouTube."
  exec "$PYTHON" src/agent_worker.py --once
else
  if [[ "$pendientes" -gt 0 ]]; then
    echo "Simulación con $pendientes workflow(s) en cola: no se procesan para no archivarlos sin publicar. Activa la publicación con modo.ps1 -Publicar."
    exit 0
  fi
  echo "Simulación (PUBLICAR=$PUBLICAR) con la plantilla de demo."
  exec "$PYTHON" src/agent_worker.py --once --dry-run
fi
