from __future__ import annotations

from pathlib import Path

from .config import DEFAULT_BEAM_SIZE, DEFAULT_COMPUTE_TYPE, DEFAULT_DEVICE, DEFAULT_FASTER_WHISPER_MODEL, DEFAULT_LANGUAGE, ensure_cuda_dll_paths
from .paths import FASTER_WHISPER_MODEL_DIR
from .transcriber_base import Segment
from .utils import get_logger

OOM_HINT = """GPU 显存不足。
可尝试：
--model large-v3 --compute-type int8_float16
--model large-v3-turbo --compute-type int8
--model medium --compute-type float16
--device cpu"""

CUDA_HINT = """CUDA 不可用。
将自动尝试 CPU，或请检查：
1. NVIDIA 驱动
2. CUDA 12 运行时 DLL
3. faster-whisper / ctranslate2 GPU 依赖"""

CUDA_DLL_HINT = """CUDA 运行时 DLL 未找到或无法加载。
已为项目配置 nvidia-cublas-cu12 / nvidia-cudnn-cu12 后请重新运行。
如果仍失败，请尝试：
--device cpu --compute-type int8"""


class FasterWhisperTranscriber:
    def __init__(
        self,
        *,
        model: str = DEFAULT_FASTER_WHISPER_MODEL,
        device: str = DEFAULT_DEVICE,
        compute_type: str = DEFAULT_COMPUTE_TYPE,
        language: str = DEFAULT_LANGUAGE,
        vad: bool = True,
        beam_size: int = DEFAULT_BEAM_SIZE,
    ):
        self.model_name = model
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.vad = vad
        self.beam_size = beam_size
        self.logger = get_logger("asr", "asr.log")

    def transcribe(self, input_path: Path) -> list[Segment]:
        ensure_cuda_dll_paths()
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("faster-whisper 未安装，请运行 .\\scripts\\bootstrap.ps1") from exc

        self.logger.info(
            "ASR engine=faster-whisper model=%s device=%s compute_type=%s input=%s",
            self.model_name,
            self.device,
            self.compute_type,
            input_path,
        )
        try:
            model = WhisperModel(
                model_size_or_path=self.model_name,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(FASTER_WHISPER_MODEL_DIR),
            )
            raw_segments, _info = model.transcribe(
                str(input_path),
                language=self.language,
                vad_filter=self.vad,
                beam_size=self.beam_size,
            )
            segments: list[Segment] = []
            for index, segment in enumerate(raw_segments, start=1):
                text = (segment.text or "").strip()
                if text:
                    segments.append(Segment(id=index, start=float(segment.start), end=float(segment.end), text=text))
            return segments
        except Exception as exc:
            message = str(exc)
            lower = message.lower()
            self.logger.exception("faster-whisper failed")
            if "is not found or cannot be loaded" in lower or "cublas64_12.dll" in lower or "cudnn" in lower:
                raise RuntimeError(CUDA_DLL_HINT) from exc
            if "out of memory" in lower or "cuda out of memory" in lower:
                raise RuntimeError(OOM_HINT) from exc
            if "cuda" in lower and self.device == "cuda":
                raise RuntimeError(CUDA_HINT) from exc
            raise
