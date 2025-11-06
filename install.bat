@echo off
REM Script de instalación completa de Willay con RAG
echo ================================================
echo   WILLAY - Instalacion Completa con RAG
echo ================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en PATH
    echo Descarga Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python detectado
echo.

REM Verificar Ollama
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama no esta corriendo
    echo.
    echo Pasos para solucionar:
    echo 1. Descarga Ollama: https://ollama.com/download/windows
    echo 2. Instala Ollama
    echo 3. Ollama se iniciara automaticamente
    echo 4. Ejecuta este script de nuevo
    pause
    exit /b 1
)

echo [OK] Ollama corriendo
echo.

REM Cambiar al directorio backend
cd backend

REM Crear entorno virtual
if not exist .venv (
    echo [*] Creando entorno virtual...
    python -m venv .venv
    echo [OK] Entorno virtual creado
) else (
    echo [OK] Entorno virtual ya existe
)
echo.

REM Activar entorno virtual
call .venv\Scripts\activate.bat

REM Instalar dependencias
echo [*] Instalando dependencias (esto puede tardar)...
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias
    pause
    exit /b 1
)

echo [OK] Dependencias instaladas
echo.

REM Verificar modelos de Ollama
echo [*] Verificando modelos de Ollama...

ollama list | findstr llama3.2 >nul 2>&1
if errorlevel 1 (
    echo [*] Descargando modelo llama3.2 (esto tardara varios minutos)...
    ollama pull llama3.2
    echo [OK] Modelo llama3.2 instalado
) else (
    echo [OK] Modelo llama3.2 ya instalado
)
echo.

ollama list | findstr nomic-embed-text >nul 2>&1
if errorlevel 1 (
    echo [*] Descargando modelo nomic-embed-text para RAG...
    ollama pull nomic-embed-text
    echo [OK] Modelo nomic-embed-text instalado
) else (
    echo [OK] Modelo nomic-embed-text ya instalado
)
echo.

REM Crear directorios necesarios
if not exist ..\rag mkdir ..\rag
if not exist rag_engine\cache mkdir rag_engine\cache
if not exist rag_engine\vector_store mkdir rag_engine\vector_store

echo [OK] Directorios RAG creados
echo.

REM Verificar si hay PDFs para indexar
cd ..
set PDF_COUNT=0
for %%f in (rag\*.pdf) do set /a PDF_COUNT+=1

if %PDF_COUNT% gtr 0 (
    echo [*] Se encontraron %PDF_COUNT% archivos PDF
    echo.
    choice /C SN /M "Deseas indexarlos ahora (S/N)"
    if errorlevel 2 goto skip_indexing
    if errorlevel 1 goto do_indexing
    
    :do_indexing
    echo [*] Indexando documentos...
    cd backend
    python rag_cli.py index
    cd ..
    echo.
    goto after_indexing
    
    :skip_indexing
    echo [*] Puedes indexar mas tarde con: python backend\rag_cli.py index
    echo.
    
    :after_indexing
) else (
    echo [*] No se encontraron PDFs en la carpeta rag\
    echo    Puedes agregar PDFs y luego ejecutar: python backend\rag_cli.py index
    echo.
)

echo ================================================
echo   INSTALACION COMPLETADA
echo ================================================
echo.
echo Proximos pasos:
echo.
echo 1. Iniciar el backend:
echo    cd backend
echo    run.bat
echo.
echo 2. Abrir index.html en tu navegador
echo.
echo 3. (Opcional) Para usar RAG:
echo    - Coloca PDFs en la carpeta 'rag\'
echo    - Ejecuta: python backend\rag_cli.py index
echo    - Activa el toggle "Usar RAG" en el chat
echo.
echo ================================================
echo.
pause
