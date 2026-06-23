param(
    [switch]$WithFunASR
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\env.ps1"
$Root = $env:BILI_WHISPER_HOME

$Uv = "$Root\runtime\bin\uv.exe"
$Ffmpeg = "$Root\runtime\ffmpeg\bin\ffmpeg.exe"
$Ffprobe = "$Root\runtime\ffmpeg\bin\ffprobe.exe"
$Venv = "$Root\.venv"
$Project = "$Root\app"

if (-not (Test-Path -LiteralPath $Uv)) {
    Write-Host "Please download uv.exe manually and place it at $Root\runtime\bin\uv.exe" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path -LiteralPath $Ffmpeg) -or -not (Test-Path -LiteralPath $Ffprobe)) {
    Write-Host "Please extract ffmpeg.exe and ffprobe.exe to $Root\runtime\ffmpeg\bin" -ForegroundColor Yellow
}

if (-not (Test-Path -LiteralPath "$Venv\Scripts\python.exe")) {
    & $Uv venv "$Venv" --python ">=3.10,<3.13"
}

if ($WithFunASR) {
    & $Uv pip install --python "$Venv\Scripts\python.exe" -e "$Project[funasr]"
} else {
    & $Uv pip install --python "$Venv\Scripts\python.exe" -e "$Project"
}

& "$PSScriptRoot\patch-yt-dlp-bilibili.ps1"

Write-Host "Bootstrap finished." -ForegroundColor Green
Write-Host "Run .\scripts\doctor.ps1 to verify the environment."
