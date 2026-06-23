$ErrorActionPreference = "Stop"
. "$PSScriptRoot\env.ps1"

$Root = $env:BILI_WHISPER_HOME
$Targets = @(
    "$Root\cache\pip",
    "$Root\cache\uv",
    "$Root\cache\xdg",
    "$Root\cache\torch",
    "$Root\cache\huggingface",
    "$Root\cache\modelscope",
    "$Root\cache\temp",
    "$Root\data\temp"
)

foreach ($Target in $Targets) {
    $ResolvedRoot = (Resolve-Path -LiteralPath $Root).Path
    if (Test-Path -LiteralPath $Target) {
        $ResolvedTarget = (Resolve-Path -LiteralPath $Target).Path
        if (-not $ResolvedTarget.StartsWith($ResolvedRoot)) {
            throw "Refusing to clean path outside project root: $ResolvedTarget"
        }
        Remove-Item -LiteralPath $ResolvedTarget -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $Target | Out-Null
}

Write-Host "Cache cleaned under $Root only." -ForegroundColor Green
