#!/usr/bin/env python3
"""
SaaS Tutorial Network - End-to-End Video Generator Demo
Automates browser actions, screen recording, narration synthesis, and multiformat video packaging.
"""
import argparse
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_workflow
from src.mock_saas import MockSaaSServer
from src.recorder import record_workflow_sync
from src.voiceover import generate_voiceover
from src.video_composer import compose_horizontal, compose_vertical_short, find_ffmpeg_binary

def main():
    parser = argparse.ArgumentParser(description="Generate automated SaaS tutorial videos")
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "config" / "default_workflow.yaml"),
        help="Path to YAML workflow file"
    )
    parser.add_argument("--url", default=None, help="Optional URL to record (defaults to mock SaaS)")
    parser.add_argument("--headed", action="store_true", help="Launch browser visibly")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "output"), help="Output directory")
    args = parser.parse_args()

    print("=" * 65)
    print(" RED DE CANALES DE TUTORIALES SAAS - MOTOR DE DEMO")
    print("=" * 65)

    start_time = time.time()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = PROJECT_ROOT / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Config
    print("\n[1/5] Cargando configuracion de workflow...")
    workflow = load_workflow(args.config)
    print(f"  -> Titulo: {workflow.get('title')}")
    print(f"  -> Pasos definidos: {len(workflow.get('steps', []))}")

    # 2. Narration Audio
    print("\n[2/5] Generando narracion estructurada (Hook -> Problema -> Solucion -> Afiliado)...")
    narration_cfg = workflow.get("narration", {})
    audio_path = None
    if narration_cfg.get("enabled", True):
        voice = narration_cfg.get("voice", "es-ES-AlvaroNeural")
        script_parts = narration_cfg.get("script_parts", {})
        target_audio = temp_dir / "voiceover.mp3"
        audio_path = generate_voiceover(script_parts, target_audio, voice=voice)
        print(f"  -> Audio generado: {audio_path.name} ({audio_path.stat().st_size} bytes)")

    # 3. Target Environment & Recording
    print("\n[3/5] Grabando sesion de navegador en 1080p con Playwright...")
    server = None
    target_url = args.url

    try:
        if not target_url:
            mock_dir = PROJECT_ROOT / "demo_assets" / "mock_saas"
            server = MockSaaSServer(mock_dir)
            target_url = server.start()
            print(f"  -> Servidor SaaS simulado activo en: {target_url}")

        raw_recording = record_workflow_sync(
            target_url=target_url,
            workflow=workflow,
            output_dir=temp_dir,
            headless=not args.headed
        )
        print(f"  -> Captura de pantalla completada: {raw_recording.name}")

        # 4. Packaging
        print("\n[4/5] Ensamblando video multiformato con FFmpeg...")
        ffmpeg_bin = find_ffmpeg_binary()
        print(f"  -> Motor FFmpeg: {ffmpeg_bin}")

        horiz_out = out_dir / "tutorial_16x9_youtube.mp4"
        vert_out = out_dir / "tutorial_9x16_shorts.mp4"

        print("  - Renderizando version horizontal (16:9 1080p)...")
        compose_horizontal(raw_recording, audio_path, horiz_out, ffmpeg_bin=ffmpeg_bin)
        print(f"    [OK] Listo: {horiz_out} ({horiz_out.stat().st_size / (1024*1024):.2f} MB)")

        print("  - Renderizando version vertical (9:16 Shorts/TikTok)...")
        compose_vertical_short(raw_recording, audio_path, vert_out, ffmpeg_bin=ffmpeg_bin)
        print(f"    [OK] Listo: {vert_out} ({vert_out.stat().st_size / (1024*1024):.2f} MB)")

    finally:
        if server:
            server.stop()

    elapsed = time.time() - start_time
    print("\n" + "=" * 65)
    print(f" [EXITO] DEMO GENERADA CORRECTAMENTE en {elapsed:.1f} segundos")
    print(f" Carpeta de salida: {out_dir}")
    print("=" * 65)

if __name__ == "__main__":
    main()
