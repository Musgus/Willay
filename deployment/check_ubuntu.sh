#!/bin/bash

# Script de verificación rápida para Ubuntu
# Verifica que todos los componentes estén funcionando

echo "========================================="
echo "  Verificación de Willay - Ubuntu"
echo "========================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1"
        return 1
    fi
}

echo "1. Verificando Python..."
python3 --version > /dev/null 2>&1
check "Python 3 instalado"

echo ""
echo "2. Verificando Ollama..."
curl -s http://localhost:11434/api/tags > /dev/null 2>&1
check "Ollama corriendo en puerto 11434"

echo ""
echo "3. Verificando modelos de Ollama..."
if command -v ollama &> /dev/null; then
    if ollama list | grep -q "llama3.2"; then
        echo -e "${GREEN}✓${NC} Modelo llama3.2 instalado"
    else
        echo -e "${YELLOW}⚠${NC} Modelo llama3.2 no encontrado (ejecuta: ollama pull llama3.2)"
    fi
    
    if ollama list | grep -q "nomic-embed-text"; then
        echo -e "${GREEN}✓${NC} Modelo nomic-embed-text instalado"
    else
        echo -e "${YELLOW}⚠${NC} Modelo nomic-embed-text no encontrado (para RAG)"
    fi
else
    echo -e "${RED}✗${NC} Comando ollama no disponible"
fi

echo ""
echo "4. Verificando Backend de Willay..."
curl -s http://localhost:8000/health > /dev/null 2>&1
check "Backend corriendo en puerto 8000"

echo ""
echo "5. Verificando Nginx..."
systemctl is-active --quiet nginx
check "Nginx activo"

echo ""
echo "6. Verificando servicio willay-backend..."
if systemctl list-units --type=service | grep -q willay-backend; then
    systemctl is-active --quiet willay-backend
    check "Servicio willay-backend activo"
else
    echo -e "${YELLOW}⚠${NC} Servicio willay-backend no instalado"
fi

echo ""
echo "7. Verificando archivos del proyecto..."
if [ -f "/opt/willay/index.html" ]; then
    echo -e "${GREEN}✓${NC} Frontend instalado en /opt/willay"
else
    echo -e "${YELLOW}⚠${NC} Frontend no encontrado en /opt/willay"
fi

if [ -f "/opt/willay/backend/app.py" ]; then
    echo -e "${GREEN}✓${NC} Backend instalado en /opt/willay/backend"
else
    echo -e "${YELLOW}⚠${NC} Backend no encontrado en /opt/willay/backend"
fi

echo ""
echo "8. Verificando dependencias de Python..."
if [ -d "/opt/willay/backend/venv" ]; then
    source /opt/willay/backend/venv/bin/activate
    python -c "import fastapi, uvicorn, httpx, pydantic" 2>/dev/null
    check "Dependencias básicas instaladas"
    
    python -c "import chromadb, pypdf2" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Dependencias RAG instaladas"
    else
        echo -e "${YELLOW}⚠${NC} Dependencias RAG no instaladas"
    fi
    deactivate
else
    echo -e "${YELLOW}⚠${NC} Entorno virtual no encontrado"
fi

echo ""
echo "========================================="
echo "  Resumen"
echo "========================================="
echo ""

# Test completo
ALL_OK=true

curl -s http://localhost:11434/api/tags > /dev/null 2>&1 || ALL_OK=false
curl -s http://localhost:8000/health > /dev/null 2>&1 || ALL_OK=false
systemctl is-active --quiet nginx || ALL_OK=false

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}✓ Todos los componentes principales están funcionando${NC}"
    echo ""
    echo "Puedes acceder a Willay en:"
    echo "  - Frontend: http://$(hostname -I | awk '{print $1}')"
    echo "  - API: http://$(hostname -I | awk '{print $1}'):8000"
    echo ""
    echo "Comandos útiles:"
    echo "  - Ver logs: sudo journalctl -u willay-backend -f"
    echo "  - Reiniciar: sudo systemctl restart willay-backend"
    echo "  - Estado: sudo systemctl status willay-backend"
else
    echo -e "${YELLOW}⚠ Algunos componentes no están funcionando correctamente${NC}"
    echo ""
    echo "Revisa los errores arriba y consulta:"
    echo "  - Logs del backend: sudo journalctl -u willay-backend -n 50"
    echo "  - Logs de Nginx: sudo tail -f /var/log/nginx/error.log"
    echo "  - UBUNTU_DEPLOYMENT.md - Sección de troubleshooting"
fi

echo ""
