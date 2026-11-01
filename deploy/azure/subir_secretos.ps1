# Copia credentials\client_secret.json y credentials\token.json a la VM (permisos 600, usuario 'tutoriales').
# token.json se genera una vez en tu PC:
#   python -c "from src.youtube_uploader import get_authenticated_service; get_authenticated_service()"
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\config.ps1"
$destino = Destino
$raiz = (Resolve-Path "$PSScriptRoot\..\..").Path
$subidos = @()
foreach ($f in "client_secret.json", "token.json") {
  $ruta = Join-Path $raiz "credentials\$f"
  if (Test-Path $ruta) { scp $ruta "${destino}:/tmp/p3_$f"; $subidos += $f }
}
if (-not $subidos) { Write-Host "No encontré client_secret.json ni token.json en $raiz\credentials"; exit 1 }
if ($subidos -notcontains "token.json") { Write-Host "Aviso: sin token.json la VM no puede subir (no hay navegador para el login de Google)." }
$cmds = ($subidos | ForEach-Object { "sudo install -o tutoriales -g tutoriales -m 600 /tmp/p3_$_ /opt/tutoriales/app/credentials/$_ && rm /tmp/p3_$_" }) -join " && "
ssh -t $destino $cmds
Write-Host "Subidos: $($subidos -join ', ')."
