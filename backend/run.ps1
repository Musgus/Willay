# Crear y activar entorno, instalar dependencias y lanzar FastAPI con uvicorn.
# Si Windows Firewall solicita permiso, acepta para permitir conexiones locales.
$ErrorActionPreference = "Stop"
$venvPath = Join-Path $PSScriptRoot ".venv"

if (-not (Test-Path $venvPath)) {
    Write-Host "Creando entorno virtual..."
    python -m venv $venvPath
}

$activateScript = Join-Path $venvPath "Scripts/Activate.ps1"
. $activateScript

pip install --upgrade pip
pip install -r (Join-Path $PSScriptRoot "requirements.txt")

Push-Location $PSScriptRoot
try {
    uvicorn app:app --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
