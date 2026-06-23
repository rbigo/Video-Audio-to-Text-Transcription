from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from .paths import AUDIO_DIR, FFMPEG_BIN_DIR, FFMPEG_EXE, safe_output_path
from .utils import run_command, sanitize_filename

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".flv", ".webm", ".wmv", ".m4v", ".ts"}


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_audio(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_EXTENSIONS


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def extract_audio(input_path: Path) -> Path:
    if not FFMPEG_EXE.exists():
        raise FileNotFoundError(
            f"ffmpeg.exe was not found. Place ffmpeg.exe and ffprobe.exe under: {FFMPEG_BIN_DIR}"
        )
    source = input_path.expanduser().resolve(strict=True)
    output_name = sanitize_filename(source.stem) + ".wav"
    output_path = safe_output_path(AUDIO_DIR / output_name)
    if output_path == source:
        output_path = safe_output_path(AUDIO_DIR / f"{sanitize_filename(source.stem)}.asr.wav")
    command = [
        str(FFMPEG_EXE),
        "-y",
        "-i",
        str(source),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_path),
    ]
    run_command(command, "ffmpeg.log", "ffmpeg 音频提取失败。")
    return output_path
