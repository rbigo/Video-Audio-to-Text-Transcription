from __future__ import annotations

from pathlib import Path

from .config import DEFAULT_COMPUTE_TYPE, DEFAULT_DEVICE, DEFAULT_ENGINE, DEFAULT_FASTER_WHISPER_MODEL, DEFAULT_FUNASR_MODEL, DEFAULT_LANGUAGE
from .downloader import download_audio, download_subs, list_subs
from .media import extract_audio, is_audio, is_url, is_video
from .paths import TRANSCRIPTS_DIR, safe_output_path
from .subtitle import parse_subtitle_file, write_json, write_srt, write_txt
from .transcriber_base import Segment
from .transcriber_faster_whisper import FasterWhisperTranscriber
from .transcriber_funasr import FunASRTranscriber
from .utils import get_logger, sanitize_filename


def process_url(
    url: str,
    *,
    engine: str = DEFAULT_ENGINE,
    model: str | None = None,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    language: str = DEFAULT_LANGUAGE,
    vad: bool = True,
    output_dir: Path = TRANSCRIPTS_DIR,
) -> list[Path]:
    logger = get_logger("app", "app.log")
    logger.info("process_url input=%s engine=%s model=%s", url, engine, model)
    try:
        list_subs(url)
    except Exception as exc:
        logger.info("list_subs failed, will still try subtitle download: %s", exc)
    try:
        subtitle_paths = download_subs(url)
    except Exception as exc:
        logger.info("download_subs failed, will try audio download: %s", exc)
        subtitle_paths = []
    for subtitle_path in subtitle_paths:
        segments = parse_subtitle_file(subtitle_path)
        if segments:
            logger.info("使用 B站已有字幕: %s", subtitle_path)
            return _write_outputs(
                segments,
                source=str(subtitle_path),
                video_name=sanitize_filename(subtitle_path.stem),
                engine="bilibili-subtitle",
                model="existing",
                language=language,
                output_dir=output_dir,
            )
    audio_path = download_audio(url)
    return transcribe_file(
        audio_path,
        engine=engine,
        model=model,
        device=device,
        compute_type=compute_type,
        language=language,
        vad=vad,
        output_dir=output_dir,
    )


def process_file(
    path: Path,
    *,
    engine: str = DEFAULT_ENGINE,
    model: str | None = None,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    language: str = DEFAULT_LANGUAGE,
    vad: bool = True,
    output_dir: Path = TRANSCRIPTS_DIR,
) -> list[Path]:
    input_path = path.expanduser().resolve(strict=True)
    if is_video(input_path) or is_audio(input_path):
        audio_path = extract_audio(input_path)
    else:
        raise ValueError(f"不支持的文件类型: {input_path}")
    return transcribe_file(
        audio_path,
        engine=engine,
        model=model,
        device=device,
        compute_type=compute_type,
        language=language,
        vad=vad,
        output_dir=output_dir,
    )


def transcribe_file(
    path: Path,
    *,
    engine: str = DEFAULT_ENGINE,
    model: str | None = None,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    language: str = DEFAULT_LANGUAGE,
    vad: bool = True,
    output_dir: Path = TRANSCRIPTS_DIR,
    output_suffix: str | None = None,
) -> list[Path]:
    input_path = path.expanduser().resolve(strict=True)
    transcriber, selected_model = _make_transcriber(
        engine=engine,
        model=model,
        device=device,
        compute_type=compute_type,
        language=language,
        vad=vad,
    )
    segments = transcriber.transcribe(input_path)
    video_name = sanitize_filename(input_path.stem.removesuffix(".asr"))
    return _write_outputs(
        segments,
        source=str(input_path),
        video_name=video_name,
        engine=engine,
        model=selected_model,
        language=language,
        output_dir=output_dir,
        approximate_timestamps=bool(getattr(transcriber, "approximate_timestamps", False)),
    )


def process_any(value: str, **kwargs) -> list[Path]:
    if is_url(value):
        return process_url(value, **kwargs)
    return process_file(Path(value), **kwargs)


def compare(path: Path, *, language: str = DEFAULT_LANGUAGE, output_dir: Path = TRANSCRIPTS_DIR) -> list[Path]:
    outputs: list[Path] = []
    input_path = path.expanduser().resolve(strict=True)
    if is_video(input_path) or is_audio(input_path):
        audio_path = extract_audio(input_path)
    else:
        raise ValueError(f"不支持的文件类型: {input_path}")
    outputs.extend(
        transcribe_file(
            audio_path,
            engine="faster-whisper",
            model=DEFAULT_FASTER_WHISPER_MODEL,
            language=language,
            output_dir=output_dir,
            output_suffix="faster-whisper",
        )
    )
    outputs.extend(
        transcribe_file(
            audio_path,
            engine="funasr",
            model=DEFAULT_FUNASR_MODEL,
            language=language,
            output_dir=output_dir,
            output_suffix="funasr",
        )
    )
    return outputs


def _make_transcriber(
    *,
    engine: str,
    model: str | None,
    device: str,
    compute_type: str,
    language: str,
    vad: bool,
):
    normalized = engine.lower()
    if normalized == "faster-whisper":
        selected_model = model or DEFAULT_FASTER_WHISPER_MODEL
        return (
            FasterWhisperTranscriber(
                model=selected_model,
                device=device,
                compute_type=compute_type,
                language=language,
                vad=vad,
            ),
            selected_model,
        )
    if normalized == "funasr":
        selected_model = model or DEFAULT_FUNASR_MODEL
        return FunASRTranscriber(model=selected_model, language=language), selected_model
    raise ValueError("engine 必须是 faster-whisper 或 funasr")


def _write_outputs(
    segments: list[Segment],
    *,
    source: str,
    video_name: str,
    engine: str,
    model: str,
    language: str,
    output_dir: Path,
    approximate_timestamps: bool = False,
) -> list[Path]:
    engine_dir_name = _engine_dir_name(engine)
    directory = safe_output_path(output_dir / sanitize_filename(video_name) / engine_dir_name)
    directory.mkdir(parents=True, exist_ok=True)
    txt = write_txt(segments, directory / "transcript.txt")
    srt = write_srt(segments, directory / "transcript.srt")
    json_path = write_json(
        segments,
        directory / "transcript.json",
        source=source,
        engine=engine,
        model=model,
        language=language,
        approximate_timestamps=approximate_timestamps,
    )
    get_logger("app", "app.log").info("outputs=%s", [str(path) for path in (txt, srt, json_path)])
    return [txt, srt, json_path]


def _engine_dir_name(engine: str) -> str:
    normalized = engine.lower().replace("_", "-")
    if normalized in {"faster-whisper", "funasr", "bilibili-subtitle"}:
        return normalized
    return sanitize_filename(normalized)
