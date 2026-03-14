# na-analytics — self-bootstrapping wrapper for Windows PowerShell
# Clone the repo, run this file. That's it.

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Bootstrap on first run
if (-not (Test-Path "$ProjectDir\.venv")) {
    Write-Host "na-analytics: first run — installing dependencies..." -ForegroundColor Cyan

    # Check Python
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command python3 -ErrorAction SilentlyContinue
    }
    if (-not $python) {
        Write-Host "ERROR: Python 3.10+ required." -ForegroundColor Red
        Write-Host "  Install: winget install Python.Python.3.12"
        Write-Host "  Or download from https://python.org"
        exit 1
    }
    $pyCmd = $python.Name

    # Check/install uv
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        Write-Host "  Installing uv (Python package manager)..."
        irm https://astral.sh/uv/install.ps1 | iex
        $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
    }
    Write-Host "  uv OK" -ForegroundColor Green

    # Create venv + install
    Push-Location $ProjectDir
    uv venv --python $pyCmd --quiet 2>$null
    uv pip install -e . --quiet 2>$null
    if ($LASTEXITCODE -ne 0) { uv pip install -e . }
    Pop-Location

    Write-Host "na-analytics: ready.`n" -ForegroundColor Green
}

# Run the CLI
Push-Location $ProjectDir
uv run na-analytics @args
Pop-Location
