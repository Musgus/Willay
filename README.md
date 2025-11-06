# 🎓 Willay - Asistente Académico con IA Local

**Willay** es un chatbot académico inteligente que utiliza Ollama para ejecutar modelos de lenguaje localmente en Windows, con streaming en tiempo real y memoria conversacional.

---

## ✨ Características

- 🤖 **IA Local con Ollama**: Usa modelos LLM (llama3.2, llama3, llama2) sin necesidad de APIs externas
- 💬 **Streaming en tiempo real**: Respuestas token por token, como ChatGPT
- 🧠 **Memoria conversacional**: Mantiene contexto de la conversación con sistema de sesiones
- 📚 **Prompts académicos especializados**: Matemáticas, Física, Programación, Historia, Literatura, Química
- 📖 **Historial persistente**: Guarda y recupera conversaciones anteriores
- ⚙️ **Panel de administrador**: Logs en tiempo real, estadísticas de uso
- 🎨 **UI moderna y responsive**: Diseño limpio con sidebar desplegable
- 🔧 **Configurable**: Selector de modelo, control de temperatura

---

## 📋 Requisitos Previos

- **Windows 10/11**
- **Python 3.8+** instalado y en PATH
- **Ollama para Windows** ([descargar aquí](https://ollama.com/download/windows))
- Navegador web moderno (Chrome, Edge, Firefox)

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Musgus/Willay.git
cd Willay
```

### 2. Instalar y configurar Ollama

```cmd
# Ollama ya debería estar corriendo tras instalarlo
# Verifica que esté activo:
curl http://127.0.0.1:11434/api/tags

# Descarga el modelo llama3.2 (recomendado):
ollama pull llama3.2
```

### 3. Configurar el backend

Desde la carpeta `backend/`, ejecuta:

**Opción A - Usando run.bat (doble clic):**
```cmd
cd backend
run.bat
```

**Opción B - PowerShell:**
```powershell
cd backend
powershell -ExecutionPolicy Bypass -File run.ps1
```

**Opción C - Manual:**
```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```

> ⚠️ Si Windows Firewall solicita permiso, **acepta** para permitir conexiones locales.

---

## 🎯 Uso

1. **Inicia el backend** (ver paso 3 arriba). Deberías ver:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```

2. **Abre `index.html`** en tu navegador (doble clic o arrastra a la ventana del navegador)

3. **¡Listo!** Puedes:
   - Seleccionar un **prompt académico** en el sidebar (Matemáticas, Física, etc.)
   - Escribir tu pregunta directamente
   - Ajustar **modelo** y **temperatura** según necesites
   - Ver el **historial** de conversaciones en el sidebar
   - Acceder al **Panel Admin** (⚙️) para ver logs y estadísticas

---

## 📁 Estructura del Proyecto

```
Willay/
├── index.html          # Interfaz principal del chatbot
├── style.css           # Estilos responsive con sidebar
├── script.js           # Lógica frontend: streaming, historial, admin
├── install.sh          # Instalador automático para Ubuntu Server
├── UBUNTU_DEPLOYMENT.md # Guía completa de despliegue en Ubuntu
├── backend/
│   ├── app.py          # FastAPI con streaming y sesiones
│   ├── requirements.txt
│   ├── run.bat         # Script de inicio (Windows)
│   ├── run.ps1         # Script de inicio (PowerShell)
│   ├── run.sh          # Script de inicio (Ubuntu/Linux)
│   ├── willay-backend.service  # Archivo systemd para Ubuntu
│   ├── rag_cli.py      # CLI para gestión RAG
│   └── rag_engine/     # Motor RAG completo
└── README.md
```

---

## 🛠️ Tecnologías

### Frontend (Vanilla)
- HTML5 + CSS3 (sin frameworks)
- JavaScript puro con Fetch API
- LocalStorage para persistencia

### Backend
- **FastAPI** - Framework web asíncrono
- **Uvicorn** - Servidor ASGI
- **httpx** - Cliente HTTP asíncrono para Ollama
- **Pydantic v2** - Validación de datos

### IA
- **Ollama** - Motor de modelos LLM local
- Modelos soportados: llama3.2, llama3, llama2

---

## ⚙️ Configuración

### Cambiar modelo por defecto
Edita `index.html`, línea 39:
```html
<option value="llama3.2" selected>llama3.2</option>
```

### Ajustar límite de tokens
Edita `backend/app.py`, línea 17:
```python
MAX_RESPONSE_CHARS = 500  # Caracteres máximos por respuesta
```

### Modificar temperatura por defecto
Edita `index.html`, línea 44:
```html
<input type="range" id="temperatureRange" ... value="0.3" ...>
```

---

## � Sistema RAG (¡Disponible Ahora!)

**RAG (Retrieval-Augmented Generation)** ya está implementado y funcional. Características:

- ✅ **Carga de PDFs**: Sube documentos y Willay los usa como fuente de conocimiento
- ✅ **Búsqueda vectorial**: Embeddings locales con ChromaDB + Ollama
- ✅ **Indexación automática**: Procesa PDFs, extrae texto, genera embeddings
- ✅ **Citación de fuentes**: Willay menciona archivo y página de donde obtiene información
- ✅ **Panel de gestión**: Interfaz web para subir, indexar y eliminar documentos
- ✅ **CLI incluido**: Script para indexar desde terminal
- ✅ **100% local**: Todo el procesamiento en tu PC, sin APIs externas

### 🚀 Configuración RAG

**1. Instalar modelo de embeddings:**
```cmd
ollama pull nomic-embed-text
```

**2. Reinstalar dependencias con soporte RAG:**
```cmd
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
```

**3. Colocar PDFs en la carpeta `rag/`**

**4. Indexar documentos:**
```cmd
cd backend
python rag_cli.py index
```

**5. En el frontend, activar el toggle "📚 Usar RAG"**

📖 **Guía completa**: Ver [SETUP_RAG.md](SETUP_RAG.md) para instrucciones detalladas.

### Comandos RAG disponibles

```cmd
# Indexar documentos
python backend/rag_cli.py index

# Ver estadísticas
python backend/rag_cli.py stats

# Listar archivos indexados
python backend/rag_cli.py list

# Limpiar índice
python backend/rag_cli.py clear

# Modo observador (auto-reindex)
python backend/rag_cli.py watch
```

---

## 🐛 Solución de Problemas

### Error: `ModuleNotFoundError: No module named 'httpx'`
**Solución**: Instala las dependencias con `pip install -r requirements.txt` dentro del venv.

### Error: `NetworkError when attempting to fetch resource`
**Solución**: 
1. Verifica que el backend esté corriendo en `http://127.0.0.1:8000`
2. Revisa que CORS permita `null` (ya configurado)

### Error: `Ollama no disponible`
**Solución**:
1. Verifica que Ollama esté corriendo: `curl http://127.0.0.1:11434/api/tags`
2. Si no, inicia Ollama o reinicia el servicio de Windows

### El streaming no funciona
**Solución**: Algunos navegadores bloquean streaming desde `file://`. Usa un servidor local:
```cmd
python -m http.server 5500
```
Luego abre `http://localhost:5500`

---

## � Despliegue en Ubuntu Server

Willay ahora soporta despliegue completo en Ubuntu Server con instalación automática.

### Instalación Rápida en Ubuntu

```bash
# Clonar repositorio
git clone https://github.com/Musgus/Willay.git
cd Willay

# Dar permisos de ejecución
chmod +x install.sh

# Ejecutar instalador (instala Ollama, Nginx, crea servicios systemd)
sudo ./install.sh
```

El instalador automáticamente:
- ✅ Instala Python, Nginx y dependencias
- ✅ Instala y configura Ollama
- ✅ Descarga modelos (llama3.2, nomic-embed-text)
- ✅ Crea servicio systemd para el backend
- ✅ Configura Nginx como reverse proxy
- ✅ Inicia todos los servicios

Después de la instalación:
- Frontend: `http://TU_IP_SERVIDOR`
- API: `http://TU_IP_SERVIDOR:8000`

### Gestión del Servicio

```bash
# Ver logs en tiempo real
sudo journalctl -u willay-backend -f

# Reiniciar servicio
sudo systemctl restart willay-backend

# Estado
sudo systemctl status willay-backend
```

📖 **Guía completa**: Ver [UBUNTU_DEPLOYMENT.md](UBUNTU_DEPLOYMENT.md) para instrucciones detalladas, configuración avanzada, HTTPS, monitoreo y troubleshooting.

---

## �📄 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---

## 👨‍💻 Autor

Desarrollado por **Musgus**  
GitHub: [@Musgus](https://github.com/Musgus)

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea tu rama de característica (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: nueva característica'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Notas

- Este proyecto NO envía datos a servicios externos; todo se ejecuta localmente.
- Compatible con **Windows** (scripts .bat/.ps1) y **Ubuntu Server** (scripts .sh + systemd).
- Requiere ~8GB RAM para despliegue en servidor con Ollama.
- Para desarrollo local Windows, 4GB RAM es suficiente.

---

**🎓 Hecho con ❤️ para estudiantes que buscan privacidad y control sobre su asistente IA.**
