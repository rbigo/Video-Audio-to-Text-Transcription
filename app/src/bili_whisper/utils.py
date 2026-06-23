from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

from .paths import LOGS_DIR, ensure_dirs, safe_output_path

WINDOWS_FORBIDDEN = r'<>:"/\|?*'


class CommandError(RuntimeError):
    def __init__(self, message: str, command: list[str], returncode: int, stdout: str, stderr: str):
        super().__init__(message)
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def setup_logging() -> None:
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(LOGS_DIR / "app.log", encoding="utf-8"),
        ],
    )


def get_logger(name: str, file_name: str | None = None) -> logging.Logger:
    ensure_dirs()
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if file_name and not any(
        isinstance(handler, logging.FileHandler)
        and Path(getattr(handler, "baseFilename", "")).name == file_name
        for handler in logger.handlers
    ):
        handler = logging.FileHandler(LOGS_DIR / file_name, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger


def sanitize_filename(value: str, fallback: str = "output") -> str:
    name = "".join("_" if ch in WINDOWS_FORBIDDEN else ch for ch in value)
    name = re.sub(r"\s+", " ", name).strip().strip(".")
    return name[:180] or fallback


def run_command(command: list[str], log_name: str, failure_message: str) -> subprocess.CompletedProcess[str]:
    logger = get_logger(log_name.removesuffix(".log"), log_name)
    safe_command = ["<cookie-file>" if part.lower().endswith("bilibili.txt") else part for part in command]
    logger.info("COMMAND %s", subprocess.list2cmdline(safe_command))
    completed = subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if completed.stdout:
        logger.info("STDOUT %s", completed.stdout.strip())
    if completed.stderr:
        logger.info("STDERR %s", completed.stderr.strip())
    if completed.returncode != 0:
        raise CommandError(
            f"{failure_message}\n\nstdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}",
            command,
            completed.returncode,
            completed.stdout,
            completed.stderr,
        )
    return completed


def write_text(path: Path, content: str) -> Path:
    target = safe_output_path(path)
    target.write_text(content, encoding="utf-8", newline="\n")
    return target
