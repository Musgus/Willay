(() => {
  const API_BASE = "http://127.0.0.1:8000";
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

  const clientId = ensureClientId();
  updateTemperatureLabel();

  temperatureRange.addEventListener("input", updateTemperatureLabel);

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

  function updateTemperatureLabel() {
    temperatureValue.textContent = Number(temperatureRange.value).toFixed(1);
  }

  function pushMessage(message) {
    history.push(message);
    while (history.length > MAX_CONTEXT) {
      history.splice(1, 1);
    }
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
    messagesContainer.innerHTML = "";
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
})();
