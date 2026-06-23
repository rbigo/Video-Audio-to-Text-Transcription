from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import DEFAULT_FASTER_WHISPER_MODEL, DEFAULT_FUNASR_MODEL, DEFAULT_LANGUAGE, apply_local_environment
from .paths import CACHE_DIR, FASTER_WHISPER_MODEL_DIR, FUNASR_MODEL_DIR, ensure_dirs
from .utils import get_logger


@dataclass(frozen=True)
class PreloadResult:
    engine: str
    model: str
    path: Path | None


def preload_faster_whisper(model: str = DEFAULT_FASTER_WHISPER_MODEL) -> PreloadResult:
    ensure_dirs()
    apply_local_environment()
    logger = get_logger("asr", "asr.log")
    logger.info("preload faster-whisper model=%s", model)
    try:
        from faster_whisper.utils import download_model
    except ImportError as exc:
        raise RuntimeError("faster-whisper is not installed. Run .\\scripts\\bootstrap.ps1 first.") from exc

    path = download_model(
        model,
        output_dir=str(FASTER_WHISPER_MODEL_DIR),
        cache_dir=str(CACHE_DIR / "huggingface"),
    )
    return PreloadResult(engine="faster-whisper", model=model, path=Path(path))


def preload_funasr(model: str = DEFAULT_FUNASR_MODEL, language: str = DEFAULT_LANGUAGE) -> PreloadResult:
    ensure_dirs()
    apply_local_environment()
    logger = get_logger("asr", "asr.log")
    logger.info("preload funasr model=%s", model)
    try:
        from funasr import AutoModel
    except ImportError as exc:
        raise RuntimeError("FunASR is not installed. Run .\\scripts\\bootstrap.ps1 -WithFunASR first.") from exc

    try:
        loaded = AutoModel(model=model, hub="ms", disable_update=True)
    except TypeError:
        loaded = AutoModel(model=model)
    model_path = _find_funasr_model_path(model)
    # Keep a reference until the function returns so lazy loaders finish initialization.
    _ = loaded
    _ = language
    return PreloadResult(engine="funasr", model=model, path=model_path)


def _find_funasr_model_path(model: str) -> Path | None:
    relative = Path(*model.split("/"))
    candidates = [
        CACHE_DIR / "modelscope" / "models" / relative,
        FUNASR_MODEL_DIR / "models" / relative,
        FUNASR_MODEL_DIR / relative,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None
