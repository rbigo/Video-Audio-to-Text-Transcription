from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson

from .bilibili_playlist import BilibiliPlaylist, fetch_bilibili_playlist, format_playlist_text, playlist_to_dict
from .config import DEFAULT_COMPUTE_TYPE, DEFAULT_DEVICE, DEFAULT_ENGINE, DEFAULT_FASTER_WHISPER_MODEL, DEFAULT_FUNASR_MODEL, DEFAULT_LANGUAGE
from .downloader import download_audio, download_subs, list_subs
from .media import extract_audio, is_audio, is_url, is_video
from .paths import TRANSCRIPTS_DIR, safe_output_path
from .subtitle import parse_subtitle_file, write_json, write_srt, write_txt
from .transcriber_base import Segment
from .transcriber_faster_whisper import FasterWhisperTranscriber
from .transcriber_funasr import FunASRTranscriber
from .utils import get_logger, sanitize_filename, write_text


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


def list_playlist(url: str) -> BilibiliPlaylist:
    return fetch_bilibili_playlist(url)


def transcribe_playlist(
    url: str,
    *,
    engine: str = DEFAULT_ENGINE,
    model: str | None = None,
    device: str = DEFAULT_DEVICE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    language: str = DEFAULT_LANGUAGE,
    vad: bool = True,
    output_dir: Path = TRANSCRIPTS_DIR,
    limit: int | None = None,
    dry_run: bool = False,
) -> list[Path]:
    playlist = fetch_bilibili_playlist(url)
    if limit is not None and limit < 1:
        raise ValueError("limit must be greater than 0.")
    episodes = playlist.episodes[:limit] if limit else playlist.episodes
    if not episodes:
        raise RuntimeError("No episodes were found in the Bilibili playlist.")

    directory_name = sanitize_filename(f"{playlist.title} [{playlist.id or playlist.source_bvid}]")
    playlist_dir = safe_output_path(output_dir / directory_name)
    playlist_dir.mkdir(parents=True, exist_ok=True)
    text_path = write_text(playlist_dir / "playlist.txt", format_playlist_text(playlist))
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    manifest_path = _write_playlist_manifest(
        playlist_dir,
        playlist=playlist,
        selected_count=len(episodes),
        dry_run=dry_run,
        results=results,
        errors=errors,
    )
    outputs = [text_path, manifest_path]
    if dry_run:
        return outputs

    logger = get_logger("app", "app.log")
    for episode in episodes:
        logger.info("playlist episode index=%s bvid=%s title=%s", episode.index, episode.bvid, episode.title)
        try:
            episode_outputs = process_url(
                episode.url,
                engine=engine,
                model=model,
                device=device,
                compute_type=compute_type,
                language=language,
                vad=vad,
                output_dir=playlist_dir,
            )
        except Exception as exc:
            logger.exception("playlist episode failed bvid=%s", episode.bvid)
            errors.append(
                {
                    "index": episode.index,
                    "bvid": episode.bvid,
                    "title": episode.title,
                    "url": episode.url,
                    "error": str(exc),
                }
            )
        else:
            results.append(
                {
                    "index": episode.index,
                    "bvid": episode.bvid,
                    "title": episode.title,
                    "url": episode.url,
                    "outputs": [str(path) for path in episode_outputs],
                }
            )
            outputs.extend(episode_outputs)
        manifest_path = _write_playlist_manifest(
            playlist_dir,
            playlist=playlist,
            selected_count=len(episodes),
            dry_run=dry_run,
            results=results,
            errors=errors,
        )

    if errors:
        error_text = "\n".join(
            "\n".join(
                [
                    f"{item['index']:02d}. {item['bvid']} {item['title']}",
                    f"    {item['url']}",
                    f"    {item['error']}",
                    "",
                ]
            )
            for item in errors
        )
        errors_path = write_text(playlist_dir / "playlist-errors.txt", error_text)
        outputs.append(errors_path)
    if errors and not results:
        raise RuntimeError(f"All playlist episodes failed. See manifest: {manifest_path}")
    return outputs


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


def _write_playlist_manifest(
    directory: Path,
    *,
    playlist: BilibiliPlaylist,
    selected_count: int,
    dry_run: bool,
    results: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> Path:
    target = safe_output_path(directory / "playlist.json")
    payload = {
        "playlist": playlist_to_dict(playlist),
        "selected_count": selected_count,
        "dry_run": dry_run,
        "completed_count": len(results),
        "failed_count": len(errors),
        "results": results,
        "errors": errors,
    }
    target.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2 | orjson.OPT_APPEND_NEWLINE))
    return target


def _engine_dir_name(engine: str) -> str:
    normalized = engine.lower().replace("_", "-")
    if normalized in {"faster-whisper", "funasr", "bilibili-subtitle"}:
        return normalized
    return sanitize_filename(normalized)
