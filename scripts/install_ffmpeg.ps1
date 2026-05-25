$ErrorActionPreference = "Stop"

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpeg) {
    Write-Host "ffmpeg is already installed at $($ffmpeg.Source)"
    exit 0
}

$winget = Get-Command winget -ErrorAction SilentlyContinue
if (-not $winget) {
    Write-Host "winget is not available. Install ffmpeg manually or via chocolatey/scoop."
    exit 1
}

Write-Host "Installing ffmpeg via winget..."
winget install --id Gyan.FFmpeg

$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if (-not $ffmpeg) {
    Write-Host "ffmpeg install finished but not found in PATH. Restart your terminal."
    exit 1
}

Write-Host "ffmpeg is installed at $($ffmpeg.Source)"
