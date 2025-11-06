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
├── backend/
│   ├── app.py          # FastAPI con streaming y sesiones
│   ├── requirements.txt
│   ├── run.bat         # Script de inicio (Windows)
│   └── run.ps1         # Script de inicio (PowerShell)
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

## 🔮 Próximas Características (RAG)

- 📚 **RAG (Retrieval-Augmented Generation)**: Carga PDFs, TXT y documentos para entrenar a Willay con tu propio "rack de libros"
- 🔍 **Búsqueda vectorial**: Embeddings con ChromaDB o FAISS
- 📊 **Indexación de URLs**: Scraping y entrenamiento desde sitios web
- 🎓 **Modos de entrenamiento**: Contexto específico por materia

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

## 📄 Licencia

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
- Compatible únicamente con Windows (por ahora).
- Requiere ~4GB RAM mínimo para modelos llama3.2.

---

**🎓 Hecho con ❤️ para estudiantes que buscan privacidad y control sobre su asistente IA.**
