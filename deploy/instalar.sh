#!/usr/bin/env bash
# Instala o actualiza la Red de Tutoriales SaaS (P3) en Ubuntu 24.04.
# Pensado para convivir en la misma VM de Azure que la Fábrica de Contenido (P2):
# usuario propio, carpeta propia y un timer en vez de un proceso 24/7.
# Uso (en la VM, desde la carpeta donde subiste el código):  sudo bash deploy/instalar.sh
# Se puede repetir: no toca .env, credentials/, history.json ni workflows/ que ya existan.
set -euo pipefail

ORIGEN="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAIZ=/opt/tutoriales
APP=$RAIZ/app
VENV=$RAIZ/venv
NAVEGADORES=$RAIZ/ms-playwright

if [[ $EUID -ne 0 ]]; then echo "Ejecuta con sudo"; exit 1; fi

echo "==> Paquetes del sistema"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip ffmpeg fonts-dejavu fonts-liberation \
  fontconfig rsync tar >/dev/null

echo "==> Memoria de intercambio (si P2 no la creó ya)"
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> Usuario y carpetas"
id tutoriales &>/dev/null || useradd --system --create-home --home-dir $RAIZ --shell /usr/sbin/nologin tutoriales
mkdir -p $APP $RAIZ/backups

echo "==> Copiando el código (sin pisar estado ni secretos)"
rsync -a --delete \
  --exclude '.git' --exclude '__pycache__' --exclude '.venv' --exclude 'output/' --exclude 'temp/' \
  --exclude '.env' --exclude 'credentials/' --exclude 'history.json' --exclude '*.log' \
  --exclude 'workflows/' \
  "$ORIGEN"/ $APP/
# La cola y los completados son estado: solo se crean la primera vez
mkdir -p $APP/workflows/queue $APP/workflows/completed $APP/credentials $APP/output
# Primera instalación: modo simulación. Para publicar de verdad, PUBLICAR=1 en el .env de la VM.
if [[ ! -f $APP/.env ]]; then
  cat > $APP/.env <<ENV
# 0 = simula la subida a YouTube (--dry-run). 1 = publica de verdad.
PUBLICAR=0
# Días que se guardan los videos renderizados en output/
DIAS_OUTPUT=7
ENV
fi
chown -R tutoriales:tutoriales $RAIZ
chmod 600 $APP/.env
chmod 700 $APP/credentials

echo "==> Entorno de Python"
[[ -d $VENV ]] || sudo -u tutoriales python3 -m venv $VENV
sudo -u tutoriales $VENV/bin/pip install -q --upgrade pip
sudo -u tutoriales $VENV/bin/pip install -q -r $APP/requirements.txt

echo "==> Chromium para Playwright (dependencias como root, navegador para el usuario)"
$VENV/bin/python -m playwright install-deps chromium >/dev/null
sudo -u tutoriales env PLAYWRIGHT_BROWSERS_PATH=$NAVEGADORES $VENV/bin/python -m playwright install chromium >/dev/null

echo "==> Servicio y timer"
chmod 755 $APP/deploy/ejecutar_ciclo.sh
# tr quita los CRLF de Windows por si algún editor los añadió
for u in tutoriales.service tutoriales.timer; do tr -d '\r' < $APP/deploy/$u > /etc/systemd/system/$u; done
# El servicio viejo corría como root en bucle 24/7: si quedó de una instalación anterior, se retira
if [[ -f /etc/systemd/system/saas-agent.service ]]; then
  systemctl disable --now saas-agent >/dev/null 2>&1 || true
  rm -f /etc/systemd/system/saas-agent.service
fi
systemctl daemon-reload
systemctl enable --now tutoriales.timer >/dev/null

echo "==> Copia diaria del estado (se guardan 14)"
cat > /etc/cron.d/tutoriales <<CRON
45 3 * * * root tar -czf $RAIZ/backups/estado-\$(date +\%F).tgz -C $APP .env credentials workflows \$(cd $APP && ls history.json 2>/dev/null) && ls -1t $RAIZ/backups/estado-*.tgz | tail -n +15 | xargs -r rm
CRON

echo "==> Cortafuegos: solo SSH"
if command -v ufw >/dev/null; then ufw allow OpenSSH >/dev/null && ufw --force enable >/dev/null; fi

echo
systemctl list-timers tutoriales.timer --no-pager || true
grep -q '^PUBLICAR=1' $APP/.env && echo "Modo: PUBLICA en YouTube." || echo "Modo: SIMULACIÓN (PUBLICAR=0 en $APP/.env)."
echo "Listo. Ciclo manual: sudo systemctl start tutoriales  ·  Logs: journalctl -u tutoriales -n 100"
