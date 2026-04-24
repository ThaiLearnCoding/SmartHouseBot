param(
    [int]$Port = 8000,
    [string]$Host = "0.0.0.0"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

Set-Location $rootDir

if (-not (Test-Path ".env")) {
    Write-Error "Missing .env file. Copy .env.example to .env and fill values first."
    exit 1
}

& "$rootDir\scripts\load_env.ps1" -EnvFile ".env"

uvicorn web_voice_server:app --host $Host --port $Port --reload
