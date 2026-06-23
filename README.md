# bili-whisper

Windows local transcription tool for Bilibili, YouTube, local video, and local audio.

This repository contains source code and deployment scripts only. It intentionally does not include local virtual environments, ffmpeg, uv, downloaded models, caches, cookies, media files, transcripts, or logs.

## Features

- Bilibili and YouTube URL transcription through `yt-dlp`
- Local video and audio transcription
- `faster-whisper` as the default ASR engine
- Optional `FunASR / SenseVoiceSmall` comparison engine
- `txt`, `srt`, and `json` output
- Tkinter local GUI
- Project-local cache, model, runtime, log, and output directories

## Clone

```powershell
git clone <YOUR_REPO_URL> bili-whisper
cd bili-whisper
```

The scripts now detect the repository root automatically. You can clone the project to any writable path, though a non-system drive is recommended because models and caches can be large.

## Required Local Tools

Download `uv.exe` and put it here:

```text
runtime\bin\uv.exe
```

Download or extract ffmpeg and put these files here:

```text
runtime\ffmpeg\bin\ffmpeg.exe
runtime\ffmpeg\bin\ffprobe.exe
```

For YouTube JS challenge solving, optional `deno.exe` can be placed here:

```text
runtime\bin\deno.exe
```

## Bootstrap

```powershell
.\scripts\bootstrap.ps1
.\scripts\doctor.ps1
```

Install the optional FunASR dependencies:

```powershell
.\scripts\bootstrap.ps1 -WithFunASR
```

## Run

Process a Bilibili or YouTube URL:

```powershell
.\scripts\run.ps1 all "https://www.bilibili.com/video/BVxxxx"
.\scripts\run.ps1 all "https://www.youtube.com/watch?v=xxxx"
```

Transcribe a local file:

```powershell
.\scripts\run.ps1 transcribe "D:\path\to\video-or-audio.mp4"
```

Compare faster-whisper and FunASR:

```powershell
.\scripts\run.ps1 compare "D:\path\to\audio.wav"
```

Open the GUI:

```powershell
.\scripts\gui.ps1
```

## Cookies

The project never reads browser cookies automatically. If a site requires login, export cookies manually in Netscape `cookies.txt` format and place them here:

```text
data\cookies\bilibili.txt
data\cookies\youtube.txt
```

Cookie files are ignored by Git.

## Output

Generated output stays under the local project directory:

```text
data\audio
data\subtitles
data\transcripts
data\logs
cache
models
```

These directories are ignored by Git because they are machine-local runtime state.

## Notes

- Do not commit cookies, downloaded media, transcripts, models, caches, `.venv`, or runtime binaries.
- Run `.\scripts\doctor.ps1` after bootstrap to check paths, ffmpeg, Python, yt-dlp, ASR imports, CUDA, and GPU status.
- More usage examples are in `app\README.md`.
