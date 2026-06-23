$ErrorActionPreference = "Continue"
. "$PSScriptRoot\env.ps1"

$Root = $env:BILI_WHISPER_HOME
$Python = "$Root\.venv\Scripts\python.exe"
$Ffmpeg = "$Root\runtime\ffmpeg\bin\ffmpeg.exe"
$Ffprobe = "$Root\runtime\ffmpeg\bin\ffprobe.exe"
$Warnings = New-Object System.Collections.Generic.List[string]
$Errors = New-Object System.Collections.Generic.List[string]

function Write-Item {
    param([string]$Name, [string]$Value, [string]$Status = "INFO")
    $color = "Gray"
    if ($Status -eq "OK") { $color = "Green" }
    if ($Status -eq "WARNING") { $color = "Yellow" }
    if ($Status -eq "ERROR") { $color = "Red" }
    Write-Host ("{0,-28} {1}" -f $Name, $Value) -ForegroundColor $color
}

function Test-PathRisk {
    param([string]$Label, [string]$Value, [switch]$AllowSystemNvidia)
    if ([string]::IsNullOrWhiteSpace($Value)) { return }
    $risk = $false
    foreach ($needle in @('C:\', '%USERPROFILE%', 'AppData')) {
        if ($Value -like "*$needle*") { $risk = $true }
    }
    if ($AllowSystemNvidia -and $Value -like "*nvidia-smi.exe") { $risk = $false }
    if ($risk) {
        $Warnings.Add("$Label contains a risky C drive or user profile path: $Value")
    }
}

Write-Host "Bili Whisper Doctor" -ForegroundColor Cyan
Write-Item "Project root" $Root "OK"

$PythonStatus = if (Test-Path -LiteralPath $Python) { "OK" } else { "ERROR" }
Write-Item "Python path" $Python $PythonStatus
if (-not (Test-Path -LiteralPath $Python)) {
    $Errors.Add("Virtualenv Python is missing. Run .\scripts\bootstrap.ps1")
}
if (Test-Path -LiteralPath $Python) {
    $ResolvedPython = (Resolve-Path -LiteralPath $Python).Path
    $ResolvedVenv = (Resolve-Path -LiteralPath "$Root\.venv").Path
    if (-not $ResolvedPython.StartsWith($ResolvedVenv)) {
        $Errors.Add("Python is not under $Root\.venv")
    }
}

$envItems = [ordered]@{
    "pip cache" = $env:PIP_CACHE_DIR
    "uv cache" = $env:UV_CACHE_DIR
    "HF_HOME" = $env:HF_HOME
    "HF_HUB_CACHE" = $env:HF_HUB_CACHE
    "MODELSCOPE_CACHE" = $env:MODELSCOPE_CACHE
    "TORCH_HOME" = $env:TORCH_HOME
    "TEMP" = $env:TEMP
    "TMP" = $env:TMP
    "models dir" = "$Root\models"
}

foreach ($item in $envItems.GetEnumerator()) {
    $status = if ($item.Value -like "$Root*") { "OK" } else { "WARNING" }
    Write-Item $item.Key $item.Value $status
    Test-PathRisk $item.Key $item.Value
}

$FfmpegStatus = if (Test-Path -LiteralPath $Ffmpeg) { "OK" } else { "ERROR" }
$FfprobeStatus = if (Test-Path -LiteralPath $Ffprobe) { "OK" } else { "ERROR" }
Write-Item "ffmpeg path" $Ffmpeg $FfmpegStatus
Write-Item "ffprobe path" $Ffprobe $FfprobeStatus
if (-not (Test-Path -LiteralPath $Ffmpeg)) {
    $Errors.Add("ffmpeg.exe not found. Place it under $Root\runtime\ffmpeg\bin")
}
if (-not (Test-Path -LiteralPath $Ffprobe)) {
    $Errors.Add("ffprobe.exe not found. Place it under $Root\runtime\ffmpeg\bin")
}

if (Test-Path -LiteralPath $Python) {
    & $Python -m bili_whisper doctor
    if ($LASTEXITCODE -ne 0) { $Warnings.Add("Python doctor returned a non-zero status.") }
} else {
    Write-Item "yt-dlp available" "not checked: Python missing" "ERROR"
    Write-Item "faster-whisper import" "not checked: Python missing" "ERROR"
    Write-Item "FunASR import" "not checked: Python missing" "WARNING"
    Write-Item "torch import" "not checked: Python missing" "WARNING"
}

$NvidiaSmi = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
if ($NvidiaSmi) {
    Write-Item "nvidia-smi available" $NvidiaSmi.Source "OK"
    Test-PathRisk "nvidia-smi" $NvidiaSmi.Source -AllowSystemNvidia
    $gpu = & $NvidiaSmi.Source --query-gpu=name,memory.total --format=csv,noheader 2>$null
    if ($gpu) { Write-Item "GPU name/memory" ($gpu -join "; ") "OK" }
} else {
    Write-Item "nvidia-smi available" "no" "WARNING"
    $Warnings.Add("nvidia-smi is not available.")
}

foreach ($warning in $Warnings) {
    Write-Host "WARNING: $warning" -ForegroundColor Yellow
}
foreach ($errorItem in $Errors) {
    Write-Host "ERROR: $errorItem" -ForegroundColor Red
}

if ($Errors.Count -gt 0) {
    Write-Host "ERROR: Missing required components" -ForegroundColor Red
    exit 2
}
if ($Warnings.Count -gt 0) {
    Write-Host "WARNING: Runnable, but path or environment risks were found" -ForegroundColor Yellow
    exit 1
}
Write-Host "OK: Ready to run" -ForegroundColor Green
