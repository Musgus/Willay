# Despliegue en Ubuntu Server

Esta guía explica cómo instalar y configurar Willay en un servidor Ubuntu.

## Requisitos Previos

- Ubuntu Server 20.04 o superior
- Acceso root o sudo
- Conexión a internet
- Al menos 8GB de RAM (para Ollama)
- 20GB de espacio en disco

## Instalación Automática

La forma más rápida es usar el script de instalación automática:

```bash
# Clonar o copiar el proyecto al servidor
cd /tmp
# (copiar archivos de Willay aquí)

# Dar permisos de ejecución
chmod +x install.sh

# Ejecutar instalador
sudo ./install.sh
```

El script automáticamente:
1. Instala dependencias del sistema (Python, Nginx)
2. Instala y configura Ollama
3. Descarga modelos de IA (llama3.2, nomic-embed-text)
4. Configura entorno virtual de Python
5. Instala dependencias de Python
6. Crea servicio systemd
7. Configura Nginx como reverse proxy
8. Inicia todos los servicios

Después de la instalación, accede a:
- **Frontend**: `http://TU_IP_SERVIDOR`
- **API**: `http://TU_IP_SERVIDOR:8000`

## Instalación Manual

### 1. Instalar Dependencias del Sistema

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx
```

### 2. Instalar Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable ollama
sudo systemctl start ollama
```

### 3. Descargar Modelos de IA

```bash
# Modelo principal (3.2GB)
ollama pull llama3.2

# Modelo de embeddings para RAG (274MB)
ollama pull nomic-embed-text
```

### 4. Configurar la Aplicación

```bash
# Crear directorio de instalación
sudo mkdir -p /opt/willay
sudo chown $USER:$USER /opt/willay

# Copiar archivos
cp -r backend/ index.html style.css script.js /opt/willay/

# Configurar backend
cd /opt/willay/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Crear directorios para RAG
mkdir -p rag rag_engine/vector_store rag_engine/cache
```

### 5. Configurar Servicio Systemd

```bash
# Copiar archivo de servicio
sudo cp /opt/willay/backend/willay-backend.service /etc/systemd/system/

# Editar el archivo si es necesario (cambiar usuario, rutas, etc.)
sudo nano /etc/systemd/system/willay-backend.service

# Habilitar e iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable willay-backend
sudo systemctl start willay-backend
```

### 6. Configurar Nginx

Crear archivo de configuración:

```bash
sudo nano /etc/nginx/sites-available/willay
```

Contenido:

```nginx
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
```

Habilitar sitio:

```bash
sudo ln -s /etc/nginx/sites-available/willay /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## Gestión del Servicio

### Ver logs en tiempo real
```bash
sudo journalctl -u willay-backend -f
```

### Estado del servicio
```bash
sudo systemctl status willay-backend
```

### Reiniciar servicio
```bash
sudo systemctl restart willay-backend
```

### Detener servicio
```bash
sudo systemctl stop willay-backend
```

### Ver logs de Nginx
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Configuración de RAG

### Usar CLI de RAG
```bash
cd /opt/willay/backend
source venv/bin/activate

# Ver ayuda
python rag_cli.py --help

# Indexar PDFs
python rag_cli.py index

# Ver estadísticas
python rag_cli.py stats

# Modo watch (auto-indexar al agregar PDFs)
python rag_cli.py watch
```

### Subir PDFs manualmente
```bash
# Copiar PDFs al directorio rag/
cp documento.pdf /opt/willay/backend/rag/

# Indexar
cd /opt/willay/backend
source venv/bin/activate
python rag_cli.py index
```

## Configuración Avanzada

### Cambiar puerto del backend

Editar servicio:
```bash
sudo nano /etc/systemd/system/willay-backend.service
```

Cambiar línea ExecStart:
```
ExecStart=/opt/willay/backend/venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8080
```

Actualizar Nginx:
```bash
sudo nano /etc/nginx/sites-available/willay
# Cambiar proxy_pass a puerto 8080
sudo systemctl restart willay-backend
sudo systemctl restart nginx
```

### Configurar HTTPS con Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

### Limitar acceso por IP

Editar configuración de Nginx:
```nginx
location / {
    allow 192.168.1.0/24;  # Tu red local
    deny all;
    # ... resto de configuración
}
```

## Firewall

Si usas UFW:

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Monitoreo

### Verificar que todo funciona
```bash
# Backend API
curl http://localhost:8000/health

# Ollama
curl http://localhost:11434/api/tags

# Nginx
curl http://localhost/

# Estado de servicios
systemctl status willay-backend ollama nginx
```

### Recursos del sistema
```bash
# CPU y memoria
htop

# Uso de Ollama
ps aux | grep ollama

# Espacio en disco
df -h
```

## Actualización

```bash
cd /opt/willay
sudo systemctl stop willay-backend

# Actualizar archivos (git pull o copiar nuevos archivos)
# git pull

# Actualizar dependencias
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade

sudo systemctl start willay-backend
```

## Solución de Problemas

### El backend no inicia
```bash
# Ver logs detallados
sudo journalctl -u willay-backend -n 100 --no-pager

# Verificar dependencias
cd /opt/willay/backend
source venv/bin/activate
python -c "import fastapi, uvicorn; print('OK')"
```

### Ollama no responde
```bash
sudo systemctl status ollama
sudo systemctl restart ollama

# Verificar que el modelo está descargado
ollama list
```

### RAG no indexa PDFs
```bash
# Verificar permisos
ls -la /opt/willay/backend/rag/
ls -la /opt/willay/backend/rag_engine/

# Probar manualmente
cd /opt/willay/backend
source venv/bin/activate
python rag_cli.py stats
```

### Nginx muestra 502 Bad Gateway
```bash
# Verificar que el backend está corriendo
curl http://localhost:8000/health

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log
```

## Backup

```bash
# Backup completo
sudo tar -czf willay-backup-$(date +%Y%m%d).tar.gz \
    /opt/willay/backend/rag/ \
    /opt/willay/backend/rag_engine/vector_store/ \
    /etc/systemd/system/willay-backend.service \
    /etc/nginx/sites-available/willay

# Restaurar
sudo tar -xzf willay-backup-YYYYMMDD.tar.gz -C /
sudo systemctl restart willay-backend nginx
```

## Desinstalación

```bash
# Detener y deshabilitar servicios
sudo systemctl stop willay-backend
sudo systemctl disable willay-backend

# Eliminar archivos
sudo rm /etc/systemd/system/willay-backend.service
sudo rm /etc/nginx/sites-enabled/willay
sudo rm /etc/nginx/sites-available/willay
sudo rm -rf /opt/willay

# Recargar servicios
sudo systemctl daemon-reload
sudo systemctl restart nginx

# (Opcional) Desinstalar Ollama
curl -fsSL https://ollama.com/install.sh | OLLAMA_UNINSTALL=1 sh
```

## Soporte

Para más información consulta:
- `README.md` - Documentación general
- `RAG_IMPLEMENTATION.md` - Detalles del sistema RAG
- `SETUP_RAG.md` - Guía de configuración RAG
