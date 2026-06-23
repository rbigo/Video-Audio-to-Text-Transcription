from __future__ import annotations

import os

from .paths import CACHE_DIR, FASTER_WHISPER_MODEL_DIR, FUNASR_MODEL_DIR, ROOT

DEFAULT_ENGINE = "faster-whisper"
DEFAULT_FASTER_WHISPER_MODEL = "large-v3-turbo"
DEFAULT_FUNASR_MODEL = "iic/SenseVoiceSmall"
DEFAULT_DEVICE = "cuda"
DEFAULT_COMPUTE_TYPE = "float16"
DEFAULT_LANGUAGE = "zh"
DEFAULT_BEAM_SIZE = 5


def apply_local_environment() -> None:
    values = {
        "BILI_WHISPER_HOME": ROOT,
        "HF_HOME": CACHE_DIR / "huggingface",
        "HF_HUB_CACHE": CACHE_DIR / "huggingface" / "hub",
        "HUGGINGFACE_HUB_CACHE": CACHE_DIR / "huggingface" / "hub",
        "TRANSFORMERS_CACHE": CACHE_DIR / "huggingface" / "transformers",
        "MODELSCOPE_CACHE": CACHE_DIR / "modelscope",
        "MODELSCOPE_HOME": CACHE_DIR / "modelscope",
        "XDG_CACHE_HOME": CACHE_DIR / "xdg",
        "PIP_CACHE_DIR": CACHE_DIR / "pip",
        "UV_CACHE_DIR": CACHE_DIR / "uv",
        "UV_PYTHON_INSTALL_DIR": ROOT / "runtime" / "python",
        "UV_TOOL_DIR": ROOT / "runtime" / "uv-tools",
        "UV_TOOL_BIN_DIR": ROOT / "runtime" / "bin",
        "TORCH_HOME": CACHE_DIR / "torch",
        "TEMP": CACHE_DIR / "temp",
        "TMP": CACHE_DIR / "temp",
        "FASTER_WHISPER_MODEL_DIR": FASTER_WHISPER_MODEL_DIR,
        "FUNASR_MODEL_DIR": FUNASR_MODEL_DIR,
    }
    for key, value in values.items():
        os.environ[key] = str(value)
    ensure_cuda_dll_paths()


def ensure_cuda_dll_paths() -> None:
    cuda_bins = [
        ROOT / ".venv" / "Lib" / "site-packages" / "nvidia" / "cublas" / "bin",
        ROOT / ".venv" / "Lib" / "site-packages" / "nvidia" / "cuda_nvrtc" / "bin",
        ROOT / ".venv" / "Lib" / "site-packages" / "nvidia" / "cudnn" / "bin",
    ]
    existing_path = os.environ.get("PATH", "")
    for directory in cuda_bins:
        if directory.exists():
            text = str(directory)
            if text not in existing_path:
                os.environ["PATH"] = f"{text};{os.environ.get('PATH', '')}"
            if hasattr(os, "add_dll_directory"):
                try:
                    os.add_dll_directory(text)
                except OSError:
                    pass
