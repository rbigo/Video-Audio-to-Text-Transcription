from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from .config import (
    DEFAULT_COMPUTE_TYPE,
    DEFAULT_DEVICE,
    DEFAULT_ENGINE,
    DEFAULT_FASTER_WHISPER_MODEL,
    DEFAULT_FUNASR_MODEL,
    DEFAULT_LANGUAGE,
    apply_local_environment,
)
from .audio_extract import extract_video_audio
from .downloader import download_audio as download_audio_impl
from .downloader import download_subs as download_subs_impl
from .downloader import list_subs as list_subs_impl
from .paths import (
    CACHE_DIR,
    FASTER_WHISPER_MODEL_DIR,
    FFMPEG_EXE,
    FFPROBE_EXE,
    FUNASR_MODEL_DIR,
    LOGS_DIR,
    MODELS_DIR,
    ROOT,
    TRANSCRIPTS_DIR,
    YOUTUBE_COOKIE_FILE,
    ensure_dirs,
    safe_output_path,
)
from .pipeline import compare as compare_impl
from .pipeline import process_any, process_file
from .model_preload import preload_faster_whisper, preload_funasr
from .utils import CommandError, setup_logging

app = typer.Typer(help="Bilibili and local media transcription tool.")


@app.callback()
def main() -> None:
    ensure_dirs()
    apply_local_environment()
    setup_logging()


@app.command()
def gui() -> None:
    """Open the local GUI."""
    from .gui import main as gui_main

    gui_main()


