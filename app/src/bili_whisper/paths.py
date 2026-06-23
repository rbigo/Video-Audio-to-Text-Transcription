from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(os.environ.get("BILI_WHISPER_HOME", Path(__file__).resolve().parents[3]))
APP_DIR = ROOT / "app"
RUNTIME_DIR = ROOT / "runtime"
RUNTIME_BIN_DIR = RUNTIME_DIR / "bin"
FFMPEG_BIN_DIR = RUNTIME_DIR / "ffmpeg" / "bin"
FFMPEG_EXE = FFMPEG_BIN_DIR / "ffmpeg.exe"
FFPROBE_EXE = FFMPEG_BIN_DIR / "ffprobe.exe"
DENO_EXE = RUNTIME_BIN_DIR / "deno.exe"

CACHE_DIR = ROOT / "cache"
MODELS_DIR = ROOT / "models"
FASTER_WHISPER_MODEL_DIR = MODELS_DIR / "faster-whisper"
FUNASR_MODEL_DIR = MODELS_DIR / "funasr"

DATA_DIR = ROOT / "data"
COOKIES_DIR = DATA_DIR / "cookies"
BILIBILI_COOKIE_FILE = COOKIES_DIR / "bilibili.txt"
YOUTUBE_COOKIE_FILE = COOKIES_DIR / "youtube.txt"
DOWNLOADS_DIR = DATA_DIR / "downloads"
AUDIO_DIR = DATA_DIR / "audio"
SUBTITLES_DIR = DATA_DIR / "subtitles"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
JOBS_DIR = DATA_DIR / "jobs"
LOGS_DIR = DATA_DIR / "logs"
TEMP_DIR = DATA_DIR / "temp"

PROJECT_DIRS = [
    APP_DIR / "src" / "bili_whisper",
    ROOT / "scripts",
    RUNTIME_BIN_DIR,
    RUNTIME_DIR / "python",
    FFMPEG_BIN_DIR,
    ROOT / ".venv",
    CACHE_DIR / "pip",
    CACHE_DIR / "uv",
    CACHE_DIR / "xdg",
    CACHE_DIR / "torch",
    CACHE_DIR / "huggingface",
    CACHE_DIR / "huggingface" / "hub",
    CACHE_DIR / "huggingface" / "transformers",
    CACHE_DIR / "modelscope",
    CACHE_DIR / "temp",
    FASTER_WHISPER_MODEL_DIR,
    FUNASR_MODEL_DIR,
    COOKIES_DIR,
    DOWNLOADS_DIR,
    AUDIO_DIR,
    SUBTITLES_DIR,
    TRANSCRIPTS_DIR,
    JOBS_DIR,
    LOGS_DIR,
    TEMP_DIR,
]

FORBIDDEN_WRITE_MARKERS = ("C:\\", "%USERPROFILE%", "AppData", "Desktop", "Downloads", "Documents")


def ensure_dirs() -> None:
    for directory in PROJECT_DIRS:
        directory.mkdir(parents=True, exist_ok=True)
    BILIBILI_COOKIE_FILE.touch(exist_ok=True)
    YOUTUBE_COOKIE_FILE.touch(exist_ok=True)


def resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def assert_under_root(path: Path) -> Path:
    ensure_dirs()
    target = resolved(path)
    root = resolved(ROOT)
    if target == root or root in target.parents:
        return target
    raise ValueError(f"拒绝写入项目目录外路径: {target}")


def safe_output_path(path: Path) -> Path:
    target = assert_under_root(path)
    text = str(target)
    for marker in FORBIDDEN_WRITE_MARKERS:
        if marker.lower() in text.lower() and not str(target).lower().startswith(str(resolved(ROOT)).lower()):
            raise ValueError(f"拒绝写入高风险路径: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    return target
