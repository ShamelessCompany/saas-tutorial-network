"""Video composer & multiformat exporter (16:9 and 9:16) using FFmpeg."""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

def find_ffmpeg_binary() -> str:
    """Resolve FFmpeg binary path across system PATH, imageio-ffmpeg, or winget dirs."""
    # 1. System PATH
    cmd = shutil.which("ffmpeg")
    if cmd:
        return cmd

    # 2. imageio_ffmpeg
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return exe
    except Exception:
        pass

    # 3. Known WinGet / Local AppData paths on Windows
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        winget_pkgs = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        if winget_pkgs.exists():
            for match in winget_pkgs.glob("**/ffmpeg.exe"):
                return str(match)

    raise FileNotFoundError(
        "FFmpeg binary not found. Install it via winget (winget install Gyan.FFmpeg) "
        "or install imageio-ffmpeg (pip install imageio-ffmpeg)."
    )

def compose_horizontal(
    raw_video_path: Path | str,
    audio_path: Optional[Path | str],
    output_path: Path | str,
    ffmpeg_bin: Optional[str] = None
) -> Path:
    """Exports 1080p 16:9 Landscape Video for YouTube."""
    raw_video = Path(raw_video_path).resolve()
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    bin_path = ffmpeg_bin or find_ffmpeg_binary()

    cmd = [
        bin_path, "-y",
        "-i", str(raw_video),
    ]

    if audio_path and Path(audio_path).exists():
        cmd.extend(["-i", str(Path(audio_path).resolve())])
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(out)
        ])
    else:
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            str(out)
        ])

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg horizontal render failed:\n{res.stderr}")

    return out

def compose_vertical_short(
    raw_video_path: Path | str,
    audio_path: Optional[Path | str],
    output_path: Path | str,
    title_text: str = "TUTORIAL SAAS EN 30 SEGUNDOS",
    affiliate_badge: str = "🎁 Codigo: TUTORIAL30 | Link en Bio",
    ffmpeg_bin: Optional[str] = None
) -> Path:
    """
    Exports 1080x1920 9:16 Vertical Video for YouTube Shorts, Instagram Reels & TikTok.
    Uses blurred background padding with sharp centered SaaS interaction.
    """
    raw_video = Path(raw_video_path).resolve()
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    bin_path = ffmpeg_bin or find_ffmpeg_binary()

    # Filter complex:
    # 1. Scale background to fill 1080x1920, blur it
    # 2. Scale foreground to width 1080 (maintaining 16:9 aspect = 1080x608)
    # 3. Overlay foreground at center (y = (1920-608)/2 = 656)
    filter_graph = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
        "[0:v]scale=1080:-1[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[vcomposed]"
    )

    cmd = [
        bin_path, "-y",
        "-i", str(raw_video),
    ]

    if audio_path and Path(audio_path).exists():
        cmd.extend(["-i", str(Path(audio_path).resolve())])
        cmd.extend([
            "-filter_complex", filter_graph,
            "-map", "[vcomposed]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(out)
        ])
    else:
        cmd.extend([
            "-filter_complex", filter_graph,
            "-map", "[vcomposed]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(out)
        ])

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg vertical render failed:\n{res.stderr}")

    return out
