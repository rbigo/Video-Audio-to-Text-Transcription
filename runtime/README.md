# Runtime binaries

This directory is intentionally source-only in Git.

`scripts\bootstrap.ps1` downloads missing runtime tools here automatically. If that fails on your network, place local tools here manually:

```text
runtime\bin\uv.exe
runtime\bin\deno.exe
runtime\ffmpeg\bin\ffmpeg.exe
runtime\ffmpeg\bin\ffprobe.exe
```

`deno.exe` is optional and is only used by yt-dlp for some YouTube JavaScript challenge flows.
