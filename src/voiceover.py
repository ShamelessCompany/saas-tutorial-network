"""Voiceover generator using edge-tts with offline fallback."""
import asyncio
import math
import struct
import wave
from pathlib import Path
from typing import Dict, List

def _generate_fallback_audio(output_path: Path, duration_seconds: float = 6.0):
    """Generate a valid silent/soft-tone WAV file if TTS network is unavailable."""
    sample_rate = 24000
    total_samples = int(sample_rate * max(1.0, duration_seconds))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        # Gentle soft ambient tone at 220Hz fade-in fade-out
        data = bytearray()
        for i in range(total_samples):
            envelope = min(1.0, i / 2400.0) * min(1.0, (total_samples - i) / 2400.0)
            sample = int(300.0 * envelope * math.sin(2.0 * math.pi * 220.0 * (i / sample_rate)))
            data.extend(struct.pack("<h", sample))
        wav_file.writeframes(data)

async def _synthesize_edge_tts(text: str, voice: str, output_path: Path):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))

def generate_voiceover(
    script_parts: Dict[str, str],
    output_path: str | Path,
    voice: str = "es-ES-AlvaroNeural"
) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Build continuous narration text
    text_blocks: List[str] = []
    for key in ("hook", "problem", "solution", "cta"):
        val = script_parts.get(key)
        if val:
            text_blocks.append(val.strip())

    full_script = " ... ".join(text_blocks)
    if not full_script:
        _generate_fallback_audio(out, 4.0)
        return out

    try:
        asyncio.run(_synthesize_edge_tts(full_script, voice, out))
        if out.exists() and out.stat().st_size > 500:
            return out
    except Exception as e:
        print(f"[Voiceover] Edge-TTS notice ({e}). Generating fallback audio.")

    # Fallback WAV
    fallback_wav = out.with_suffix(".wav")
    _generate_fallback_audio(fallback_wav, duration_seconds=10.0)
    return fallback_wav
