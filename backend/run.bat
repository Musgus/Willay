@echo off
REM Crea el entorno virtual, instala dependencias y arranca uvicorn.
REM Si Windows Firewall muestra un aviso, permite el acceso para uso local.
setlocal
set "VENV_DIR=%~dp0.venv"

if not exist "%VENV_DIR%" (
    echo Creando entorno virtual...
    python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"

pip install --upgrade pip
pip install -r "%~dp0requirements.txt"

pushd "%~dp0"
uvicorn app:app --host 127.0.0.1 --port 8000
popd

endlocal
