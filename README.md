# Video-Audio-to-Text-Transcription

Windows local transcription tool for Bilibili, YouTube, local video, and local audio.

[中文介绍](README.zh-CN.md)

This repository contains source code and deployment scripts only. It intentionally does not commit local virtual environments, ffmpeg, uv, downloaded models, caches, cookies, media files, transcripts, or logs. The bootstrap script downloads the missing runtime tools and can prefetch the default ASR model into the project-local cache.

## Features

- Bilibili and YouTube URL transcription through `yt-dlp`
- Local video and audio transcription
- Local downloaded video to WAV audio extraction without transcription
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

## Bootstrap

Recommended first run after cloning:

```powershell
.\scripts\bootstrap.ps1 -WithDeno -PreloadModels
.\scripts\doctor.ps1
```

This automatically downloads missing runtime tools into the repository:

```text
runtime\bin\uv.exe
runtime\bin\deno.exe
runtime\ffmpeg\bin\ffmpeg.exe
runtime\ffmpeg\bin\ffprobe.exe
```

It also preloads the default `faster-whisper` model. If you also want FunASR dependencies and the SenseVoiceSmall model:

```powershell
.\scripts\bootstrap.ps1 -WithFunASR -WithDeno -PreloadModels
```

If automatic runtime downloads are unavailable on your network, place the files manually in the paths above and run:

```powershell
.\scripts\bootstrap.ps1 -NoDownloadTools
.\scripts\doctor.ps1
```

You can also preload models later without reinstalling dependencies:

```powershell
.\scripts\run.ps1 preload-models --engine faster-whisper
.\scripts\run.ps1 preload-models --engine all
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

Extract audio from a URL or a local downloaded video without transcription:

```powershell
.\scripts\run.ps1 extract-audio "https://www.bilibili.com/video/BVxxxx"
.\scripts\run.ps1 extract-audio "D:\path\to\downloaded-video.mp4"
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
