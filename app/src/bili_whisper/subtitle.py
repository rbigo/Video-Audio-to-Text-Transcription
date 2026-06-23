from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

import orjson

from .paths import safe_output_path
from .transcriber_base import Segment


def format_srt_time(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_txt(segments: Iterable[Segment], output_path: Path) -> Path:
    target = safe_output_path(output_path)
    text = "\n".join(segment.text.strip() for segment in segments if segment.text.strip())
    target.write_text(text + ("\n" if text else ""), encoding="utf-8", newline="\n")
    return target


def write_srt(segments: Iterable[Segment], output_path: Path) -> Path:
    target = safe_output_path(output_path)
    blocks: list[str] = []
    for index, segment in enumerate(segments, start=1):
        blocks.append(
            f"{index}\n"
            f"{format_srt_time(segment.start)} --> {format_srt_time(segment.end)}\n"
            f"{segment.text.strip()}"
        )
    target.write_text("\n\n".join(blocks) + ("\n" if blocks else ""), encoding="utf-8", newline="\n")
    return target


def write_json(
    segments: Iterable[Segment],
    output_path: Path,
    *,
    source: str = "",
    engine: str = "",
    model: str = "",
    language: str = "zh",
    approximate_timestamps: bool = False,
) -> Path:
    target = safe_output_path(output_path)
    payload: dict[str, Any] = {
        "source": source,
        "engine": engine,
        "model": model,
        "language": language,
        "segments": [_segment_dict(segment) for segment in segments],
    }
    if approximate_timestamps:
        payload["note"] = "该 FunASR 模型未返回可靠时间戳，SRT 为近似时间轴。"
    target.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2 | orjson.OPT_APPEND_NEWLINE))
    return target


def parse_subtitle_file(path: Path) -> list[Segment]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".srt":
        return _parse_srt(text)
    return _parse_vtt_or_plain(text)


def _parse_srt(text: str) -> list[Segment]:
    segments: list[Segment] = []
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n").strip())
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        time_line = next((line for line in lines if "-->" in line), "")
        if not time_line:
            continue
        start_text, end_text = [part.strip().split(" ")[0] for part in time_line.split("-->", 1)]
        content = [line for line in lines if line != time_line and not line.isdigit()]
        if content:
            segments.append(
                Segment(
                    id=len(segments) + 1,
                    start=_parse_srt_time(start_text),
                    end=_parse_srt_time(end_text),
                    text=" ".join(content),
                )
            )
    return segments


def _parse_vtt_or_plain(text: str) -> list[Segment]:
    segments: list[Segment] = []
    current_start = 0.0
    current_end = 0.0
    current_lines: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        line = raw.strip()
        if not line or line == "WEBVTT" or line.startswith(("NOTE", "STYLE", "REGION")):
            if current_lines:
                segments.append(Segment(id=len(segments) + 1, start=current_start, end=current_end, text=" ".join(current_lines)))
                current_lines = []
            continue
        if "-->" in line:
            if current_lines:
                segments.append(Segment(id=len(segments) + 1, start=current_start, end=current_end, text=" ".join(current_lines)))
                current_lines = []
            start_text, end_text = [part.strip().split(" ")[0] for part in line.split("-->", 1)]
            current_start = _parse_srt_time(start_text.replace(".", ","))
            current_end = _parse_srt_time(end_text.replace(".", ","))
            continue
        if not line.isdigit():
            current_lines.append(re.sub(r"<[^>]+>", "", line))
    if current_lines:
        segments.append(Segment(id=len(segments) + 1, start=current_start, end=current_end, text=" ".join(current_lines)))
    if segments:
        return segments
    plain = "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip() and "-->" not in line and line.strip() != "WEBVTT"
    )
    return [Segment(id=1, start=0.0, end=max(1.0, len(plain) / 8), text=plain)] if plain else []


def _parse_srt_time(value: str) -> float:
    match = re.match(r"(?:(\d+):)?(\d{2}):(\d{2})[,.](\d{1,3})", value)
    if not match:
        return 0.0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    millis = int(match.group(4).ljust(3, "0")[:3])
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def _segment_dict(segment: Segment) -> dict[str, Any]:
    if hasattr(segment, "model_dump"):
        return segment.model_dump()
    return segment.dict()
