# 🚀 Configuración RAG - Guía de Instalación

## Paso 1: Instalar modelo de embeddings en Ollama

Para que RAG funcione, necesitas instalar un modelo de embeddings en Ollama:

```cmd
ollama pull nomic-embed-text
```

Este modelo es liviano (~274MB) y genera embeddings de 768 dimensiones, ideal para RAG.

### Alternativa (más pesado pero mejor calidad):

```cmd
ollama pull mxbai-embed-large
```

Si usas este modelo, actualiza `backend/app.py`:

```python
rag_engine = RAGEngine(
    ...
    embedding_model="mxbai-embed-large"  # Cambiar aquí
)
```

## Paso 2: Instalar dependencias Python

```cmd
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
```

Las dependencias RAG incluyen:
- `pypdf2` - Extracción de texto de PDFs
- `chromadb` - Base de datos vectorial
- `sentence-transformers` - Biblioteca de embeddings (usado por ChromaDB)
- `numpy` - Operaciones con arrays
- `watchdog` - Monitoreo de archivos (opcional)

## Paso 3: Verificar instalación

```cmd
# Verificar que Ollama responde
curl http://127.0.0.1:11434/api/tags

# Verificar que el modelo de embeddings está instalado
ollama list | findstr nomic-embed-text
```

## Paso 4: Probar RAG

1. Coloca un PDF de prueba en `rag/`
2. Ejecuta: `python backend/rag_cli.py index`
3. Verifica: `python backend/rag_cli.py stats`

Si todo funciona, deberías ver:

```
📊 Estado del índice:
  • Total de chunks: [número]
  • Total de archivos: 1
```

## Solución de problemas

### Error: "Import chromadb could not be resolved"

```cmd
pip install chromadb --upgrade
```

### Error: "sentence-transformers not found"

```cmd
pip install sentence-transformers
```

### Error generando embeddings

Verifica que el modelo esté instalado:

```cmd
ollama list
```

Si no está, instálalo:

```cmd
ollama pull nomic-embed-text
```

### La indexación es muy lenta

Es normal. Cada chunk requiere llamar a Ollama para generar embeddings. Para un PDF de 50 páginas, puede tardar 2-5 minutos.

### Error: "Can't find ChromaDB database"

ChromaDB creará automáticamente la base de datos en `backend/rag_engine/vector_store/`. Asegúrate de tener permisos de escritura en esa carpeta.

## Uso avanzado

### Re-indexar forzando

```cmd
python backend/rag_cli.py index --force
```

### Modo observador (auto-reindex)

```cmd
python backend/rag_cli.py watch
```

Detecta automáticamente cuando agregas nuevos PDFs y los indexa.

### Búsqueda desde CLI

Edita `backend/rag_cli.py` y agrega:

```python
async def search_test(rag: RAGEngine):
    query = input("Buscar: ")
    results = await rag.search_context(query, n_results=3)
    
    for result in results:
        print(f"\n📄 {result['filename']} - Página {result['page']}")
        print(f"   Score: {result['relevance_score']:.2f}")
        print(f"   {result['text'][:200]}...")
```

## Configuración avanzada

### Ajustar tamaño de chunks

En `backend/app.py`:

```python
rag_engine = RAGEngine(
    chunk_size=1000,    # Aumentar para más contexto
    chunk_overlap=250   # Aumentar overlap
)
```

### Cambiar cantidad de contexto recuperado

En el frontend, ajusta:

```javascript
function buildPayload() {
  return {
    ...
    ragNResults: 10  // Recuperar más chunks
  };
}
```

### Filtrar por archivo

```python
# En backend
context = await rag_engine.search_context(
    query,
    filename_filter="matematicas.pdf"
)
```

## Rendimiento

### Tiempos estimados (Intel i5, 16GB RAM):

- **Extracción PDF** (50 páginas): ~5 segundos
- **Generación embeddings** (50 páginas): ~2-3 minutos
- **Búsqueda** (5 resultados): <1 segundo
- **Indexación completa** (10 PDFs, 500 páginas): ~15-20 minutos

### Optimizaciones:

1. Usa caché (ya implementado) para evitar re-procesar
2. Reduce `chunk_size` para menos embeddings
3. Usa `nomic-embed-text` (más rápido que mxbai)
4. Indexa de noche o en segundo plano

## Próximos pasos

Una vez funcional:
1. Agrega tus documentos académicos
2. Prueba preguntas específicas
3. Ajusta parámetros según necesites
4. Considera implementar caché de búsquedas frecuentes

---

**¿Dudas?** Revisa los logs en el panel de administrador o los mensajes de consola del backend.
