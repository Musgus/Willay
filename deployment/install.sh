#!/bin/bash

# Script de instalación completa para Willay en Ubuntu Server
# Uso: sudo ./install.sh

set -e

echo "============================================="
echo "   Instalador de Willay - Ubuntu Server"
echo "============================================="
echo ""

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    echo "Error: Este script debe ejecutarse con sudo"
    echo "Uso: sudo ./install.sh"
    exit 1
fi

INSTALL_USER="${SUDO_USER:-$USER}"
INSTALL_DIR="/opt/willay"
SERVICE_FILE="/etc/systemd/system/willay-backend.service"

echo "1. Instalando dependencias del sistema..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx

echo ""
echo "2. Verificando instalación de Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "Ollama no está instalado. Instalando..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "Ollama instalado."
else
    echo "Ollama ya está instalado."
fi

# Iniciar servicio de Ollama
systemctl enable ollama
systemctl start ollama

echo ""
echo "3. Descargando modelo llama3.2 (esto puede tardar)..."
su - $INSTALL_USER -c "ollama pull llama3.2"

echo ""
echo "4. Descargando modelo de embeddings nomic-embed-text..."
su - $INSTALL_USER -c "ollama pull nomic-embed-text"

echo ""
echo "5. Copiando archivos a $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copiar archivos del proyecto
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
chown -R $INSTALL_USER:$INSTALL_USER "$INSTALL_DIR"

echo ""
echo "6. Creando entorno virtual de Python..."
cd "$INSTALL_DIR/backend"
su - $INSTALL_USER -c "cd $INSTALL_DIR/backend && python3 -m venv venv"

echo ""
echo "7. Instalando dependencias de Python..."
su - $INSTALL_USER -c "cd $INSTALL_DIR/backend && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

echo ""
echo "8. Creando directorios para RAG..."
mkdir -p "$INSTALL_DIR/backend/rag"
mkdir -p "$INSTALL_DIR/backend/rag_engine/vector_store"
mkdir -p "$INSTALL_DIR/backend/rag_engine/cache"
chown -R $INSTALL_USER:$INSTALL_USER "$INSTALL_DIR/backend/rag"
chown -R $INSTALL_USER:$INSTALL_USER "$INSTALL_DIR/backend/rag_engine"

echo ""
echo "9. Configurando servicio systemd..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Willay Backend - Chatbot Académico
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=$INSTALL_USER
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/backend/venv/bin"
ExecStart=$INSTALL_DIR/backend/venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "10. Configurando Nginx..."
cat > /etc/nginx/sites-available/willay << 'EOF'
server {
    listen 80;
    server_name _;

    # Servir frontend
    location / {
        root /opt/willay;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Proxy para API backend
    location /chat/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }

    location /rag/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF

# Habilitar sitio
ln -sf /etc/nginx/sites-available/willay /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Verificar configuración
nginx -t

echo ""
echo "11. Habilitando e iniciando servicios..."
systemctl daemon-reload
systemctl enable willay-backend
systemctl start willay-backend
systemctl restart nginx

echo ""
echo "============================================="
echo "   ✓ Instalación completada"
echo "============================================="
echo ""
echo "El chatbot Willay está corriendo en:"
echo "  - Frontend: http://$(hostname -I | awk '{print $1}')"
echo "  - Backend API: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "Comandos útiles:"
echo "  - Ver logs: sudo journalctl -u willay-backend -f"
echo "  - Reiniciar: sudo systemctl restart willay-backend"
echo "  - Estado: sudo systemctl status willay-backend"
echo "  - CLI RAG: cd $INSTALL_DIR/backend && python rag_cli.py --help"
echo ""
echo "Archivos de configuración:"
echo "  - Servicio: $SERVICE_FILE"
echo "  - Nginx: /etc/nginx/sites-available/willay"
echo "  - Aplicación: $INSTALL_DIR"
echo ""
