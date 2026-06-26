from __future__ import annotations

from pathlib import Path

from .media import extract_audio, is_video
from .utils import get_logger


def extract_video_audio(path: Path) -> Path:
    """Convert a local downloaded video file to project-local WAV audio."""
    input_path = path.expanduser().resolve(strict=True)
    if not is_video(input_path):
        raise ValueError(f"Only local video files are supported for extract-audio: {input_path}")
    output_path = extract_audio(input_path)
    get_logger("app", "app.log").info("extract_audio input=%s output=%s", input_path, output_path)
    return output_path
