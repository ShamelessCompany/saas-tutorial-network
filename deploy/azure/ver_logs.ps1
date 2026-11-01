# Muestra el historial del timer y los logs del agente en la VM (Ctrl+C para salir).
. "$PSScriptRoot\config.ps1"
ssh -t (Destino) "systemctl list-timers tutoriales.timer --no-pager; journalctl -u tutoriales -f -n 100"
