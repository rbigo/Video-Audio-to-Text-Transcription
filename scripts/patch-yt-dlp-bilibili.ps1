$ErrorActionPreference = "Stop"

$Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$Extractor = "$Root\.venv\Lib\site-packages\yt_dlp\extractor\bilibili.py"

if (-not (Test-Path -LiteralPath $Extractor)) {
    Write-Host "yt-dlp Bilibili extractor was not found; run bootstrap first." -ForegroundColor Yellow
    exit 0
}

$Text = Get-Content -LiteralPath $Extractor -Raw
$Old = @'
        return self._download_json(
            'https://api.bilibili.com/x/player/wbi/playurl', bvid,
            query=self._sign_wbi(params, bvid), headers=headers, note=note)['data']
'@
$New = @'
        return self._download_json(
            'https://api.bilibili.com/x/player/playurl', bvid,
            query=params, headers=headers, note=note)['data']
'@

if ($Text.Contains($New)) {
    Write-Host "yt-dlp Bilibili 412 patch is already applied." -ForegroundColor Green
    exit 0
}

if (-not $Text.Contains($Old)) {
    Write-Host "yt-dlp Bilibili extractor layout did not match the known patch target." -ForegroundColor Yellow
    exit 0
}

$Text.Replace($Old, $New) | Set-Content -LiteralPath $Extractor -Encoding UTF8NoBOM
Write-Host "Applied yt-dlp Bilibili 412 patch." -ForegroundColor Green
