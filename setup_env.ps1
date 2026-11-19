# Tao moi truong cho D tren Windows (PowerShell). Chay 1 lan:
#   .\setup_env.ps1
# Neu bi chan script: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "[1/4] Kiem tra Python..."
python --version
if ($LASTEXITCODE -ne 0) { Write-Error "Chua cai Python 3.10+ (tick 'Add Python to PATH' khi cai)"; exit 1 }

if (-not (Test-Path ".venv")) {
    Write-Host "[2/4] Tao moi truong ao .venv..."
    python -m venv .venv
} else {
    Write-Host "[2/4] Da co .venv, dung lai."
}

Write-Host "[3/4] Cai thu vien (1-3 phut)..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "[4/4] Chay kiem tra nhiem vu 1.6..."
& .\.venv\Scripts\python.exe scripts\check_task.py

Write-Host ""
Write-Host "XONG. Lan sau chi can:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  .\run_app.ps1      (mo giao dien)"
Write-Host "  .\run_tests.ps1    (chay test)"
