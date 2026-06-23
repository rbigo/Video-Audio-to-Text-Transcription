from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel


class Segment(BaseModel):
    id: int
    start: float
    end: float
    text: str


class Transcriber(Protocol):
    def transcribe(self, input_path: Path) -> list[Segment]:
        ...
