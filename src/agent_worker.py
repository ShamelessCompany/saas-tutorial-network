"""24/7 Autonomous Agent Daemon for SaaS Tutorial Generation and YouTube Publishing."""
import argparse
import json
import logging
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_workflow
from src.mock_saas import MockSaaSServer
from src.recorder import record_workflow_sync
from src.voiceover import generate_voiceover
from src.video_composer import compose_horizontal, compose_vertical_short, find_ffmpeg_binary
from src.youtube_uploader import upload_to_youtube

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "agent.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("SaaSAgentDaemon")

class SaaSAgentDaemon:
    def __init__(
        self,
        queue_dir: Path | str = PROJECT_ROOT / "workflows" / "queue",
        completed_dir: Path | str = PROJECT_ROOT / "workflows" / "completed",
        history_file: Path | str = PROJECT_ROOT / "history.json",
        interval_hours: float = 8.0,
        dry_run: bool = False
    ):
        self.queue_dir = Path(queue_dir)
        self.completed_dir = Path(completed_dir)
        self.history_file = Path(history_file)
        self.interval_seconds = int(interval_hours * 3600)
        self.dry_run = dry_run

        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.completed_dir.mkdir(parents=True, exist_ok=True)

    def load_history(self) -> Dict[str, Any]:
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"total_published": 0, "publications": []}

    def save_history(self, history: Dict[str, Any]):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def process_workflow(self, workflow_path: Path):
        logger.info(f"Procesando workflow: {workflow_path.name}")
        workflow = load_workflow(workflow_path)

        timestamp_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        temp_dir = PROJECT_ROOT / "temp" / timestamp_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        output_dir = PROJECT_ROOT / "output" / timestamp_id
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Narracion
            narration_cfg = workflow.get("narration", {})
            audio_path = None
            if narration_cfg.get("enabled", True):
                voice = narration_cfg.get("voice", "es-ES-AlvaroNeural")
                audio_target = temp_dir / "voiceover.mp3"
                audio_path = generate_voiceover(
                    narration_cfg.get("script_parts", {}),
                    audio_target,
                    voice=voice
                )
                logger.info(f"Audio sintetizado: {audio_path.name}")

            # 2. Grabacion
            target_url = workflow.get("target_url")
            server = None
            if not target_url:
                mock_dir = PROJECT_ROOT / "demo_assets" / "mock_saas"
                server = MockSaaSServer(mock_dir)
                target_url = server.start()

            try:
                raw_vid = record_workflow_sync(
                    target_url=target_url,
                    workflow=workflow,
                    output_dir=temp_dir,
                    headless=True
                )
                logger.info(f"Captura web completada: {raw_vid.name}")

                # 3. Composicion
                ffmpeg_bin = find_ffmpeg_binary()
                horiz_video = output_dir / "tutorial_16x9.mp4"
                vert_video = output_dir / "short_9x16.mp4"

                compose_horizontal(raw_vid, audio_path, horiz_video, ffmpeg_bin=ffmpeg_bin)
                compose_vertical_short(raw_vid, audio_path, vert_video, ffmpeg_bin=ffmpeg_bin)
                logger.info("Renderizado de video 16:9 y 9:16 finalizado con exito")

            finally:
                if server:
                    server.stop()

            # 4. Publicacion en YouTube (Video Largo)
            title = workflow.get("title", "Tutorial SaaS Automatizado")
            affiliate = workflow.get("affiliate", {})
            aff_link = affiliate.get("link", "https://tudominio.com/afiliado")
            aff_code = affiliate.get("code", "DESCUENTO")

            description = (
                f"{title}\n\n"
                f"🔗 Accede a la plataforma con descuento: {aff_link}\n"
                f"🎁 Cupón exclusivo: {aff_code}\n\n"
                f"Tutorial paso a paso para configurar tu flujo de trabajo en minutos.\n"
                f"#SaaS #Automatizacion #Productividad #AI"
            )

            yt_id_horiz = upload_to_youtube(
                video_path=horiz_video,
                title=title,
                description=description,
                tags=["saas", "tutorial", "ia", "automatizacion", "nocode"],
                privacy_status="public",
                dry_run=self.dry_run
            )

            # 5. Publicacion de YouTube Short
            short_title = f"{title[:80]} #Shorts"
            yt_id_short = upload_to_youtube(
                video_path=vert_video,
                title=short_title,
                description=f"Mira el tutorial completo con link en bio: {aff_link}",
                tags=["shorts", "tutorial", "ia", "saas"],
                privacy_status="public",
                dry_run=self.dry_run
            )

            # Archivar y guardar historial
            history = self.load_history()
            history["total_published"] += 2
            history["publications"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "workflow": workflow_path.name,
                "youtube_16x9": yt_id_horiz,
                "youtube_short": yt_id_short,
                "affiliate_code": aff_code
            })
            self.save_history(history)

            # Mover archivo procesado a completados
            dest = self.completed_dir / f"{timestamp_id}_{workflow_path.name}"
            shutil.move(str(workflow_path), str(dest))
            logger.info(f"Workflow archivado exitosamente en: {dest.name}")

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def run_cycle(self):
        queue_files = sorted(list(self.queue_dir.glob("*.yaml")) + list(self.queue_dir.glob("*.yml")))

        if not queue_files:
            logger.info("Cola vacia. Verificando plantilla por defecto...")
            default_cfg = PROJECT_ROOT / "config" / "default_workflow.yaml"
            if default_cfg.exists():
                # Enviar una copia a la cola para mantener actividad continua
                target = self.queue_dir / f"task_{int(time.time())}.yaml"
                shutil.copy(str(default_cfg), str(target))
                queue_files = [target]

        for w_file in queue_files:
            try:
                self.process_workflow(w_file)
                # YouTube API Quota guard: pausa prudente entre publicaciones
                time.sleep(60)
            except Exception as e:
                logger.error(f"Fallo al procesar {w_file.name}: {e}", exc_info=True)

    def run_forever(self):
        logger.info(f"Iniciando Agente 24/7 en segundo plano (Intervalo: {self.interval_seconds // 3600} horas)...")
        while True:
            try:
                self.run_cycle()
            except Exception as e:
                logger.critical(f"Error inesperado en ciclo del agente: {e}", exc_info=True)

            logger.info(f"Ciclo terminado. Durmiendo {self.interval_seconds // 3600} horas hasta la siguiente tanda...")
            time.sleep(self.interval_seconds)

def main():
    parser = argparse.ArgumentParser(description="24/7 Autonomous SaaS Tutorial Publisher Agent")
    parser.add_argument("--interval", type=float, default=8.0, help="Publishing interval in hours (default: 8.0)")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit immediately")
    parser.add_argument("--dry-run", action="store_true", help="Simulate YouTube upload without contacting API")
    args = parser.parse_args()

    daemon = SaaSAgentDaemon(interval_hours=args.interval, dry_run=args.dry_run)
    if args.once:
        daemon.run_cycle()
    else:
        daemon.run_forever()

if __name__ == "__main__":
    main()
