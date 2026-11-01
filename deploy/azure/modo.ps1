# Cambia entre simulación y publicación real en la VM.
# Uso:  deploy\azure\modo.ps1 -Publicar     (sube a YouTube)
#       deploy\azure\modo.ps1               (vuelve a simulación, --dry-run)
param([switch]$Publicar)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\config.ps1"
$valor = if ($Publicar) { "1" } else { "0" }
ssh -t (Destino) "sudo sed -i 's/^PUBLICAR=.*/PUBLICAR=$valor/' /opt/tutoriales/app/.env && sudo grep '^PUBLICAR=' /opt/tutoriales/app/.env"
if ($Publicar) { Write-Host "Modo publicación: solo publica si hay workflows en la cola (encolar.ps1)." } else { Write-Host "Modo simulación." }
