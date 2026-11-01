# Lanza un ciclo ya (sin esperar al timer) y muestra su salida.
. "$PSScriptRoot\config.ps1"
ssh -t (Destino) "sudo systemctl start tutoriales; journalctl -u tutoriales -n 60 --no-pager"
