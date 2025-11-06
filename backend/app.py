import asyncio
import json
import time
from typing import AsyncGenerator, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
SYSTEM_PROMPT = "Responde en frases cortas."
SESSION_TTL_SECONDS = 1800
MAX_RESPONSE_CHARS = 500
MAX_SESSION_MESSAGES = 20
HTTP_TIMEOUT = httpx.Timeout(60.0, connect=10.0)

app = FastAPI(title="Ollama Chatbot", version="1.0.0")

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
