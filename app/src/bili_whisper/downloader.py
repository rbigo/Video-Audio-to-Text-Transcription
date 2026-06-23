from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlparse

from .paths import (
    AUDIO_DIR,
    BILIBILI_COOKIE_FILE,
    COOKIES_DIR,
    DENO_EXE,
    FFMPEG_BIN_DIR,
    FFMPEG_EXE,
    SUBTITLES_DIR,
    YOUTUBE_COOKIE_FILE,
    ensure_dirs,
    safe_output_path,
)
from .utils import CommandError, run_command

DOWNLOAD_FAILURE = f"""Download failed.
Possible reasons:
1. The video requires login cookies.
2. The video is restricted or private.
3. The URL is invalid.
4. The site changed its extractor behavior.
5. yt-dlp is outdated.

Suggestions:
1. Update yt-dlp.
2. Check the matching cookies file under {COOKIES_DIR}.
3. Run list-subs first."""


def _cookie_args(url: str) -> list[str]:
    cookie_file = _cookie_file_for_url(url)
    if cookie_file and cookie_file.exists() and cookie_file.stat().st_size > 0:
        return ["--cookies", str(cookie_file)]
    return []


def _base_args(url: str) -> list[str]:
    return [sys.executable, "-m", "yt_dlp", *_site_args(url), "--windows-filenames", url]


def list_subs(url: str) -> str:
    ensure_dirs()
    command = [sys.executable, "-m", "yt_dlp", *_site_args(url), "--list-subs", url]
    completed = run_command(command, "yt-dlp.log", DOWNLOAD_FAILURE)
    return completed.stdout


def download_subs(url: str) -> list[Path]:
    ensure_dirs()
    before = _snapshot(SUBTITLES_DIR)
    output_template = str(safe_output_path(SUBTITLES_DIR / "%(title).200B [%(id)s].%(ext)s"))
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        *_site_args(url),
        "--windows-filenames",
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs",
        "all",
        "--sub-format",
        "srt/best",
        "-o",
        output_template,
        url,
    ]
    try:
        run_command(command, "yt-dlp.log", DOWNLOAD_FAILURE)
    except CommandError:
        raise
    after = _snapshot(SUBTITLES_DIR)
    new_files = sorted(after - before)
    return [path for path in new_files if path.suffix.lower() in {".srt", ".vtt", ".ass", ".ssa", ".json"}]


def download_audio(url: str) -> Path:
    ensure_dirs()
    before = _snapshot(AUDIO_DIR)
    output_template = str(safe_output_path(AUDIO_DIR / "%(title).200B [%(id)s].%(ext)s"))
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        *_site_args(url),
        "--windows-filenames",
        "-x",
        "--audio-format",
        "wav",
        "--postprocessor-args",
        "ffmpeg:-ar 16000 -ac 1",
        "-o",
        output_template,
        url,
    ]
    if FFMPEG_EXE.exists():
        command[3:3] = ["--ffmpeg-location", str(FFMPEG_BIN_DIR)]
    run_command(command, "yt-dlp.log", DOWNLOAD_FAILURE)
    after = _snapshot(AUDIO_DIR)
    wavs = sorted(path for path in after - before if path.suffix.lower() == ".wav")
    if wavs:
        return wavs[-1]
    all_wavs = sorted(AUDIO_DIR.glob("*.wav"), key=lambda path: path.stat().st_mtime)
    if all_wavs:
        return all_wavs[-1]
    raise RuntimeError(f"yt-dlp completed, but no wav output was found in {AUDIO_DIR}.")


def _cookie_file_for_url(url: str) -> Path | None:
    host = (urlparse(url).hostname or "").lower()
    if host.endswith("bilibili.com") or host.endswith("b23.tv"):
        return BILIBILI_COOKIE_FILE
    if host.endswith("youtube.com") or host.endswith("youtu.be") or host.endswith("youtube-nocookie.com"):
        return YOUTUBE_COOKIE_FILE
    return None


def _site_args(url: str) -> list[str]:
    args = _cookie_args(url)
    host = (urlparse(url).hostname or "").lower()
    if _is_youtube_host(host) and DENO_EXE.exists():
        args.extend(["--js-runtimes", f"deno:{DENO_EXE}"])
        args.extend(["--remote-components", "ejs:github"])
    return args


def _is_youtube_host(host: str) -> bool:
    return host.endswith("youtube.com") or host.endswith("youtu.be") or host.endswith("youtube-nocookie.com")


def _snapshot(directory: Path) -> set[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    return {path.resolve(strict=False) for path in directory.glob("**/*") if path.is_file()}
