$Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path

$env:BILI_WHISPER_HOME = $Root

$env:HF_HOME = "$Root\cache\huggingface"
$env:HF_HUB_CACHE = "$Root\cache\huggingface\hub"
$env:HUGGINGFACE_HUB_CACHE = "$Root\cache\huggingface\hub"
$env:TRANSFORMERS_CACHE = "$Root\cache\huggingface\transformers"

$env:MODELSCOPE_CACHE = "$Root\cache\modelscope"
$env:MODELSCOPE_HOME = "$Root\cache\modelscope"

$env:XDG_CACHE_HOME = "$Root\cache\xdg"
$env:PIP_CACHE_DIR = "$Root\cache\pip"
$env:UV_CACHE_DIR = "$Root\cache\uv"
$env:UV_PYTHON_INSTALL_DIR = "$Root\runtime\python"
$env:UV_TOOL_DIR = "$Root\runtime\uv-tools"
$env:UV_TOOL_BIN_DIR = "$Root\runtime\bin"

$env:TORCH_HOME = "$Root\cache\torch"

$env:TEMP = "$Root\cache\temp"
$env:TMP = "$Root\cache\temp"

$pathParts = @(
    "$Root\runtime\ffmpeg\bin",
    "$Root\.venv\Scripts",
    "$Root\.venv\Lib\site-packages\nvidia\cublas\bin",
    "$Root\.venv\Lib\site-packages\nvidia\cuda_nvrtc\bin",
    "$Root\.venv\Lib\site-packages\nvidia\cudnn\bin",
    "$Root\runtime\bin"
)
$env:PATH = ($pathParts -join ";") + ";$env:PATH"

$Directories = @(
    "$Root\app\src\bili_whisper",
    "$Root\scripts",
    "$Root\runtime\bin",
    "$Root\runtime\python",
    "$Root\runtime\ffmpeg\bin",
    "$Root\.venv",
    "$Root\cache\pip",
    "$Root\cache\uv",
    "$Root\cache\xdg",
    "$Root\cache\torch",
    "$Root\cache\huggingface",
    "$Root\cache\huggingface\hub",
    "$Root\cache\huggingface\transformers",
    "$Root\cache\modelscope",
    "$Root\cache\temp",
    "$Root\models\faster-whisper",
    "$Root\models\funasr",
    "$Root\data\cookies",
    "$Root\data\downloads",
    "$Root\data\audio",
    "$Root\data\subtitles",
    "$Root\data\transcripts",
    "$Root\data\jobs",
    "$Root\data\logs",
    "$Root\data\temp"
)

foreach ($Directory in $Directories) {
    if (-not (Test-Path -LiteralPath $Directory)) {
        New-Item -ItemType Directory -Force -Path $Directory | Out-Null
    }
}

$CookieFile = "$Root\data\cookies\bilibili.txt"
if (-not (Test-Path -LiteralPath $CookieFile)) {
    New-Item -ItemType File -Force -Path $CookieFile | Out-Null
}

$YouTubeCookieFile = "$Root\data\cookies\youtube.txt"
if (-not (Test-Path -LiteralPath $YouTubeCookieFile)) {
    New-Item -ItemType File -Force -Path $YouTubeCookieFile | Out-Null
}
