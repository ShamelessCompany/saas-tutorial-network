# 🚀 Red de Canales de Tutoriales SaaS & Monetización de Afiliados

> **Carpeta Local del Proyecto:** `D:\Programacion\SaaSTutorialNetwork`  
> **Organización:** Shameless Company — Proyecto 3  
> **Objetivo:** Automatización integral de captura de software, síntesis de narración estructurada y renderizado multiformato (YouTube 16:9 y Shorts/Reels 9:16) con monetización de enlaces de afiliados.

---

## 📋 Arquitectura de la Solución

```
                     [Definición de Software Objetivo]
                                     │
                                     ▼
               [YAML Workflow: Hook -> Problema -> Solución 2 Clics -> Afiliado]
                                     │
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
       [Grabación de Pantalla Web]         [Generador de Voz TTS]
          Playwright Chromium 1080p           Edge-TTS Neural (ES)
                     │                               │
                     └───────────────┬───────────────┘
                                     ▼
                        [Ensamblador FFmpeg]
                     ┌───────────────┴───────────────┐
                     ▼                               ▼
      [YouTube Horizontal 16:9]           [Shorts / Reels Vertical 9:16]
        1080p + Banner Afiliado             Padding desenfocado + CTA
```

---

## 🛠️ Requisitos Previos

Antes de comenzar, asegúrate de contar con:

1. **Python 3.10 o superior** (verificar con `python --version`).
2. **Git** (verificar con `git --version`).
3. **FFmpeg** para la codificación y ensamblado de video:
   - **Windows:** Ejecutar en PowerShell:
     ```powershell
     winget install Gyan.FFmpeg
     ```
     *(O alternativamente, el proyecto incluye soporte automático mediante `imageio-ffmpeg`)*.
   - **Linux (Ubuntu/Debian / DigitalOcean):**
     ```bash
     sudo apt update && sudo apt install -y ffmpeg
     ```
   - **macOS:**
     ```bash
     brew install ffmpeg
     ```

---

## ⚡ Instalación Paso a Paso

### 1. Ubicarse en el directorio del proyecto
```powershell
cd D:\Programacion\SaaSTutorialNetwork
```

### 2. Crear y activar el entorno virtual
En Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(Si PowerShell bloquea scripts, ejecuta una vez: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

En CMD:
```cmd
.\.venv\Scripts\activate.bat
```

En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar librerías de Python
```bash
pip install -r requirements.txt
```

### 4. Instalar navegadores para Playwright
Este paso descarga el binario headless optimizado de Chromium para capturar la pantalla:
```bash
playwright install chromium
```

---

## 🎬 Ejecución de la Demo

El proyecto incluye un **SaaS simulado en modo oscuro** (`demo_assets/mock_saas`) para que puedas generar videos de prueba completos de forma local, offline e inmediata sin depender de credenciales o sitios web externos.

### Ejecución rápida (Headless):
```bash
python run_demo.py
```

### Ejecución visual (Ver el navegador interactuando en tiempo real):
```bash
python run_demo.py --headed
```

### Grabar una URL o SaaS externo real:
```bash
python run_demo.py --url "https://app.ejemplo.com" --config config/default_workflow.yaml
```

---

## 📦 Archivos de Salida Generados

Al finalizar la ejecución, encontrarás los videos listos para publicación en la carpeta `output/`:

| Archivo | Formato | Resolución | Destino Principal |
| :--- | :--- | :--- | :--- |
| `output/tutorial_16x9_youtube.mp4` | Horizontal 16:9 | 1920x1080 | YouTube (Video Largo) |
| `output/tutorial_9x16_shorts.mp4` | Vertical 9:16 | 1080x1920 | YouTube Shorts, TikTok, Instagram Reels |

---

## 🗂️ Estructura del Proyecto

```
D:\Programacion\SaaSTutorialNetwork/
├── README.md                      # Esta documentación y guía de despliegue
├── requirements.txt               # Librerías (Playwright, PyYAML, Edge-TTS, imageio-ffmpeg)
├── .gitignore                     # Exclusión de videos temporales y entornos
├── run_demo.py                    # Script principal de orquestación end-to-end
├── config/
│   └── default_workflow.yaml     # Definición declarativa de pasos, guion y afiliados
├── demo_assets/
│   └── mock_saas/
│       └── index.html             # Interfaz web SaaS moderna para pruebas deterministas
├── src/
│   ├── __init__.py
│   ├── config.py                  # Validador de configuración YAML
│   ├── mock_saas.py               # Servidor HTTP local para testing
│   ├── recorder.py                # Motor de automatización y grabación con Playwright
│   ├── voiceover.py               # Síntesis de voz estructurada con Edge-TTS
│   └── video_composer.py          # Renderizador de videos 16:9 y 9:16 con FFmpeg
└── tests/
    └── test_workflow.py           # Batería de pruebas unitarias automáticas
```

---

## ⚙️ Cómo Personalizar un Tutorial (YAML)

Edita o duplica `config/default_workflow.yaml`:

```yaml
title: "Cómo Automatizar Leads en 2 Clics"
saas_name: "NexusFlow AI"

affiliate:
  code: "TUTORIAL30"
  banner_text: "🎁 30% DTO con código TUTORIAL30 • Link en descripción"

narration:
  enabled: true
  voice: "es-ES-AlvaroNeural"  # Opciones: es-MX-JorgeNeural, es-ES-ElviraNeural
  script_parts:
    hook: "¿Sigues copiando y pegando datos de tus clientes manualmente?"
    problem: "Eso consume horas valiosas y provoca errores humanos costosos."
    solution: "Hoy te muestro cómo automatizar todo en dos simples clics."
    cta: "Tienes el cupón con 30% de descuento en la descripción."

steps:
  - action: "wait"
    duration_ms: 1500
    callout: "Paso 1: Abrir panel"
  - action: "click"
    selector: "#btn-create"
    duration_ms: 1200
  - action: "type"
    selector: "input[name='prompt']"
    text: "Sincronizar Stripe con Notion"
    delay_ms: 50
```

---

## 🌐 Despliegue en la Nube (DigitalOcean Droplet)

Para ejecutar este generador de forma desatendida y programada en un Droplet de DigitalOcean (Ubuntu 24.04):

1. **Instalar paquetes del sistema:**
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv ffmpeg xvfb
   ```
2. **Clonar repositorio e instalar:**
   ```bash
   git clone <URL_DE_TU_REPOSITORIO> SaaSTutorialNetwork
   cd SaaSTutorialNetwork
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   playwright install --with-deps chromium
   ```
3. **Ejecución desatendida vía Cron (Ej: 3 tutoriales semanales):**
   ```bash
   0 9 * * 1,3,5 cd /root/SaaSTutorialNetwork && .venv/bin/python run_demo.py >> /var/log/tutorial_cron.log 2>&1
   ```

---

## 👥 Coordinación del Equipo (6 Personas)

- **Curaduría & Afiliados (2 Personas):** Identificar SaaS con comisiones recurrentes (20-40%) y diseñar los casos de uso "Solución en 2 clics".
- **Programación de Automatizaciones (2 Personas):** Crear selectores Playwright y redactar los archivos YAML de configuración.
- **Empaque, SEO & Miniaturas (2 Personas):** Creación de miniaturas de alto contraste, configuración de títulos clickeables y distribución con enlaces trackeados.
