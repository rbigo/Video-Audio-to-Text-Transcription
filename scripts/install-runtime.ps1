param(
    [switch]$WithDeno
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\env.ps1"

$Root = $env:BILI_WHISPER_HOME
$DownloadDir = "$Root\cache\downloads"
$Uv = "$Root\runtime\bin\uv.exe"
$Deno = "$Root\runtime\bin\deno.exe"
$Ffmpeg = "$Root\runtime\ffmpeg\bin\ffmpeg.exe"
$Ffprobe = "$Root\runtime\ffmpeg\bin\ffprobe.exe"

New-Item -ItemType Directory -Force -Path $DownloadDir | Out-Null

function Invoke-FileDownload {
    param(
        [string]$Url,
        [string]$OutFile
    )
    Write-Host "Downloading $Url" -ForegroundColor Cyan
    Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing
}

function Get-GitHubAssetUrl {
    param(
        [string]$Repo,
        [string]$NamePattern
    )
    $release = Invoke-RestMethod `
        -Uri "https://api.github.com/repos/$Repo/releases/latest" `
        -Headers @{ "User-Agent" = "bili-whisper-bootstrap" }
    $asset = $release.assets | Where-Object { $_.name -like $NamePattern } | Select-Object -First 1
    if (-not $asset) {
        throw "No GitHub release asset matching '$NamePattern' found for $Repo."
    }
    return $asset.browser_download_url
}

function Expand-ZipToTemp {
    param([string]$ZipFile)
    $TempExtract = Join-Path $DownloadDir ([IO.Path]::GetFileNameWithoutExtension($ZipFile))
    if (Test-Path -LiteralPath $TempExtract) {
        Remove-Item -LiteralPath $TempExtract -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $TempExtract | Out-Null
    Expand-Archive -LiteralPath $ZipFile -DestinationPath $TempExtract -Force
    return $TempExtract
}

function Install-ToolFromZip {
    param(
        [string]$Url,
        [string]$ZipName,
        [string[]]$ExeNames,
        [string]$Destination
    )
    $ZipFile = Join-Path $DownloadDir $ZipName
    Invoke-FileDownload -Url $Url -OutFile $ZipFile
    $TempExtract = Expand-ZipToTemp -ZipFile $ZipFile
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    foreach ($ExeName in $ExeNames) {
        $Exe = Get-ChildItem -LiteralPath $TempExtract -Recurse -File -Filter $ExeName | Select-Object -First 1
        if (-not $Exe) {
            throw "$ExeName was not found inside $ZipName."
        }
        Copy-Item -LiteralPath $Exe.FullName -Destination (Join-Path $Destination $ExeName) -Force
    }
}

if (-not (Test-Path -LiteralPath $Uv)) {
    $Url = Get-GitHubAssetUrl -Repo "astral-sh/uv" -NamePattern "uv-x86_64-pc-windows-msvc.zip"
    Install-ToolFromZip -Url $Url -ZipName "uv-x86_64-pc-windows-msvc.zip" -ExeNames @("uv.exe") -Destination "$Root\runtime\bin"
} else {
    Write-Host "uv.exe already exists." -ForegroundColor Green
}

if (-not (Test-Path -LiteralPath $Ffmpeg) -or -not (Test-Path -LiteralPath $Ffprobe)) {
    Install-ToolFromZip `
        -Url "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" `
        -ZipName "ffmpeg-release-essentials.zip" `
        -ExeNames @("ffmpeg.exe", "ffprobe.exe") `
        -Destination "$Root\runtime\ffmpeg\bin"
} else {
    Write-Host "ffmpeg.exe and ffprobe.exe already exist." -ForegroundColor Green
}

if ($WithDeno) {
    if (-not (Test-Path -LiteralPath $Deno)) {
        $Url = Get-GitHubAssetUrl -Repo "denoland/deno" -NamePattern "deno-x86_64-pc-windows-msvc.zip"
        Install-ToolFromZip -Url $Url -ZipName "deno-x86_64-pc-windows-msvc.zip" -ExeNames @("deno.exe") -Destination "$Root\runtime\bin"
    } else {
        Write-Host "deno.exe already exists." -ForegroundColor Green
    }
}

Write-Host "Runtime tools are ready under $Root\runtime." -ForegroundColor Green
