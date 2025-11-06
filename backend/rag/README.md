# 📚 Carpeta RAG - Documentos para Willay

Esta carpeta contiene los documentos PDF que Willay utilizará como base de conocimiento.

## 📖 ¿Qué es RAG?

**RAG (Retrieval-Augmented Generation)** es una técnica que permite a Willay:
- Buscar información relevante en tus documentos
- Usar esa información para responder preguntas con mayor precisión
- Citar las fuentes (archivo y página) de donde obtuvo la información

## 🚀 Cómo usar

### 1. Agregar documentos PDF

Simplemente coloca tus archivos PDF en esta carpeta:

```
rag/
├── matematicas_basicas.pdf
├── fisica_teoria.pdf
├── programacion_python.pdf
└── ...
```

### 2. Indexar los documentos

Tienes dos opciones:

**Opción A - Script CLI (recomendado):**
```cmd
cd backend
python rag_cli.py index
```

**Opción B - API REST:**
```cmd
curl -X POST http://127.0.0.1:8000/rag/index
```

### 3. Usar RAG en el chat

En el frontend, activa el toggle **"Usar RAG"** antes de hacer tu pregunta. Willay buscará automáticamente información relevante en los documentos indexados.

## 🛠️ Comandos CLI

```cmd
# Indexar documentos
python rag_cli.py index

# Forzar re-indexación completa
python rag_cli.py index --force

# Ver estadísticas
python rag_cli.py stats

# Listar documentos indexados
python rag_cli.py list

# Limpiar índice
python rag_cli.py clear

# Modo observador (auto-reindex cuando hay cambios)
python rag_cli.py watch
```

## 📊 ¿Qué sucede al indexar?

1. **Extracción**: Se extrae el texto de cada PDF página por página
2. **Caché**: El texto se guarda en `backend/rag_engine/cache/` para no volver a procesar
3. **Chunking**: El texto se divide en fragmentos de ~800 caracteres
4. **Embeddings**: Cada fragmento se convierte en un vector usando Ollama (`nomic-embed-text`)
5. **Almacenamiento**: Los vectores se guardan en `backend/rag_engine/vector_store/` (ChromaDB)

## ⚙️ Configuración avanzada

Puedes ajustar parámetros en `backend/app.py`:

```python
rag_engine = RAGEngine(
    pdf_dir="rag",
    embedding_model="nomic-embed-text",  # o "mxbai-embed-large"
    chunk_size=800,                      # Tamaño de chunks
    chunk_overlap=200                    # Overlap entre chunks
)
```

## 📝 Notas importantes

- **Privacidad**: Todo el procesamiento es local, los documentos nunca salen de tu PC
- **Modelo de embeddings**: Asegúrate de tener `nomic-embed-text` en Ollama:
  ```cmd
  ollama pull nomic-embed-text
  ```
- **Rendimiento**: La indexación puede tardar varios minutos dependiendo del tamaño de los PDFs
- **Caché**: Los archivos `.txt` en `cache/` aceleran la re-indexación

## 🐛 Solución de problemas

### "No se encontraron PDFs"
- Verifica que los archivos tengan extensión `.pdf`
- Asegúrate de estar en el directorio correcto

### "Error generando embeddings"
- Verifica que Ollama esté corriendo: `curl http://127.0.0.1:11434`
- Instala el modelo: `ollama pull nomic-embed-text`

### La indexación es muy lenta
- Es normal, cada página genera múltiples embeddings
- Puedes reducir `chunk_size` para menos chunks (menos precisión)

### No encuentra información en el chat
- Verifica que RAG esté activado (toggle en frontend)
- Aumenta `rag_n_results` para buscar más contexto
- Re-indexa con `--force` si modificaste los PDFs

## 🎯 Mejores prácticas

✅ **DO:**
- Usar PDFs con texto seleccionable (no escaneos de imágenes)
- Organizar documentos por materia
- Re-indexar después de agregar nuevos PDFs
- Probar con preguntas específicas del contenido

❌ **DON'T:**
- No subas documentos confidenciales si compartes el proyecto
- No uses PDFs con DRM o protección de copia
- No esperes que funcione con PDFs puramente gráficos

---

**💡 Tip**: Prueba hacer preguntas como:
- "¿Qué dice el documento sobre [tema]?"
- "Resume la página 5 del archivo [nombre]"
- "Explica el concepto de [X] según los documentos"

Willay citará automáticamente las fuentes cuando use información de los PDFs.
