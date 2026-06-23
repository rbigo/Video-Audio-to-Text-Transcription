param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\env.ps1"

$Python = "$env:BILI_WHISPER_HOME\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    Write-Host "Virtualenv Python was not found. Run .\scripts\bootstrap.ps1 first." -ForegroundColor Red
    exit 1
}

& $Python -m bili_whisper @Args
exit $LASTEXITCODE
