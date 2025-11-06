import asyncio
import json
import time
from typing import AsyncGenerator, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from pathlib import Path
import shutil

from rag_engine import RAGEngine

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
SYSTEM_PROMPT = "Responde en frases cortas."
SESSION_TTL_SECONDS = 1800
MAX_RESPONSE_CHARS = 500
MAX_SESSION_MESSAGES = 20
HTTP_TIMEOUT = httpx.Timeout(60.0, connect=10.0)

app = FastAPI(title="Willay Chatbot", version="2.0.0")

# Inicializar motor RAG
rag_engine = RAGEngine(
    pdf_dir="rag",
    cache_dir="backend/rag_engine/cache",
    vector_store_dir="backend/rag_engine/vector_store",
    embedding_model="nomic-embed-text"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    model: str = Field(default="llama3.2", min_length=1)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    messages: Optional[List[ChatMessage]] = None
    prompt: Optional[str] = None
    client_id: Optional[str] = Field(default=None, alias="clientId")
    reset: bool = False
    use_rag: bool = Field(default=False, alias="useRag")
    rag_n_results: int = Field(default=5, ge=1, le=10, alias="ragNResults")

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class ChatResponse(BaseModel):
    response: str


class SessionData(BaseModel):
    messages: List[ChatMessage]
    expires_at: float


_sessions: Dict[str, SessionData] = {}
_sessions_lock = asyncio.Lock()


async def _prune_sessions() -> None:
    now = time.time()
    stale = [key for key, value in _sessions.items() if value.expires_at <= now]
    for key in stale:
        _sessions.pop(key, None)


async def _get_session_messages(client_id: str) -> List[ChatMessage]:
    async with _sessions_lock:
        await _prune_sessions()
        data = _sessions.get(client_id)
        if not data:
            return []
        return list(data.messages)


async def _save_session_messages(client_id: str, messages: List[ChatMessage]) -> None:
    trimmed = list(messages)[-MAX_SESSION_MESSAGES:]
    data = SessionData(messages=trimmed, expires_at=time.time() + SESSION_TTL_SECONDS)
    async with _sessions_lock:
        _sessions[client_id] = data


async def _clear_session(client_id: str) -> None:
    async with _sessions_lock:
        _sessions.pop(client_id, None)


def _ensure_system_message(messages: List[ChatMessage]) -> List[ChatMessage]:
    if messages and messages[0].role == "system":
        return messages
    return [ChatMessage(role="system", content=SYSTEM_PROMPT), *messages]


def _sanitize_messages(messages: List[ChatMessage]) -> List[ChatMessage]:
    sanitized: List[ChatMessage] = []
    for message in messages:
        content = (message.content or "").strip()
        if not content:
            continue
        sanitized.append(ChatMessage(role=message.role, content=content))
    return sanitized


async def _build_messages(payload: ChatRequest) -> List[ChatMessage]:
    if payload.reset and payload.client_id:
        await _clear_session(payload.client_id)

    incoming = _sanitize_messages(payload.messages or [])
    if not incoming:
        prompt = (payload.prompt or "").strip()
        if not prompt:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No recibí ningún mensaje")
        incoming = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(role="user", content=prompt),
        ]

    if payload.client_id and not payload.reset and not payload.messages:
        session_messages = await _get_session_messages(payload.client_id)
    else:
        session_messages = []

    merged = list(session_messages or []) + incoming
    merged = _ensure_system_message(merged)
    
    # Si RAG está habilitado, enriquecer el system prompt con contexto
    if payload.use_rag and rag_engine.is_indexed():
        # Obtener el último mensaje del usuario
        last_user_msg = next((m.content for m in reversed(merged) if m.role == "user"), "")
        
        if last_user_msg:
            # Buscar contexto relevante
            context_chunks = await rag_engine.search_context(
                last_user_msg,
                n_results=payload.rag_n_results
            )
            
            if context_chunks:
                # Enriquecer el system prompt con contexto
                original_system = merged[0].content if merged and merged[0].role == "system" else SYSTEM_PROMPT
                enhanced_system = rag_engine.build_rag_prompt(
                    last_user_msg,
                    context_chunks,
                    original_system
                )
                
                # Reemplazar el system message
                if merged and merged[0].role == "system":
                    merged[0] = ChatMessage(role="system", content=enhanced_system)
                else:
                    merged.insert(0, ChatMessage(role="system", content=enhanced_system))
    
    return merged[-MAX_SESSION_MESSAGES:]


