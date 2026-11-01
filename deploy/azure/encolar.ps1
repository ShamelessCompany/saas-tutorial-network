# Sube uno o varios workflows YAML a la cola de la VM. El próximo ciclo del timer los procesa.
# Uso:  deploy\azure\encolar.ps1 config\clickbank_affiliate.yaml [otro.yaml ...]
param([Parameter(Mandatory = $true, ValueFromRemainingArguments = $true)][string[]]$Workflows)
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\config.ps1"
$destino = Destino
foreach ($w in $Workflows) {
  if (-not (Test-Path $w)) { throw "No existe $w" }
  $nombre = "{0}_{1}" -f (Get-Date -Format "yyyyMMdd_HHmmss"), (Split-Path $w -Leaf)
  scp $w "${destino}:/tmp/$nombre"
  ssh $destino "sudo install -o tutoriales -g tutoriales -m 644 /tmp/$nombre /opt/tutoriales/app/workflows/queue/$nombre && rm /tmp/$nombre"
  Write-Host "En cola: $nombre"
}
