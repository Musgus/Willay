# 🚀 INICIO RÁPIDO - Willay

## Windows (Desarrollo)

### 1️⃣ Instalar Ollama
```cmd
# Descargar e instalar desde:
https://ollama.com/download/windows

# Verificar instalación
curl http://127.0.0.1:11434/api/tags
```

### 2️⃣ Descargar Modelos
```cmd
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 3️⃣ Iniciar Backend
```cmd
cd backend
run.bat
```

### 4️⃣ Abrir Frontend
```
Doble clic en: index.html
O arrastrar a Chrome/Edge/Firefox
```

**¡Listo!** Ahora puedes chatear con Willay 🎉

---

## Ubuntu Server (Producción)

### Instalación Automática (Recomendado)
```bash
# Clonar
git clone https://github.com/Musgus/Willay.git
cd Willay/deployment

# Dar permisos
chmod +x install.sh check_ubuntu.sh

# Instalar TODO automáticamente
sudo ./install.sh

# Verificar que todo funciona
sudo ./check_ubuntu.sh
```

**Accede a**: `http://TU_IP_SERVIDOR`

---

## Instalación Manual Ubuntu

Si prefieres instalar paso a paso:

### 1️⃣ Dependencias del Sistema
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx
```

### 2️⃣ Instalar Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable ollama
sudo systemctl start ollama
```

### 3️⃣ Descargar Modelos
```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 4️⃣ Configurar Aplicación
```bash
sudo mkdir -p /opt/willay
sudo chown $USER:$USER /opt/willay
cp -r * /opt/willay/
cd /opt/willay/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5️⃣ Configurar Servicio
```bash
sudo cp /opt/willay/backend/willay-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable willay-backend
sudo systemctl start willay-backend
```

### 6️⃣ Configurar Nginx
```bash
sudo cp /opt/willay/backend/nginx.conf /etc/nginx/sites-available/willay
sudo ln -s /etc/nginx/sites-available/willay /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

**Accede a**: `http://TU_IP_SERVIDOR`

---

## Verificación Rápida

### Windows
```cmd
# Backend corriendo
curl http://127.0.0.1:8000/health

# Ollama funcionando
curl http://127.0.0.1:11434/api/tags

# RAG Stats
cd backend
python rag_cli.py stats
```

### Ubuntu
```bash
# Todo el sistema
sudo ./check_ubuntu.sh

# Backend
curl http://localhost:8000/health

# Logs
sudo journalctl -u willay-backend -f

# Estado del servicio
sudo systemctl status willay-backend
```

---

## Usar RAG (Sistema de Documentos)

### 1️⃣ Agregar PDFs
```bash
# Windows
copy documento.pdf backend\rag\

# Ubuntu
cp documento.pdf /opt/willay/backend/rag/
```

### 2️⃣ Indexar
```bash
# Windows
cd backend
python rag_cli.py index

# Ubuntu
cd /opt/willay/backend
source venv/bin/activate
python rag_cli.py index
```

### 3️⃣ Activar en UI
1. Abre el chatbot
2. Activa el toggle "📚 Usar RAG" en la barra superior
3. ¡Ya puedes hacer preguntas sobre tus documentos!

---

## Comandos Útiles

### Gestión Backend Ubuntu
```bash
# Reiniciar servicio
sudo systemctl restart willay-backend

# Ver logs en tiempo real
sudo journalctl -u willay-backend -f

# Detener servicio
sudo systemctl stop willay-backend

# Estado
sudo systemctl status willay-backend
```

### RAG CLI
```bash
cd backend  # o /opt/willay/backend en Ubuntu
source venv/bin/activate  # Solo Ubuntu

# Ver ayuda
python rag_cli.py --help

# Comandos disponibles
python rag_cli.py index   # Indexar todos los PDFs
python rag_cli.py stats   # Ver estadísticas
python rag_cli.py list    # Listar archivos
python rag_cli.py clear   # Limpiar índice
python rag_cli.py watch   # Auto-indexar (modo observador)
```

---

## Solución de Problemas Comunes

### ❌ Error: "ModuleNotFoundError"
```bash
# Activar entorno virtual e instalar deps
cd backend
# Windows:
.venv\Scripts\activate
# Ubuntu:
source venv/bin/activate

pip install -r requirements.txt
```

### ❌ Error: "Ollama no disponible"
```bash
# Verificar que Ollama esté corriendo
curl http://127.0.0.1:11434/api/tags

# Si no responde, reiniciar Ollama
# Windows: Reiniciar desde servicios de Windows
# Ubuntu:
sudo systemctl restart ollama
```

### ❌ Backend no inicia
```bash
# Ver error específico
# Windows: Ver consola de run.bat
# Ubuntu:
sudo journalctl -u willay-backend -n 50 --no-pager
```

### ❌ Historial no se muestra
1. Abre DevTools (F12)
2. Consola → busca errores
3. Limpia localStorage: `localStorage.clear()`
4. Recarga (Ctrl+F5)

### ❌ RAG no encuentra documentos
```bash
# Verifica que los PDFs estén en la carpeta correcta
# Windows:
dir backend\rag\*.pdf
# Ubuntu:
ls -la /opt/willay/backend/rag/*.pdf

# Re-indexa
python rag_cli.py clear
python rag_cli.py index
```

---

## URLs Importantes

### Windows (Local)
- Frontend: `file:///ruta/a/index.html` o `http://localhost:5500`
- Backend: `http://127.0.0.1:8000`
- API Health: `http://127.0.0.1:8000/health`
- Ollama: `http://127.0.0.1:11434`

### Ubuntu Server
- Frontend: `http://TU_IP_SERVIDOR`
- Backend: `http://TU_IP_SERVIDOR:8000`
- API Docs: `http://TU_IP_SERVIDOR:8000/docs`

---

## 📚 Documentación Completa

- `README.md` - Documentación general y características
- `UBUNTU_DEPLOYMENT.md` - Guía completa de Ubuntu
- `RAG_IMPLEMENTATION.md` - Arquitectura del sistema RAG
- `SETUP_RAG.md` - Configuración paso a paso del RAG
- `CHANGELOG.md` - Registro de cambios
- `IMPLEMENTATION_STATUS.md` - Estado completo del proyecto

---

## 🎓 Características Principales

✅ Chat con IA local (Ollama)
✅ Streaming en tiempo real
✅ Historial de conversaciones
✅ Sistema RAG con PDFs
✅ Panel de administrador
✅ Prompts académicos
✅ 100% privado y local

---

**¿Necesitas ayuda?**
- Consulta `UBUNTU_DEPLOYMENT.md` para troubleshooting avanzado
- Abre un issue en GitHub
- Revisa los logs del sistema

---

**¡Disfruta de Willay! 🎉**
