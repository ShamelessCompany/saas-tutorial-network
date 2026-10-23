#!/usr/bin/env python3
"""
Record Any URL with a Realistic Human Cursor & Auto-Exploration
Usage:
  python record_url.py --url https://whop.com/blog/whop-clips/
  python record_url.py --url https://app.ejemplo.com --title "Mi Review de SaaS"
"""
import argparse
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from src.recorder import record_workflow_sync
from src.voiceover import generate_voiceover
from src.video_composer import compose_horizontal, compose_vertical_short, find_ffmpeg_binary

def generate_auto_steps(url: str, custom_title: str | None = None):
    """Generates natural human browsing actions for any URL."""
    domain = urlparse(url).netloc.replace("www.", "")
    title = custom_title or f"Explorando {domain}"

    steps = [
        {"action": "wait", "duration_ms": 1800, "callout": f"Paso 1: Ingreso a {domain}"},
        {"action": "hover", "selector": "h1, header, .hero", "duration_ms": 1200},
        {"action": "scroll", "delta_y": 600, "duration_ms": 2200, "callout": "Paso 2: Explorando contenido y características"},
        {"action": "hover", "selector": "button, a[role='button'], a.btn, a", "duration_ms": 1500},
        {"action": "scroll", "delta_y": 700, "duration_ms": 2200, "callout": "Paso 3: Verificando requisitos y beneficios"},
        {"action": "hover", "selector": "button:has-text('Join'), button:has-text('Empezar'), button:has-text('Sign'), a:has-text('Join'), button", "duration_ms": 1800},
        {"action": "click", "selector": "button:has-text('Join'), button:has-text('Empezar'), a:has-text('Join'), button, a", "duration_ms": 2500, "callout": "Paso 4: ¡Acceso directo y activación!"},
        {"action": "wait", "duration_ms": 2500, "callout": "¡Enlace oficial y detalles en la descripción!"}
    ]

    workflow = {
        "title": title,
        "slug": domain.split(".")[0] + "_tutorial",
        "target_url": url,
        "affiliate": {
            "banner_text": f"🔥 Acceso Oficial a {domain} • Link en Descripción"
        },
        "narration": {
            "enabled": True,
            "voice": "es-ES-AlvaroNeural",
            "script_parts": {
                "hook": f"¿Buscabas cómo aprovechar al máximo {domain}?",
                "problem": "Muchas veces es difícil entender cómo funciona la plataforma desde el principio.",
                "solution": "Hoy te muestro paso a paso cómo explorar y activar tu cuenta en solo dos clics.",
                "cta": "Tienes el enlace oficial directo en la descripción y en el primer comentario fijado."
            }
        },
        "viewport": {"width": 1920, "height": 1080},
        "steps": steps
    }
    return workflow

def record_custom_url(url: str, title: str | None = None, banner: str | None = None):
    print("=" * 65)
    print(f" 🎬 GRABADOR WEB CON CURSOR HUMANO EN VIVO")
    print(f" 🌐 URL Objetivo: {url}")
    print("=" * 65)

    start_time = time.time()
    out_dir = PROJECT_ROOT / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = PROJECT_ROOT / "temp" / f"record_{int(time.time())}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    workflow = generate_auto_steps(url, custom_title=title)
    if banner:
        workflow["affiliate"]["banner_text"] = banner

    slug = workflow["slug"]

    # 1. Narracion
    print("\n[1/4] Sintetizando locucion neural...")
    audio_target = temp_dir / "voiceover.mp3"
    audio_path = generate_voiceover(
        workflow["narration"]["script_parts"],
        audio_target,
        voice=workflow["narration"]["voice"]
    )
    print(f"  -> Audio listo: {audio_path.name}")

    # 2. Grabacion con cursor humano
    print("\n[2/4] Grabando interaccion con cursor humano simulado...")
    print("  - Version horizontal desktop (1920x1080)...")
    raw_horiz = record_workflow_sync(
        target_url=url,
        workflow=workflow,
        output_dir=temp_dir / "horiz",
        headless=True
    )

    print("  - Version vertical nativa para Shorts/TikTok (1080x1920)...")
    wf_vert = dict(workflow)
    wf_vert["viewport"] = {"width": 1080, "height": 1920}
    raw_vert = record_workflow_sync(
        target_url=url,
        workflow=wf_vert,
        output_dir=temp_dir / "vert",
        headless=True
    )

    # 3. Ensamblado
    print("\n[3/4] Renderizando videos multiformato con FFmpeg...")
    ffmpeg_bin = find_ffmpeg_binary()
    horiz_out = out_dir / f"{slug}_16x9_youtube.mp4"
    vert_out = out_dir / f"{slug}_9x16_shorts.mp4"

    compose_horizontal(raw_horiz, audio_path, horiz_out, ffmpeg_bin=ffmpeg_bin)
    print(f"  [OK] Horizontal listo: {horiz_out.name} ({horiz_out.stat().st_size / (1024*1024):.2f} MB)")

    compose_vertical_short(raw_vert, audio_path, vert_out, ffmpeg_bin=ffmpeg_bin)
    print(f"  [OK] Vertical listo: {vert_out.name} ({vert_out.stat().st_size / (1024*1024):.2f} MB)")

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(f" 🎉 PROCESO COMPLETADO en {elapsed:.1f} segundos")
    print(f" 📁 Ubicacion: {out_dir}")
    print("=" * 65)
    return horiz_out, vert_out

def main():
    parser = argparse.ArgumentParser(description="Record any URL with an animated human cursor")
    parser.add_argument("--url", required=True, help="Website URL to navigate and record")
    parser.add_argument("--title", default=None, help="Custom video title")
    parser.add_argument("--banner", default=None, help="Custom banner / CTA text")
    args = parser.parse_args()

    record_custom_url(args.url, title=args.title, banner=args.banner)

if __name__ == "__main__":
    main()
