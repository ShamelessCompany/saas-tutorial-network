# Red de Tutoriales SaaS (P3) en Azure

P3 no tiene VM propia: se instala **en la VM de la Fábrica de Contenido (P2)**, `vm-fabrica` del grupo `rg-fabrica`, que se crea con `PipelineNoticiasAdsense\deploy\azure\crear_vm.ps1`. Si los dos repos están lado a lado en `D:\ProyectosProgramacion\`, `config.ps1` toma la IP de la configuración de P2. Si no, rellénala en `deploy\azure\config.ps1`.

Todo se ejecuta desde PowerShell en la carpeta del repo. Si PowerShell bloquea los scripts:
`powershell -ExecutionPolicy Bypass -File deploy\azure\NOMBRE.ps1`.

## Cómo queda en la VM

| Qué | Dónde |
|---|---|
| Código | `/opt/tutoriales/app` (usuario de sistema `tutoriales`, sin shell) |
| Entorno de Python | `/opt/tutoriales/venv` |
| Chromium de Playwright | `/opt/tutoriales/ms-playwright` |
| Servicio de un ciclo | `tutoriales.service` → `deploy/ejecutar_ciclo.sh` |
| Horario | `tutoriales.timer`: lunes, miércoles y viernes a las 03:00 (hora de Bogotá). Si la VM estaba apagada, corre al encender. |
| Límites | `Nice=15`, `CPUWeight=20`, `MemoryMax=1500M`, para no quitarle recursos a la Fábrica |
| Estado | `.env`, `credentials/`, `workflows/queue`, `workflows/completed` y `history.json`; ninguno se pisa al actualizar |
| Copias | Diarias en `/opt/tutoriales/backups` (se guardan 14) |
| Renders | `output/`; se borran a los 7 días (`DIAS_OUTPUT` en `.env`) |

## Pasos

1. **VM creada** con el paso 1 de `PipelineNoticiasAdsense\deploy\azure\README_AZURE.md`.
2. **Instalar o actualizar:**
   ```powershell
   deploy\azure\subir_codigo.ps1
   ```
   La primera instalación deja `PUBLICAR=0`: **modo simulación**.
3. **Probar en simulación:**
   ```powershell
   deploy\azure\ejecutar_ahora.ps1
   ```
   Graba y renderiza la plantilla de demo con el SaaS simulado, sin subir nada.
4. **Credenciales de YouTube** (una vez, en tu PC):
   ```powershell
   pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
   # client_secret.json (OAuth de "App de escritorio") en credentials\
   python -c "from src.youtube_uploader import get_authenticated_service; get_authenticated_service()"
   deploy\azure\subir_secretos.ps1
   ```
   El login de Google necesita navegador, así que `token.json` se genera en tu PC y se sube. Se renueva solo.
5. **Encolar tutoriales y publicar:**
   ```powershell
   deploy\azure\encolar.ps1 config\clickbank_affiliate.yaml
   deploy\azure\modo.ps1 -Publicar
   ```
   Para volver a simulación: `deploy\azure\modo.ps1`.
6. **Seguimiento:** `deploy\azure\ver_logs.ps1`.

## Reglas de seguridad de `ejecutar_ciclo.sh`

`src/agent_worker.py` tiene dos comportamientos peligrosos en un servidor desatendido; el script los evita sin cambiar el agente:

| Caso | Qué haría `agent_worker.py --once` | Qué hace `ejecutar_ciclo.sh` |
|---|---|---|
| Cola vacía y publicando | Vuelve a encolar `config/default_workflow.yaml` y lo publica **público**, cada ciclo | No hace nada y lo deja en el log |
| Cola con trabajos y en simulación | Los procesa con `--dry-run` y **los archiva en `completed/` sin publicarlos** | No los toca |
| Cola vacía y en simulación | — | Simula con la plantilla de demo |
| Cola con trabajos y `PUBLICAR=1` | — | Publica |

Cualquier valor de `PUBLICAR` que no sea `1` cuenta como simulación.

## A tener en cuenta
- La privacidad de subida está fija en `public` dentro de `agent_worker.py`. Mientras el proyecto de Google Cloud no pase la auditoría de la API de YouTube, los videos subidos quedan **privados** de todas formas (ver la sección 4 de `README_AZURE.md` de P2).
- Cuota de YouTube: cada subida cuesta 1.600 unidades de las 10.000 diarias. Cada workflow sube 2 videos (16:9 y Short), y la Fábrica de P2 comparte esa cuota si usa el mismo proyecto de Google Cloud.
- El servicio antiguo `deploy/saas-agent.service` (root, bucle 24/7) se eliminó. Si quedó instalado en una VM, `instalar.sh` lo desactiva y lo borra.