@app.command()
def doctor() -> None:
    """Print local environment diagnostics."""
    _print("项目根目录", str(ROOT))
    _print("当前 Python 路径", sys.executable)
    _print("pip 缓存路径", os.environ.get("PIP_CACHE_DIR", ""))
    _print("uv 缓存路径", os.environ.get("UV_CACHE_DIR", ""))
    _print("HF_HOME", os.environ.get("HF_HOME", ""))
    _print("HF_HUB_CACHE", os.environ.get("HF_HUB_CACHE", ""))
    _print("MODELSCOPE_CACHE", os.environ.get("MODELSCOPE_CACHE", ""))
    _print("TORCH_HOME", os.environ.get("TORCH_HOME", ""))
    _print("TEMP", os.environ.get("TEMP", ""))
    _print("TMP", os.environ.get("TMP", ""))
    _print("faster-whisper 模型目录", str(FASTER_WHISPER_MODEL_DIR))
    _print("FunASR 模型目录", str(FUNASR_MODEL_DIR))
    _print("ffmpeg 路径", str(FFMPEG_EXE), FFMPEG_EXE.exists())
    _print("ffprobe 路径", str(FFPROBE_EXE), FFPROBE_EXE.exists())
    _print("yt-dlp 是否可用", _module_status("yt_dlp"))
    _print("faster-whisper 是否可导入", _module_status("faster_whisper"))
    _print("FunASR 是否可导入", _module_status("funasr"))
    _print("torch 是否可导入", _module_status("torch"))
    _cuda_info()
    nvidia = shutil.which("nvidia-smi")
    _print("nvidia-smi 是否可用", nvidia or "否", bool(nvidia))
    if nvidia:
        try:
            result = subprocess.run(
                [nvidia, "--query-gpu=name,memory.total", "--format=csv,noheader"],
                text=True,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if result.stdout.strip():
                _print("GPU 名称/显存", result.stdout.strip())
        except Exception as exc:
            _print("GPU 名称/显存", f"读取失败: {exc}", False)
    if str(MODELS_DIR).lower().startswith(str(ROOT).lower()):
        _print("模型目录检查", str(MODELS_DIR), True)
    else:
        _print("模型目录检查", str(MODELS_DIR), False)


@app.command("list-subs")
def list_subs(url: str) -> None:
    """List subtitles available for a Bilibili URL."""
    _run_or_exit(lambda: typer.echo(list_subs_impl(url)))


@app.command("download-subs")
def download_subs(url: str) -> None:
    """Download existing or auto subtitles for a Bilibili URL."""
    paths = _run_or_exit(lambda: download_subs_impl(url))
    if not paths:
        typer.echo("未下载到可用字幕。")
        return
    for path in paths:
        typer.echo(path)


@app.command("download-audio")
def download_audio(url: str) -> None:
    """Download and convert URL audio to 16 kHz mono WAV."""
    _run_or_exit(lambda: typer.echo(download_audio_impl(url)))


@app.command("extract-audio")
def extract_audio_command(file: Path) -> None:
    """Convert a local downloaded video file to WAV audio without transcription."""
    _run_or_exit(lambda: typer.echo(extract_video_audio(file)))


@app.command()
def transcribe(
    file: Path,
    engine: str = typer.Option(DEFAULT_ENGINE, "--engine"),
    model: Optional[str] = typer.Option(None, "--model"),
    device: str = typer.Option(DEFAULT_DEVICE, "--device"),
    compute_type: str = typer.Option(DEFAULT_COMPUTE_TYPE, "--compute-type"),
    language: str = typer.Option(DEFAULT_LANGUAGE, "--language"),
    vad: bool = typer.Option(True, "--vad/--no-vad"),
    output_dir: Path = typer.Option(TRANSCRIPTS_DIR, "--output-dir"),
) -> None:
    """Transcribe a local audio or video file."""
    outputs = _run_or_exit(
        lambda: process_file(
            file,
            engine=engine,
            model=model,
            device=device,
            compute_type=compute_type,
            language=language,
            vad=vad,
            output_dir=safe_output_path(output_dir),
        )
    )
    for path in outputs:
        typer.echo(path)


@app.command("all")
def all_command(
    url_or_file: str,
    engine: str = typer.Option(DEFAULT_ENGINE, "--engine"),
    model: Optional[str] = typer.Option(None, "--model"),
    device: str = typer.Option(DEFAULT_DEVICE, "--device"),
    compute_type: str = typer.Option(DEFAULT_COMPUTE_TYPE, "--compute-type"),
    language: str = typer.Option(DEFAULT_LANGUAGE, "--language"),
    vad: bool = typer.Option(True, "--vad/--no-vad"),
    output_dir: Path = typer.Option(TRANSCRIPTS_DIR, "--output-dir"),
) -> None:
    """Process a URL or local file end to end."""
    outputs = _run_or_exit(
        lambda: process_any(
            url_or_file,
            engine=engine,
            model=model,
            device=device,
            compute_type=compute_type,
            language=language,
            vad=vad,
            output_dir=safe_output_path(output_dir),
        )
    )
    for path in outputs:
        typer.echo(path)


@app.command()
def compare(file: Path, language: str = typer.Option(DEFAULT_LANGUAGE, "--language")) -> None:
    """Run faster-whisper and FunASR on the same local media file."""
    outputs = _run_or_exit(lambda: compare_impl(file, language=language))
    for path in outputs:
        typer.echo(path)


@app.command("preload-models")
def preload_models(
    engine: str = typer.Option("faster-whisper", "--engine", help="faster-whisper, funasr, or all"),
    faster_model: str = typer.Option(DEFAULT_FASTER_WHISPER_MODEL, "--faster-model"),
    funasr_model: str = typer.Option(DEFAULT_FUNASR_MODEL, "--funasr-model"),
    language: str = typer.Option(DEFAULT_LANGUAGE, "--language"),
) -> None:
    """Download ASR models into the project-local cache before the first transcription."""
    normalized = engine.strip().lower()
    if normalized not in {"faster-whisper", "funasr", "all"}:
        raise typer.BadParameter("engine must be faster-whisper, funasr, or all")
    if normalized in {"faster-whisper", "all"}:
        result = _run_or_exit(lambda: preload_faster_whisper(faster_model))
        typer.echo(f"{result.engine}: {result.model} -> {result.path}")
    if normalized in {"funasr", "all"}:
        result = _run_or_exit(lambda: preload_funasr(funasr_model, language=language))
        typer.echo(f"{result.engine}: {result.model} -> {result.path or 'project-local ModelScope cache'}")


def _module_status(module_name: str) -> str:
    return "是" if importlib.util.find_spec(module_name) else "否"


def _run_or_exit(func):
    try:
        return func()
    except CommandError as exc:
        typer.echo(str(exc), err=True)
        _print_cookie_hint(str(exc))
        raise typer.Exit(code=1) from exc
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        _print_cookie_hint(str(exc))
        raise typer.Exit(code=1) from exc


def _print_cookie_hint(message: str) -> None:
    lower = message.lower()
    if "youtube" in lower and ("not a bot" in lower or "sign in to confirm" in lower):
        typer.echo(
            "\nYouTube requires login verification for this request.\n"
            "Export cookies manually in Netscape cookies.txt format and save them to:\n"
            f"{YOUTUBE_COOKIE_FILE}\n"
            "Then rerun the same command.",
            err=True,
        )
    elif "youtube" in lower and "challenge solving failed" in lower:
        typer.echo(
            "\nYouTube JS challenge solving failed.\n"
            "The tool now enables yt-dlp remote EJS components for YouTube; rerun the command.\n",
            err=True,
        )


def _print(name: str, value: object, ok: bool | None = None) -> None:
    prefix = "INFO"
    if ok is True:
        prefix = "OK"
    elif ok is False:
        prefix = "ERROR"
    typer.echo(f"{prefix}: {name}: {value}")


def _cuda_info() -> None:
    try:
        import ctranslate2

        cuda_count = int(ctranslate2.get_cuda_device_count())
        _print("CUDA 是否可用", "是" if cuda_count > 0 else "否", cuda_count > 0)
        _print("CTranslate2 CUDA 设备数", str(cuda_count), cuda_count > 0)
    except Exception as exc:
        _print("CUDA 是否可用", f"CTranslate2 检测失败: {exc}", False)

    try:
        import torch
    except ImportError:
        _print("torch CUDA 信息", "未安装 torch；faster-whisper 基础路线可不安装")
        return
    available = bool(torch.cuda.is_available())
    _print("torch CUDA 是否可用", "是" if available else "否", available)
    if available:
        try:
            _print("GPU 名称", torch.cuda.get_device_name(0), True)
            props = torch.cuda.get_device_properties(0)
            _print("GPU 显存", f"{props.total_memory / 1024 ** 3:.1f} GB", True)
        except Exception as exc:
            _print("GPU 信息", f"读取失败: {exc}", False)
