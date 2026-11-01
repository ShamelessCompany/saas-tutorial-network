# P3 se monta en la misma VM que la Fábrica (P2). Si el repo de P2 está al lado, se usan sus datos
# (deploy\azure\config.ps1 de PipelineNoticiasAdsense, que crear_vm.ps1 rellena). Si no, ponlos aquí.
$P2_CONFIG = Join-Path $PSScriptRoot "..\..\..\PipelineNoticiasAdsense\deploy\azure\config.ps1"
if (Test-Path $P2_CONFIG) {
  . $P2_CONFIG
} else {
  $VM_IP     = ""
  $VM_USER   = "sena"
  $GRUPO     = "rg-fabrica"
  $VM_NOMBRE = "vm-fabrica"
  function Destino { if (-not $VM_IP) { throw "Falta VM_IP en deploy\azure\config.ps1" }; return "$VM_USER@$VM_IP" }
}
