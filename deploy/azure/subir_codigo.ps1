# Empaqueta el proyecto, lo sube a la VM e instala/actualiza P3 en /opt/tutoriales.
# No sube output/, .git, credentials/, .env ni el estado. En la VM no se pisan .env, credentials/, history.json ni workflows/.
# Uso:  powershell -ExecutionPolicy Bypass -File deploy\azure\subir_codigo.ps1
$ErrorActionPreference = "Stop"
. "$PSScriptRoot\config.ps1"
$destino = Destino
$raiz = (Resolve-Path "$PSScriptRoot\..\..").Path
$paquete = Join-Path $env:TEMP "tutoriales.tgz"

Write-Host "Empaquetando $raiz ..."
tar.exe -czf $paquete -C $raiz --exclude=.git --exclude=.venv --exclude=output --exclude=temp `
  --exclude=__pycache__ --exclude=credentials --exclude=.env --exclude=history.json --exclude=*.log .
if ($LASTEXITCODE -ne 0) { throw "Falló tar" }

Write-Host "Subiendo a $destino ..."
scp $paquete "${destino}:/tmp/tutoriales.tgz"
# sed quita los saltos de línea de Windows (CRLF) por si algún editor los añadió
ssh -t $destino "mkdir -p /tmp/tx && tar -xzf /tmp/tutoriales.tgz -C /tmp/tx ./deploy/actualizar.sh && sed -i 's/\r`$//' /tmp/tx/deploy/actualizar.sh && sudo bash /tmp/tx/deploy/actualizar.sh /tmp/tutoriales.tgz && rm -rf /tmp/tx"
Remove-Item $paquete
Write-Host "P3 instalado. El timer corre lunes, miércoles y viernes a las 03:00 (Bogotá)."
