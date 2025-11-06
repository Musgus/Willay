(() => {
  const API_BASE = "http://127.0.0.1:8000";
  const systemMessage = { role: "system", content: "Responde en frases cortas." };
  const MAX_CONTEXT = 20;
  let isStreaming = false;

  const messagesContainer = document.getElementById("messages");
  const chatForm = document.getElementById("chatForm");
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const newChatBtn = document.getElementById("newChatBtn");
  const modelSelect = document.getElementById("modelSelect");
  const temperatureRange = document.getElementById("temperatureRange");
  const temperatureValue = document.getElementById("temperatureValue");
  const statusText = document.getElementById("statusText");
  const chatHistoryContainer = document.getElementById("chatHistory");

  const clientId = ensureClientId();
  let currentSessionId = getCurrentSessionId();
  
  // RAG elements
  const ragToggle = document.getElementById("ragToggle");
  const ragStatus = document.getElementById("ragStatus");
  const ragUploadBtn = document.getElementById("ragUploadBtn");
  const ragFileInput = document.getElementById("ragFileInput");
  const ragIndexBtn = document.getElementById("ragIndexBtn");
  const ragClearBtn = document.getElementById("ragClearBtn");
  const ragFilesList = document.getElementById("ragFilesList");
  const ragTotalFiles = document.getElementById("ragTotalFiles");
  const ragTotalChunks = document.getElementById("ragTotalChunks");
  
  updateTemperatureLabel();
  loadRagStatus();
  renderChatHistory();

  temperatureRange.addEventListener("input", updateTemperatureLabel);
  
  // RAG event listeners
  if (ragToggle) {
    ragToggle.addEventListener("change", handleRagToggle);
  }
  
  if (ragUploadBtn) {
    ragUploadBtn.addEventListener("click", () => ragFileInput.click());
  }
  
  if (ragFileInput) {
    ragFileInput.addEventListener("change", handleRagUpload);
  }
  
  if (ragIndexBtn) {
    ragIndexBtn.addEventListener("click", handleRagIndex);
  }
  
  if (ragClearBtn) {
    ragClearBtn.addEventListener("click", handleRagClear);
  }

  chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (isStreaming) {
      return;
    }

    const rawMessage = messageInput.value.trim();
    if (!rawMessage) {
      showStatus("No recibí ningún mensaje");
      return;
    }

    messageInput.value = "";
    pushMessage({ role: "user", content: rawMessage });
    renderMessageBubble("user", rawMessage);

    try {
      await streamAssistantReply();
    } catch (error) {
      showStatus(error.message || "Error interno");
    }
  });

  newChatBtn.addEventListener("click", async () => {
    if (isStreaming) {
      return;
    }

    clearConversation();
    renderMessageBubble("assistant", "Historial reiniciado.");
    await notifyReset();
  });

  function ensureClientId() {
    try {
      const stored = localStorage.getItem("ollamaClientId");
      if (stored) {
        return stored;
      }
      const generated = crypto.randomUUID();
      localStorage.setItem("ollamaClientId", generated);
      return generated;
    } catch (error) {
      return `client-${Date.now()}`;
    }
  }

  function getCurrentSessionId() {
    let sessionId = localStorage.getItem("currentSessionId");
    if (!sessionId) {
      sessionId = `session-${Date.now()}`;
      localStorage.setItem("currentSessionId", sessionId);
    }
    return sessionId;
  }

  function getCurrentSession() {
    const sessions = getAllSessions();
    return sessions[currentSessionId] || createNewSession();
  }

  function getAllSessions() {
    try {
      const data = localStorage.getItem("chatSessions");
      return data ? JSON.parse(data) : {};
    } catch {
      return {};
    }
  }

  function saveSessions(sessions) {
    try {
      localStorage.setItem("chatSessions", JSON.stringify(sessions));
    } catch (error) {
      console.error("Error guardando sesiones:", error);
    }
  }

  function createNewSession() {
    const session = {
      id: currentSessionId,
      title: "Nueva conversación",
      messages: [systemMessage],
      timestamp: Date.now()
    };
    const sessions = getAllSessions();
    sessions[currentSessionId] = session;
    saveSessions(sessions);
    return session;
  }

  function addMessageToSession(role, content) {
    const sessions = getAllSessions();
    const session = sessions[currentSessionId];
    
    if (!session) {
      createNewSession();
      return addMessageToSession(role, content);
    }

    session.messages.push({ role, content });
    
    // Actualizar título con el primer mensaje del usuario
    if (role === "user" && session.messages.filter(m => m.role === "user").length === 1) {
      session.title = content.substring(0, 50) + (content.length > 50 ? "..." : "");
    }
    
    session.timestamp = Date.now();

    // Limitar contexto
    while (session.messages.length > MAX_CONTEXT) {
      session.messages.splice(1, 1);
    }

    saveSessions(sessions);
    renderChatHistory();
  }

  function loadSession(sessionId) {
    const sessions = getAllSessions();
    const session = sessions[sessionId];
    
    if (!session) return;

    currentSessionId = sessionId;
    localStorage.setItem("currentSessionId", sessionId);

    // Limpiar chat actual
    messagesContainer.innerHTML = "";

    // Renderizar mensajes (excepto el system)
    session.messages.forEach((msg) => {
      if (msg.role !== "system") {
        renderMessageBubble(msg.role, msg.content);
      }
    });

    renderChatHistory();
    showStatus("Sesión cargada");
  }

  function deleteSession(sessionId) {
    const sessions = getAllSessions();
    delete sessions[sessionId];
    saveSessions(sessions);

    if (sessionId === currentSessionId) {
      // Si borramos la sesión actual, crear una nueva
      currentSessionId = `session-${Date.now()}`;
      localStorage.setItem("currentSessionId", currentSessionId);
      createNewSession();
      messagesContainer.innerHTML = "";
    }

    renderChatHistory();
  }

  function renderChatHistory() {
    if (!chatHistoryContainer) return;

    const sessions = getAllSessions();
    const sessionIds = Object.keys(sessions).sort((a, b) => {
      return sessions[b].timestamp - sessions[a].timestamp;
    });

    if (sessionIds.length === 0) {
      chatHistoryContainer.innerHTML = '<p style="padding: 10px; color: #999; font-size: 0.9em;">No hay conversaciones</p>';
      return;
    }

    chatHistoryContainer.innerHTML = "";

    sessionIds.forEach((sessionId) => {
      const session = sessions[sessionId];
      const item = document.createElement("div");
      item.classList.add("history-item");
      
      if (sessionId === currentSessionId) {
        item.classList.add("active");
      }

      const title = document.createElement("div");
      title.classList.add("history-item-title");
      title.textContent = session.title || "Sin título";

      const date = document.createElement("div");
      title.classList.add("history-item-date");
      date.textContent = formatDate(session.timestamp);

      const deleteBtn = document.createElement("button");
      deleteBtn.classList.add("history-delete");
      deleteBtn.textContent = "×";
      deleteBtn.onclick = (e) => {
        e.stopPropagation();
        if (confirm("¿Eliminar esta conversación?")) {
          deleteSession(sessionId);
        }
      };

      item.onclick = () => loadSession(sessionId);

      item.appendChild(title);
      item.appendChild(date);
      item.appendChild(deleteBtn);

      chatHistoryContainer.appendChild(item);
    });
  }

  function formatDate(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return "Ahora";
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h`;
    
    return date.toLocaleDateString("es-ES", { month: "short", day: "numeric" });
  }

  function updateTemperatureLabel() {
    temperatureValue.textContent = Number(temperatureRange.value).toFixed(1);
  }

  function pushMessage(message) {
    addMessageToSession(message.role, message.content);
  }

  function showStatus(text) {
    statusText.textContent = text || "";
  }

  function renderMessageBubble(role, content, isError = false) {
    const bubble = document.createElement("div");
    bubble.classList.add("message");
    bubble.classList.add(role === "user" ? "message-user" : "message-assistant");
    if (isError) {
      bubble.classList.add("message-error");
    }
    bubble.textContent = content;
    messagesContainer.appendChild(bubble);
    autoScroll();
    return bubble;
  }

  function autoScroll() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  async function streamAssistantReply() {
    isStreaming = true;
    sendBtn.disabled = true;
    newChatBtn.disabled = true;
    messageInput.disabled = true;
    showStatus("Enviando...");

    const assistantBubble = renderMessageBubble("assistant", "");
    const payload = buildPayload();

    let assistantText = "";
    let reader = null;

    try {
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok || !response.body) {
        let errorDetail = "Error interno";
        try {
          const data = await response.json();
          errorDetail = data.detail || errorDetail;
        } catch (parseError) {
          errorDetail = response.statusText || errorDetail;
        }
        throw new Error(errorDetail);
      }

      reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          break;
        }
        const chunk = decoder.decode(value, { stream: true });
        if (!chunk) {
          continue;
        }
        assistantText += chunk;
        assistantBubble.textContent = assistantText;
        autoScroll();
      }

      if (!assistantText) {
        throw new Error("Error interno");
      }

      pushMessage({ role: "assistant", content: assistantText });
      showStatus("Listo");
    } catch (error) {
      assistantBubble.textContent = error.message || "Error interno";
      assistantBubble.classList.add("message-error");
      showStatus(error.message || "Error interno");
      throw error;
    } finally {
      if (reader) {
        reader.releaseLock();
      }
      isStreaming = false;
      sendBtn.disabled = false;
      newChatBtn.disabled = false;
      messageInput.disabled = false;
    }
  }

  function buildPayload() {
    const session = getCurrentSession();
    const messages = session.messages.map((item) => ({ role: item.role, content: item.content }));
    return {
      clientId,
      model: modelSelect.value,
      temperature: Number(temperatureRange.value),
      messages,
      useRag: ragToggle ? ragToggle.checked : false,
      ragNResults: 5
    };
  }

  function clearConversation() {
    // Crear nueva sesión
    currentSessionId = `session-${Date.now()}`;
    localStorage.setItem("currentSessionId", currentSessionId);
    createNewSession();
    messagesContainer.innerHTML = "";
    renderChatHistory();
    showStatus("Nuevo chat listo");
  }

  async function notifyReset() {
    try {
      await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clientId, reset: true })
      });
    } catch (error) {
      showStatus("Servidor sin respuesta, intenta de nuevo");
    }
  }

  // ==================== FUNCIONES RAG ====================

  async function loadRagStatus() {
    try {
      const response = await fetch(`${API_BASE}/rag/stats`);
      if (response.ok) {
        const data = await response.json();
        updateRagUI(data);
      }
    } catch (error) {
      console.error("Error cargando estado RAG:", error);
    }
  }

  function updateRagUI(stats) {
    if (ragTotalFiles) ragTotalFiles.textContent = stats.total_files || 0;
    if (ragTotalChunks) ragTotalChunks.textContent = stats.total_chunks || 0;
    
    if (ragStatus) {
      if (stats.is_indexed) {
        ragStatus.textContent = `${stats.total_files} docs indexados`;
        ragStatus.style.color = "#4caf50";
      } else {
        ragStatus.textContent = "Sin documentos";
        ragStatus.style.color = "#999";
      }
    }

    if (ragFilesList) {
      renderRagFilesList(stats.files || []);
    }
  }

  function renderRagFilesList(files) {
    if (!ragFilesList) return;

    if (files.length === 0) {
      ragFilesList.innerHTML = '<p class="loading-text">No hay documentos indexados</p>';
      return;
    }

    ragFilesList.innerHTML = "";
    
    files.forEach(file => {
      const item = document.createElement("div");
      item.classList.add("rag-file-item");

      const info = document.createElement("div");
      info.classList.add("rag-file-info");

      const name = document.createElement("div");
      name.classList.add("rag-file-name");
      name.textContent = file.filename;

      const meta = document.createElement("div");
      meta.classList.add("rag-file-meta");
      meta.textContent = `${file.chunks} chunks • ${file.pages} páginas`;

      info.appendChild(name);
      info.appendChild(meta);

      const deleteBtn = document.createElement("button");
      deleteBtn.classList.add("rag-file-delete");
      deleteBtn.textContent = "Eliminar";
      deleteBtn.onclick = () => handleRagDelete(file.filename);

      item.appendChild(info);
      item.appendChild(deleteBtn);

      ragFilesList.appendChild(item);
    });
  }

  function handleRagToggle() {
    if (ragToggle.checked) {
      showStatus("RAG activado - Se usarán los documentos indexados");
    } else {
      showStatus("RAG desactivado");
    }
  }

  async function handleRagUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith(".pdf")) {
      alert("Solo se permiten archivos PDF");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      showStatus("Subiendo PDF...");
      const response = await fetch(`${API_BASE}/rag/upload`, {
        method: "POST",
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        showStatus(`✓ ${data.filename} subido. Indexando...`);
        
        // Auto-indexar después de subir
        await handleRagIndex();
      } else {
        const error = await response.json();
        showStatus(`Error: ${error.detail}`);
      }
    } catch (error) {
      showStatus("Error subiendo PDF");
      console.error(error);
    }

    // Limpiar input
    ragFileInput.value = "";
  }

  async function handleRagIndex() {
    if (ragIndexBtn) ragIndexBtn.disabled = true;
    
    try {
      showStatus("Indexando documentos (esto puede tardar)...");
      
      const response = await fetch(`${API_BASE}/rag/index`, {
        method: "POST"
      });

      if (response.ok) {
        const data = await response.json();
        
        if (data.status === "success") {
          showStatus(`✓ Indexados ${data.total_chunks} chunks de ${data.total_files} archivos`);
          await loadRagStatus();
        } else {
          showStatus("No se encontraron PDFs para indexar");
        }
      } else {
        showStatus("Error indexando documentos");
      }
    } catch (error) {
      showStatus("Error en indexación");
      console.error(error);
    }

    if (ragIndexBtn) ragIndexBtn.disabled = false;
  }

  async function handleRagClear() {
    if (!confirm("¿Eliminar todo el índice RAG? Los PDFs se mantendrán.")) {
      return;
    }

    try {
      showStatus("Limpiando índice...");
      
      const response = await fetch(`${API_BASE}/rag/clear`, {
        method: "DELETE"
      });

      if (response.ok) {
        showStatus("✓ Índice limpiado");
        await loadRagStatus();
      } else {
        showStatus("Error limpiando índice");
      }
    } catch (error) {
      showStatus("Error en limpieza");
      console.error(error);
    }
  }

  async function handleRagDelete(filename) {
    if (!confirm(`¿Eliminar ${filename}?`)) {
      return;
    }

    try {
      showStatus(`Eliminando ${filename}...`);
      
      const response = await fetch(`${API_BASE}/rag/document/${encodeURIComponent(filename)}`, {
        method: "DELETE"
      });

      if (response.ok) {
        showStatus(`✓ ${filename} eliminado`);
        await loadRagStatus();
      } else {
        showStatus("Error eliminando documento");
      }
    } catch (error) {
      showStatus("Error en eliminación");
      console.error(error);
    }
  }

  // Actualizar admin panel cuando se abre
  const originalAdminBtnClick = adminBtn.onclick;
  adminBtn.onclick = async function(e) {
    if (originalAdminBtnClick) originalAdminBtnClick.call(this, e);
    await loadRagStatus();
  };
})();