async def _ollama_stream(
    messages: List[ChatMessage],
    model: str,
    temperature: float,
) -> AsyncGenerator[str, None]:
    payload = {
        "model": model,
        "messages": [message.model_dump() for message in messages],
        "stream": True,
        "options": {"temperature": temperature, "num_predict": 128},
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get("error"):
                    raise RuntimeError(data["error"])
                content = data.get("message", {}).get("content", "")
                if content:
                    yield content
                if data.get("done"):
                    break





def _truncate_text(text: str) -> str:
    if len(text) <= MAX_RESPONSE_CHARS:
        return text
    return text[:MAX_RESPONSE_CHARS].rstrip() + "…"





async def _finalize_session(
    client_id: Optional[str],
    conversation: List[ChatMessage],
    assistant_reply: str,
) -> None:
    if not client_id:
        return
    if not assistant_reply.strip():
        return
    updated = conversation + [ChatMessage(role="assistant", content=assistant_reply)]
    await _save_session_messages(client_id, updated)


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> JSONResponse:
    if payload.reset and not (payload.messages or (payload.prompt and payload.prompt.strip())):
        if payload.client_id:
            await _clear_session(payload.client_id)
        return JSONResponse(content=ChatResponse(response="Sesión reiniciada").model_dump())

    try:
        messages = await _build_messages(payload)
        accumulated = ""

        try:
            async for token in _ollama_stream(messages, payload.model, payload.temperature):
                if len(accumulated) >= MAX_RESPONSE_CHARS:
                    break
                remaining = MAX_RESPONSE_CHARS - len(accumulated)
                snippet = token[:remaining]
                accumulated += snippet
        except (httpx.HTTPError, RuntimeError) as error:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Ollama no disponible") from error
        except Exception as error:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Error interno") from error

        if not accumulated:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Error interno")

        await _finalize_session(payload.client_id, messages, accumulated)
        return JSONResponse(content=ChatResponse(response=accumulated).model_dump())

    except HTTPException:
        raise
    except Exception as error:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno") from error


@app.post("/chat/stream")
async def chat_stream(payload: ChatRequest):
    if payload.reset and not (payload.messages or (payload.prompt and payload.prompt.strip())):
        if payload.client_id:
            await _clear_session(payload.client_id)
        return StreamingResponse(iter(["Sesión reiniciada"]), media_type="text/plain")

    try:
        messages = await _build_messages(payload)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    async def stream_generator():
        accumulated = ""
        try:
            async for token in _ollama_stream(messages, payload.model, payload.temperature):
                if len(accumulated) >= MAX_RESPONSE_CHARS:
                    break
                remaining = MAX_RESPONSE_CHARS - len(accumulated)
                snippet = token[:remaining]
                if not snippet:
                    continue
                accumulated_part = snippet
                accumulated += accumulated_part
                yield accumulated_part
        except (httpx.HTTPError, RuntimeError):
            yield "Ollama no disponible"
            return
        except Exception:
            yield "Error interno"
            return
        finally:
            await _finalize_session(payload.client_id, messages, accumulated)

    return StreamingResponse(stream_generator(), media_type="text/plain")


@app.get("/health")
async def health_check():
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
        return {"status": "ok"}
    except httpx.HTTPError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Ollama no disponible")


@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        return await asyncio.wait_for(call_next(request), timeout=65.0)
    except asyncio.TimeoutError as error:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Tiempo de espera superado") from error


# ==================== ENDPOINTS RAG ====================

@app.post("/rag/index")
async def rag_index_documents(force: bool = False):
    """
    Indexa todos los PDFs en el directorio rag/
    
    Query params:
        force: Si True, fuerza la re-indexación completa
    """
    try:
        stats = await rag_engine.index_documents(force=force)
        return JSONResponse(content=stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error indexando documentos: {str(e)}"
        )


@app.get("/rag/stats")
async def rag_get_stats():
    """Retorna estadísticas del sistema RAG"""
    try:
        stats = rag_engine.get_stats()
        stats["is_indexed"] = rag_engine.is_indexed()
        stats["indexed_files"] = rag_engine.get_indexed_files()
        return JSONResponse(content=stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@app.post("/rag/upload")
async def rag_upload_pdf(file: UploadFile = File(...)):
    """
    Sube un PDF al directorio rag/
    
    Luego debes llamar a /rag/index para indexarlo
    """
    try:
        # Verificar que sea PDF
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se permiten archivos PDF"
            )
        
        # Guardar archivo
        pdf_path = Path("rag") / file.filename
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return JSONResponse(content={
            "status": "success",
            "filename": file.filename,
            "message": "PDF subido correctamente. Ejecuta /rag/index para indexarlo."
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo PDF: {str(e)}"
        )


@app.delete("/rag/document/{filename}")
async def rag_delete_document(filename: str):
    """Elimina un documento del índice y del directorio"""
    try:
        # Eliminar del índice
        rag_engine.remove_document(filename)
        
        # Eliminar archivo físico
        pdf_path = Path("rag") / filename
        if pdf_path.exists():
            pdf_path.unlink()
        
        # Eliminar caché
        cache_path = Path("backend/rag_engine/cache") / f"{Path(filename).stem}.txt"
        if cache_path.exists():
            cache_path.unlink()
        
        return JSONResponse(content={
            "status": "success",
            "message": f"Documento {filename} eliminado"
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando documento: {str(e)}"
        )


@app.delete("/rag/clear")
async def rag_clear_index():
    """Limpia completamente el índice RAG (no elimina PDFs)"""
    try:
        rag_engine.clear_index()
        return JSONResponse(content={
            "status": "success",
            "message": "Índice RAG limpiado"
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error limpiando índice: {str(e)}"
        )


@app.post("/rag/search")
async def rag_search_context(query: str, n_results: int = 5):
    """
    Busca contexto relevante en los documentos indexados
    
    Query params:
        query: Texto de búsqueda
        n_results: Cantidad de resultados (default: 5)
    """
    try:
        if not rag_engine.is_indexed():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay documentos indexados"
            )
        
        context_chunks = await rag_engine.search_context(query, n_results=n_results)
        
        return JSONResponse(content={
            "query": query,
            "results": context_chunks
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en búsqueda: {str(e)}"
        )
