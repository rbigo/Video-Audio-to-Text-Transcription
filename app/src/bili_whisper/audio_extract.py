from __future__ import annotations

from pathlib import Path

from .downloader import download_audio
from .media import extract_audio, is_url, is_video
from .utils import get_logger


def extract_video_audio(source: str | Path) -> Path:
    """Convert a URL or local downloaded video file to project-local WAV audio."""
    value = str(source).strip()
    logger = get_logger("app", "app.log")
    if is_url(value):
        output_path = download_audio(value)
        logger.info("extract_audio url=%s output=%s", value, output_path)
        return output_path

    input_path = Path(value).expanduser().resolve(strict=True)
    if not is_video(input_path):
        raise ValueError(f"Only local video files are supported for extract-audio: {input_path}")
    output_path = extract_audio(input_path)
    logger.info("extract_audio input=%s output=%s", input_path, output_path)
    return output_path
