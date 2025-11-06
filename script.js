(() => {
  const API_BASE = "http://127.0.0.1:8000";
  const PROMPT_TEMPLATES = {
    "ayuda-matematicas": "Explícame paso a paso cómo resolver un sistema de ecuaciones lineales de dos incógnitas.",
    "ayuda-fisica": "Ayúdame a diferenciar la cinemática de la dinámica con ejemplos sencillos.",
    "ayuda-programacion": "Explícame qué es la recursión y muéstrame un ejemplo en Python.",
    "ayuda-historia": "Resume las causas principales de la Revolución Francesa en menos de 6 puntos.",
    "ayuda-literatura": "Analiza el conflicto central de 'La casa de Bernarda Alba' en lenguaje sencillo.",
    "ayuda-quimica": "Describe el proceso de enlace covalente y da un ejemplo práctico."
  };

  const HISTORY_STORAGE_KEY = "ollamaChatSessions";
  const ACTIVE_SESSION_KEY = "ollamaActiveSessionId";
  const LOGS_STORAGE_KEY = "ollamaChatLogs";
  const STATS_STORAGE_KEY = "ollamaChatStats";
  const THEME_STORAGE_KEY = "ollamaTheme";

  const systemMessage = { role: "system", content: "Responde en frases cortas." };
  const history = [systemMessage];
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
  const sidebar = document.getElementById("sidebar");
  const toggleSidebarBtn = document.getElementById("toggleSidebar");
  const showSidebarBtn = document.getElementById("showSidebar");
  const promptButtons = document.querySelectorAll(".prompt-btn");
  const chatHistoryList = document.getElementById("chatHistory");
  const sessionTitle = document.getElementById("sessionTitle");
  const themeToggle = document.getElementById("themeToggle");
  const welcomeMarkup = messagesContainer ? messagesContainer.innerHTML : "";

  const clientId = ensureClientId();

  let sessions = loadSessions();
  let logs = loadLogs();
  let stats = loadStats();
  let activeSessionId = null;
  let currentTheme = loadThemePreference();

  initialize();

  function initialize() {
    applyTheme(currentTheme, false);
    updateTemperatureLabel();
    initializePrompts();
    initializeSidebar();
    initializeHistory();
    exposeAdminInterface();

    temperatureRange?.addEventListener("input", updateTemperatureLabel);

    themeToggle?.addEventListener("click", () => {
      currentTheme = currentTheme === "dark" ? "light" : "dark";
      applyTheme(currentTheme);
    });

    chatForm?.addEventListener("submit", async (event) => {
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
      renderMessageBubble("user", rawMessage);
      pushMessage({ role: "user", content: rawMessage });
      addLogEntry("Usuario", rawMessage);

      try {
        await streamAssistantReply();
      } catch (error) {
        showStatus(error.message || "Error interno");
      }
    });

    newChatBtn?.addEventListener("click", async () => {
      if (isStreaming) {
        return;
      }

      clearConversation();
      renderMessageBubble("assistant", "Historial reiniciado.");
      addLogEntry("Sistema", "Sesión reiniciada");
      await notifyReset();
    });

    chatHistoryList?.addEventListener("click", async (event) => {
      const item = event.target.closest(".history-item");
      if (!item || !item.dataset.sessionId || item.classList.contains("disabled")) {
        return;
      }
      if (isStreaming) {
        showStatus("Espera a que termine la respuesta actual");
        return;
      }
      const sessionId = item.dataset.sessionId;
      if (sessionId === activeSessionId) {
        return;
      }
      activeSessionId = sessionId;
      saveActiveSession();
      const session = getActiveSession();
      if (!session) {
        return;
      }
      setHistoryFromSession(session);
      renderConversationFromHistory();
      renderChatHistory();
      updateSessionTitle(session.title || "Nueva sesión");
      showStatus("Sesión cargada");
      await notifyReset();
    });
  }

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

  function initializePrompts() {
    promptButtons.forEach((button) => {
      button.addEventListener("click", () => {
        if (isStreaming) {
          return;
        }
        const template = PROMPT_TEMPLATES[button.dataset.prompt] || button.textContent.trim();
        if (!template) {
          return;
        }
        messageInput.value = template;
        messageInput.focus();
      });
    });
  }

  function initializeSidebar() {
    toggleSidebarBtn?.addEventListener("click", () => {
      sidebar?.classList.add("hidden");
      showSidebarBtn?.classList.remove("hidden");
    });

    showSidebarBtn?.addEventListener("click", () => {
      sidebar?.classList.remove("hidden");
      showSidebarBtn.classList.add("hidden");
    });
  }

  function initializeHistory() {
    if (!sessions.length) {
      const session = createNewSession();
      activeSessionId = session.id;
    } else {
      const storedId = localStorage.getItem(ACTIVE_SESSION_KEY);
      const existing = sessions.find((session) => session.id === storedId);
      activeSessionId = existing ? existing.id : sessions[0].id;
    }
    saveActiveSession();

    const activeSession = getActiveSession();
    if (activeSession && activeSession.messages.length) {
      setHistoryFromSession(activeSession);
      renderConversationFromHistory();
      updateSessionTitle(activeSession.title || "Nueva sesión");
    } else {
      insertWelcomeMessage();
      updateSessionTitle("Nueva sesión");
    }

    renderChatHistory();
    stats.totalSessions = sessions.length;
    persistStats();
  }

  function loadThemePreference() {
    try {
      const stored = localStorage.getItem(THEME_STORAGE_KEY);
      if (stored === "dark" || stored === "light") {
        return stored;
      }
    } catch (error) {
      // Ignored: fallback handled below.
    }
    if (typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
    return "light";
  }

  function applyTheme(theme, persist = true) {
    const normalized = theme === "dark" ? "dark" : "light";
    const root = document.body;
    if (root) {
      root.dataset.theme = normalized;
    }
    updateThemeToggleLabel(normalized);
    if (persist) {
      try {
        localStorage.setItem(THEME_STORAGE_KEY, normalized);
      } catch (error) {
        // Storage failures can be ignored.
      }
    }
    currentTheme = normalized;
  }

  function updateThemeToggleLabel(theme) {
    if (!themeToggle) {
      return;
    }
    if (theme === "dark") {
      themeToggle.textContent = "☀️";
      themeToggle.title = "Cambiar a tema claro";
    } else {
      themeToggle.textContent = "🌙";
      themeToggle.title = "Cambiar a tema oscuro";
    }
  }

  function exposeAdminInterface() {
    if (typeof globalThis === "undefined") {
      return;
    }

    const api = Object.freeze({
      getLogs: () => logs.slice(),
      clearLogs: () => {
        logs = [];
        persistLogs();
        if (typeof console !== "undefined") {
          console.info("[WillayAdmin] Logs borrados");
        }
      },
      exportLogs: () =>
        logs
          .slice()
          .sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0))
          .map((entry) => `[${formatDateTime(entry.timestamp)}] ${entry.author}: ${entry.content}`)
          .join("\n\n"),
      getStats: () => ({
        ...stats,
        totalSessions: sessions.length
      }),
      resetStats: () => {
        stats = {
          totalMessages: 0,
          totalSessions: sessions.length,
          modelUsage: {},
          totalResponseTimeMs: 0,
          responsesCompleted: 0
        };
        persistStats();
        return stats;
      },
      listSessions: () =>
        sessions.map((session) => ({
          id: session.id,
          title: session.title,
          createdAt: session.createdAt,
          updatedAt: session.updatedAt,
          messages: session.messages.length
        })),
      openSession: (id) => {
        if (isStreaming) {
          console.warn("[WillayAdmin] Espera a que la respuesta actual termine.");
          return false;
        }
        const session = sessions.find((item) => item.id === id);
        if (!session) {
          console.warn(`[WillayAdmin] Sesión no encontrada: ${id}`);
          return false;
        }
        activeSessionId = session.id;
        saveActiveSession();
        setHistoryFromSession(session);
        renderConversationFromHistory();
        renderChatHistory();
        updateSessionTitle(session.title || "Nueva sesión");
        showStatus("Sesión cargada desde consola");
        return true;
      },
      newSession: () => {
        if (isStreaming) {
          console.warn("[WillayAdmin] Espera a que la respuesta actual termine.");
          return null;
        }
        clearConversation();
        showStatus("Nueva sesión creada desde consola");
        return getActiveSession();
      },
      setTheme: (theme) => applyTheme(theme)
    });

    Object.defineProperty(globalThis, "WillayAdmin", {
      value: api,
      configurable: true,
      writable: false
    });

    if (typeof console !== "undefined") {
      console.info("WillayAdmin disponible en consola. Usa WillayAdmin.getLogs() para comenzar.");
    }
  }

  function updateTemperatureLabel() {
    temperatureValue.textContent = Number(temperatureRange.value).toFixed(1);
  }

  function pushMessage(message) {
    history.push(message);
    trimHistory();
    if (message.role !== "system") {
      recordMessageStats();
    }
    persistSession();
  }

  function trimHistory() {
    while (history.length > MAX_CONTEXT) {
      if (history.length <= 2) {
        history.splice(1);
        break;
      }
      const first = history[1];
      const second = history[2];
      if (second && second.role !== first.role) {
        history.splice(1, 2);
      } else {
        history.splice(1, 1);
      }
    }
  }

  function showStatus(text) {
    statusText.textContent = text || "";
  }

  function renderMessageBubble(role, content, isError = false) {
    const welcomeNode = messagesContainer.querySelector(".welcome-message");
    if (welcomeNode) {
      welcomeNode.remove();
    }
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
    const startTime = performance.now();

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

      recordModelUsage(payload.model);

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
      addLogEntry("Willay", assistantText);
      recordResponseTime(performance.now() - startTime);
      showStatus("Listo");
    } catch (error) {
      assistantBubble.textContent = error.message || "Error interno";
      assistantBubble.classList.add("message-error");
      addLogEntry("Error", error.message || "Error interno");
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
    const messages = history.map((item) => ({ role: item.role, content: item.content }));
    return {
      clientId,
      model: modelSelect.value,
      temperature: Number(temperatureRange.value),
      messages
    };
  }

  function clearConversation() {
    history.splice(0, history.length, systemMessage);
    insertWelcomeMessage();
    startNewSession();
    showStatus("Nuevo chat listo");
  }

  function insertWelcomeMessage() {
    if (!messagesContainer) {
      return;
    }
    if (!welcomeMarkup) {
      messagesContainer.innerHTML = "";
      return;
    }
    messagesContainer.innerHTML = welcomeMarkup;
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

  function loadSessions() {
    try {
      const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
      if (!raw) {
        return [];
      }
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) {
        return [];
      }
      return parsed.map((session) => ({
        id: session.id || generateSessionId(),
        title: session.title || "Nueva sesión",
        createdAt: session.createdAt || Date.now(),
        updatedAt: session.updatedAt || session.createdAt || Date.now(),
        messages: Array.isArray(session.messages)
          ? session.messages
              .filter((message) => message && message.role && message.content)
              .map((message) => ({ role: message.role, content: message.content }))
          : []
      }));
    } catch (error) {
      return [];
    }
  }

  function saveSessions() {
    sessions.sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(sessions));
    persistStats();
  }

  function createNewSession() {
    const now = Date.now();
    const session = {
      id: generateSessionId(),
      title: "Nueva sesión",
      createdAt: now,
      updatedAt: now,
      messages: []
    };
    sessions.push(session);
    saveSessions();
    return session;
  }

  function startNewSession() {
    const session = createNewSession();
    activeSessionId = session.id;
    saveActiveSession();
    renderChatHistory();
    updateSessionTitle("Nueva sesión");
    persistSession();
  }

  function persistSession() {
    const session = getActiveSession();
    if (!session) {
      return;
    }
    session.messages = history
      .slice(1)
      .map((message) => ({ role: message.role, content: message.content }));
    const firstUser = session.messages.find((message) => message.role === "user");
    if (firstUser && (!session.title || session.title === "Nueva sesión")) {
      session.title = generateSessionTitle(firstUser.content);
    }
    session.updatedAt = Date.now();
    saveSessions();
    renderChatHistory();
    updateSessionTitle(session.title || "Nueva sesión");
  }

  function setHistoryFromSession(session) {
    history.splice(0, history.length, systemMessage);
    session.messages.forEach((message) => {
      history.push({ role: message.role, content: message.content });
    });
  }

  function renderConversationFromHistory() {
    if (!messagesContainer) {
      return;
    }
    messagesContainer.innerHTML = "";
    const conversation = history.slice(1);
    if (!conversation.length) {
      insertWelcomeMessage();
      return;
    }
    conversation.forEach((message) => {
      renderMessageBubble(message.role, message.content);
    });
  }

  function renderChatHistory() {
    if (!chatHistoryList) {
      return;
    }
    chatHistoryList.innerHTML = "";
    if (!sessions.length) {
      const emptyState = document.createElement("div");
      emptyState.classList.add("history-item", "disabled");
      emptyState.textContent = "Sin conversaciones";
      chatHistoryList.appendChild(emptyState);
      return;
    }
    sessions
      .slice()
      .sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0))
      .forEach((session) => {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "history-item";
        if (session.id === activeSessionId) {
          item.classList.add("active");
        }
        item.dataset.sessionId = session.id;

        const title = document.createElement("div");
        title.className = "history-item-title";
        title.textContent = session.title || "Nueva sesión";

        const date = document.createElement("div");
        date.className = "history-item-date";
        date.textContent = formatDate(session.updatedAt || Date.now());

        item.appendChild(title);
        item.appendChild(date);
        chatHistoryList.appendChild(item);
      });
  }

  function getActiveSession() {
    return sessions.find((session) => session.id === activeSessionId) || null;
  }

  function saveActiveSession() {
    if (activeSessionId) {
      localStorage.setItem(ACTIVE_SESSION_KEY, activeSessionId);
    }
  }

  function generateSessionId() {
    try {
      return crypto.randomUUID();
    } catch (error) {
      return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    }
  }

  function generateSessionTitle(text) {
    const trimmed = text.trim();
    if (!trimmed) {
      return "Nueva sesión";
    }
    return trimmed.length > 60 ? `${trimmed.slice(0, 57)}...` : trimmed;
  }

  function updateSessionTitle(text) {
    if (sessionTitle) {
      sessionTitle.textContent = text;
    }
  }

  function loadLogs() {
    try {
      const raw = localStorage.getItem(LOGS_STORAGE_KEY);
      if (!raw) {
        return [];
      }
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) {
        return [];
      }
      return parsed
        .filter((entry) => entry && entry.author && entry.content)
        .map((entry) => ({
          id: entry.id || generateSessionId(),
          author: entry.author,
          content: entry.content,
          timestamp: entry.timestamp || Date.now()
        }));
    } catch (error) {
      return [];
    }
  }

  function addLogEntry(author, content) {
    if (!author || !content) {
      return;
    }
    const entry = {
      id: generateSessionId(),
      author,
      content,
      timestamp: Date.now()
    };
    logs.push(entry);
    if (logs.length > 300) {
      logs = logs.slice(-300);
    }
    persistLogs();
    if (typeof console !== "undefined" && console.debug) {
      console.debug(`[Willay][${entry.author}] ${entry.content}`);
    }
  }

  function persistLogs() {
    localStorage.setItem(LOGS_STORAGE_KEY, JSON.stringify(logs));
  }

  function loadStats() {
    try {
      const raw = localStorage.getItem(STATS_STORAGE_KEY);
      if (!raw) {
        return {
          totalMessages: 0,
          totalSessions: 0,
          modelUsage: {},
          totalResponseTimeMs: 0,
          responsesCompleted: 0
        };
      }
      const parsed = JSON.parse(raw);
      return {
        totalMessages: Number(parsed.totalMessages) || 0,
        totalSessions: Number(parsed.totalSessions) || 0,
        modelUsage: parsed.modelUsage && typeof parsed.modelUsage === "object" ? parsed.modelUsage : {},
        totalResponseTimeMs: Number(parsed.totalResponseTimeMs) || 0,
        responsesCompleted: Number(parsed.responsesCompleted) || 0
      };
    } catch (error) {
      return {
        totalMessages: 0,
        totalSessions: 0,
        modelUsage: {},
        totalResponseTimeMs: 0,
        responsesCompleted: 0
      };
    }
  }

  function persistStats() {
    stats.totalSessions = sessions.length;
    localStorage.setItem(STATS_STORAGE_KEY, JSON.stringify(stats));
  }

  function recordMessageStats() {
    stats.totalMessages = (stats.totalMessages || 0) + 1;
    persistStats();
  }

  function recordModelUsage(model) {
    if (!model) {
      return;
    }
    if (!stats.modelUsage) {
      stats.modelUsage = {};
    }
    stats.modelUsage[model] = (stats.modelUsage[model] || 0) + 1;
    persistStats();
  }

  function recordResponseTime(durationMs) {
    stats.totalResponseTimeMs = (stats.totalResponseTimeMs || 0) + durationMs;
    stats.responsesCompleted = (stats.responsesCompleted || 0) + 1;
    persistStats();
  }

  function formatDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString(undefined, {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit"
    });
  }

  function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
  }
})();
