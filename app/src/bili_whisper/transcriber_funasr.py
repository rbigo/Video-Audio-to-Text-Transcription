from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from .config import DEFAULT_FUNASR_MODEL, DEFAULT_LANGUAGE, apply_local_environment
from .transcriber_base import Segment
from .utils import get_logger

FUNASR_MISSING = "FunASR 未安装。\n请运行：\n.\\scripts\\bootstrap.ps1 -WithFunASR"


class FunASRTranscriber:
    def __init__(self, *, model: str = DEFAULT_FUNASR_MODEL, language: str = DEFAULT_LANGUAGE):
        self.model_name = model
        self.language = language
        self.approximate_timestamps = False
        self.logger = get_logger("asr", "asr.log")

    def transcribe(self, input_path: Path) -> list[Segment]:
        apply_local_environment()
        try:
            from funasr import AutoModel
        except ImportError as exc:
            raise RuntimeError(FUNASR_MISSING) from exc

        self.logger.info("ASR engine=funasr model=%s input=%s", self.model_name, input_path)
        try:
            try:
                model = AutoModel(model=self.model_name, hub="ms", disable_update=True)
            except TypeError:
                model = AutoModel(model=self.model_name)
            result = model.generate(input=str(input_path), language=self.language)
        except Exception:
            self.logger.exception("FunASR failed")
            raise
        return self._to_segments(result)

    def _to_segments(self, result: Any) -> list[Segment]:
        items = result if isinstance(result, list) else [result]
        segments: list[Segment] = []
        text_chunks: list[str] = []
        for item in items:
            if isinstance(item, dict):
                text = _clean_text(str(item.get("text") or item.get("sentence") or ""))
                timestamps = item.get("timestamp") or item.get("timestamps") or item.get("sentence_info")
                if timestamps:
                    segments.extend(self._segments_from_timestamps(text, timestamps))
                elif text:
                    text_chunks.append(text)
            elif isinstance(item, str) and item.strip():
                text_chunks.append(_clean_text(item))
        if segments:
            return [
                Segment(id=index, start=segment.start, end=segment.end, text=segment.text)
                for index, segment in enumerate(segments, start=1)
            ]
        text = "\n".join(text_chunks).strip()
        if not text:
            return []
        self.approximate_timestamps = True
        return [Segment(id=1, start=0.0, end=max(1.0, len(text) / 6), text=text)]

    def _segments_from_timestamps(self, text: str, timestamps: Any) -> list[Segment]:
        segments: list[Segment] = []
        if isinstance(timestamps, list):
            for entry in timestamps:
                if isinstance(entry, dict):
                    start = _seconds(entry.get("start") or entry.get("start_time") or 0)
                    end = _seconds(entry.get("end") or entry.get("end_time") or max(start + 1, 1))
                    content = _clean_text(str(entry.get("text") or entry.get("sentence") or ""))
                    if content:
                        segments.append(Segment(id=len(segments) + 1, start=start, end=end, text=content))
                elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                    start = _seconds(entry[0])
                    end = _seconds(entry[1])
                    if text:
                        segments.append(Segment(id=len(segments) + 1, start=start, end=end, text=text))
                        break
        if not segments and text:
            self.approximate_timestamps = True
            segments.append(Segment(id=1, start=0.0, end=max(1.0, len(text) / 6), text=text))
        return segments


def _seconds(value: Any) -> float:
    number = float(value or 0)
    return number / 1000 if number > 1000 else number


def _clean_text(text: str) -> str:
    return re.sub(r"<\|[^|]+?\|>", "", text).strip()
