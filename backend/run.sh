#!/bin/bash

# Script para ejecutar el backend de Willay en Ubuntu/Linux
# Uso: ./run.sh

echo "================================="
echo "   Willay Backend (Ubuntu)"
echo "================================="
echo ""

# Detectar directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: No se pudo crear el entorno virtual"
        echo "Instala python3-venv: sudo apt install python3-venv"
        exit 1
    fi
    echo "Entorno virtual creado."
    echo ""
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "Actualizando pip..."
pip install --upgrade pip > /dev/null 2>&1

# Instalar dependencias
echo "Instalando dependencias..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "Error: No se pudieron instalar las dependencias"
    exit 1
fi

echo ""
echo "================================="
echo "   Backend iniciado"
echo "================================="
echo ""
echo "Servidor corriendo en: http://127.0.0.1:8000"
echo "Presiona Ctrl+C para detener"
echo ""

# Ejecutar servidor
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
