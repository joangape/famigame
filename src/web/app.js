(() => {
  const STORAGE_KEY = "famigame_nickname";

  const connectScreen = document.getElementById("connect-screen");
  const connectedScreen = document.getElementById("connected-screen");
  const nameInput = document.getElementById("player-name");
  const connectBtn = document.getElementById("connect-btn");
  const statusMsg = document.getElementById("status-msg");

  const playerCard = document.getElementById("player-card");
  const playerBadge = document.getElementById("player-badge");
  const avatarContainer = document.getElementById("avatar-container");
  const playerNameDisplay = document.getElementById("player-name-display");
  const pongFeedback = document.getElementById("pong-feedback");
  const pingBtn = document.getElementById("ping-btn");
  const disconnectBtn = document.getElementById("disconnect-btn");

  let socket = null;
  let intentionalClose = false;
  let pongTimer = null;

  // Pre-populate nickname from localStorage
  try {
    const savedName = localStorage.getItem(STORAGE_KEY);
    if (savedName) {
      nameInput.value = savedName;
    }
  } catch (_) {
    // Ignore storage errors in private browsing
  }

  function showStatus(text, isError = false) {
    if (!text) {
      statusMsg.hidden = true;
      statusMsg.textContent = "";
      statusMsg.classList.remove("is-error");
      return;
    }
    statusMsg.textContent = text;
    statusMsg.classList.toggle("is-error", isError);
    statusMsg.hidden = false;
  }

  function showConnectScreen(notice = "", isError = false) {
    connectedScreen.hidden = true;
    connectScreen.hidden = false;
    connectBtn.disabled = false;
    connectBtn.textContent = "¡CONECTARME!";
    showStatus(notice, isError);
  }

  function buildShapeMarkup(shape, color) {
    const stroke = "#2B2D42";
    const strokeWidth = "5";
    switch (shape) {
      case "square":
        return `<rect x="20" y="20" width="80" height="80" rx="18" fill="${color}" stroke="${stroke}" stroke-width="${strokeWidth}" stroke-linejoin="round" />`;
      case "triangle":
        return `<path d="M60 14 L106 96 Q109 102 102 102 L18 102 Q11 102 14 96 Z" fill="${color}" stroke="${stroke}" stroke-width="${strokeWidth}" stroke-linejoin="round" />`;
      case "star":
        return `<polygon points="60,10 73,40 106,43 81,65 88,98 60,81 32,98 39,65 14,43 47,40" fill="${color}" stroke="${stroke}" stroke-width="${strokeWidth}" stroke-linejoin="round" />`;
      case "diamond":
        return `<polygon points="60,12 106,60 60,108 14,60" fill="${color}" stroke="${stroke}" stroke-width="${strokeWidth}" stroke-linejoin="round" />`;
      case "drop":
        return `<path d="M60 12 C60 12 102 56 102 76 A42 42 0 1 1 18 76 C18 56 60 12 60 12 Z" fill="${color}" stroke="${stroke}" stroke-width="${strokeWidth}" stroke-linejoin="round" />`;
      case "circle":
      default:
        return `<circle cx="60" cy="60" r="44" fill="${color}" stroke="${stroke}" stroke-width="${strokeWidth}" />`;
    }
  }

  function renderAvatar(shape, color) {
    const faceY = shape === "triangle" || shape === "drop" ? 68 : 60;
    const bodyMarkup = buildShapeMarkup(shape, color);

    avatarContainer.innerHTML = `
      <svg class="avatar-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Avatar del jugador">
        ${bodyMarkup}
        <!-- Rosy cheeks -->
        <ellipse cx="39" cy="${faceY + 6}" rx="6.5" ry="4" fill="#FF758F" opacity="0.85" />
        <ellipse cx="81" cy="${faceY + 6}" rx="6.5" ry="4" fill="#FF758F" opacity="0.85" />
        <!-- Eyes with cute shine -->
        <circle cx="45" cy="${faceY - 3}" r="5.5" fill="#2B2D42" />
        <circle cx="43.2" cy="${faceY - 5}" r="2" fill="#FFFFFF" />
        <circle cx="75" cy="${faceY - 3}" r="5.5" fill="#2B2D42" />
        <circle cx="73.2" cy="${faceY - 5}" r="2" fill="#FFFFFF" />
        <!-- Happy smile -->
        <path d="M 51 ${faceY + 4} Q 60 ${faceY + 14} 69 ${faceY + 4}" fill="none" stroke="#2B2D42" stroke-width="4.5" stroke-linecap="round" />
      </svg>
    `;
  }

  function triggerAvatarBounce() {
    const svg = avatarContainer.querySelector(".avatar-svg");
    if (!svg) return;
    svg.classList.remove("is-waving");
    void svg.offsetWidth;
    svg.classList.add("is-waving");
  }

  function renderPlayerJoined(player) {
    const rawColor = String(player.color || "#FF5964");
    const color = /^[#a-zA-Z0-9(),.\s%-]+$/.test(rawColor) ? rawColor : "#FF5964";
    const shape = player.shape || "circle";
    const number = player.number || 1;
    const name = player.name || `Jugador ${number}`;

    playerCard.style.setProperty("--player-accent", color);
    playerBadge.textContent = `JUGADOR #${number}`;
    playerNameDisplay.textContent = name;
    pongFeedback.textContent = "¡Conectado a la tele! 📺";
    pongFeedback.classList.remove("is-pop");

    renderAvatar(shape, color);

    connectScreen.hidden = true;
    connectedScreen.hidden = false;
  }

  function connectToGame() {
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const name = nameInput.value.trim().slice(0, 16);
    intentionalClose = false;
    connectBtn.disabled = true;
    connectBtn.textContent = "CONECTANDO...";
    showStatus("Conectando con la tele...", false);

    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${location.host}/ws`;

    try {
      socket = new WebSocket(wsUrl);
    } catch (_) {
      showConnectScreen("No se pudo abrir la conexión. Inténtalo de nuevo.", true);
      return;
    }

    socket.addEventListener("open", () => {
      try {
        localStorage.setItem(STORAGE_KEY, name);
      } catch (_) {
        // Ignore storage errors
      }
      socket.send(JSON.stringify({ type: "join", name }));
    });

    socket.addEventListener("message", (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch (_) {
        return;
      }

      if (data.type === "joined" && data.player) {
        showStatus("");
        renderPlayerJoined(data.player);
      } else if (data.type === "pong") {
        pongFeedback.textContent = "¡Saludo enviado a la tele! ✨";
        pongFeedback.classList.add("is-pop");
        clearTimeout(pongTimer);
        pongTimer = setTimeout(() => {
          pongFeedback.classList.remove("is-pop");
        }, 900);
      }
    });

    socket.addEventListener("close", () => {
      socket = null;
      if (intentionalClose) {
        showConnectScreen("Has salido de la partida. ¡Puedes cambiar tu apodo!", false);
      } else {
        showConnectScreen("Se desconectó de la tele. ¡Toca para volver a entrar!", true);
      }
    });

    socket.addEventListener("error", () => {
      showConnectScreen("No pudimos conectar con la tele. ¿Sigue encendida la partida?", true);
    });
  }

  connectBtn.addEventListener("click", connectToGame);

  nameInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      connectToGame();
    }
  });

  pingBtn.addEventListener("click", () => {
    if (navigator.vibrate) {
      navigator.vibrate(35);
    }
    triggerAvatarBounce();
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "ping" }));
    }
  });

  disconnectBtn.addEventListener("click", () => {
    intentionalClose = true;
    if (socket) {
      socket.close();
      socket = null;
    }
    showConnectScreen("¡Cambia tu apodo y vuelve cuando quieras!", false);
  });
})();
