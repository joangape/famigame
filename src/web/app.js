(() => {
  const STORAGE_KEY = "famigame_nickname";

  // Navigation screens
  const connectScreen = document.getElementById("connect-screen");
  const controllerScreen = document.getElementById("controller-screen");
  const connectedScreen = document.getElementById("connected-screen");

  // Connect Screen Elements
  const nameInput = document.getElementById("player-name");
  const connectBtn = document.getElementById("connect-btn");
  const statusMsg = document.getElementById("status-msg");

  // Controller Screen Elements
  const ctrlAvatar = document.getElementById("ctrl-avatar");
  const ctrlBadge = document.getElementById("ctrl-badge");
  const ctrlCapitanBadge = document.getElementById("ctrl-capitan-badge");
  const ctrlName = document.getElementById("ctrl-name");
  const ctrlRoleBanner = document.getElementById("ctrl-role-banner");
  const ctrlPingBtn = document.getElementById("ctrl-ping-btn");
  const ctrlDisconnectBtn = document.getElementById("ctrl-disconnect-btn");
  const ctrlToast = document.getElementById("ctrl-toast");
  const toGamepadBtn = document.getElementById("to-gamepad-btn");

  // Gamepad Elements
  const dpad = document.getElementById("dpad");
  const dpadButtons = Array.from(document.querySelectorAll(".dpad-btn"));
  const btnA = document.getElementById("btn-a");
  const btnB = document.getElementById("btn-b");

  // Connected Screen (Legacy/Fallback) Elements
  const playerCard = document.getElementById("player-card");
  const playerBadge = document.getElementById("player-badge");
  const avatarContainer = document.getElementById("avatar-container");
  const playerNameDisplay = document.getElementById("player-name-display");
  const pongFeedback = document.getElementById("pong-feedback");
  const pingBtn = document.getElementById("ping-btn");
  const disconnectBtn = document.getElementById("disconnect-btn");

  // WebSocket and Session State
  let socket = null;
  let intentionalClose = false;
  let toastTimer = null;

  // Controller Input State
  let currentDirection = "none";
  const buttonStates = { a: false, b: false };
  let dpadTouchId = null;
  const buttonTouches = new Map(); // touchId -> "a" | "b"

  // Pre-populate nickname
  try {
    const savedName = localStorage.getItem(STORAGE_KEY);
    if (savedName) {
      nameInput.value = savedName;
    }
  } catch (_) {
    // Ignore storage restrictions
  }

  function vibrate(ms = 15) {
    if (navigator.vibrate) {
      try {
        navigator.vibrate(ms);
      } catch (_) {}
    }
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

  function showToast(text, durationMs = 1200) {
    if (!ctrlToast) return;
    ctrlToast.textContent = text;
    ctrlToast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      ctrlToast.hidden = true;
    }, durationMs);
  }

  function showConnectScreen(notice = "", isError = false) {
    document.body.classList.remove("has-controller-active");
    document.documentElement.classList.remove("has-controller-active");
    if (controllerScreen) controllerScreen.hidden = true;
    if (connectedScreen) connectedScreen.hidden = true;
    connectScreen.hidden = false;
    connectBtn.disabled = false;
    connectBtn.textContent = "¡CONECTARME!";
    resetInputState();
    if (ctrlCapitanBadge) ctrlCapitanBadge.hidden = true;
    if (ctrlRoleBanner) {
      ctrlRoleBanner.hidden = true;
      ctrlRoleBanner.textContent = "";
    }
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

  function createAvatarSvg(shape, color, size = 120) {
    const faceY = shape === "triangle" || shape === "drop" ? 68 : 60;
    const bodyMarkup = buildShapeMarkup(shape, color);

    return `
      <svg class="avatar-svg" viewBox="0 0 120 120" width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Avatar del jugador">
        ${bodyMarkup}
        <ellipse cx="39" cy="${faceY + 6}" rx="6.5" ry="4" fill="#FF758F" opacity="0.85" />
        <ellipse cx="81" cy="${faceY + 6}" rx="6.5" ry="4" fill="#FF758F" opacity="0.85" />
        <circle cx="45" cy="${faceY - 3}" r="5.5" fill="#2B2D42" />
        <circle cx="43.2" cy="${faceY - 5}" r="2" fill="#FFFFFF" />
        <circle cx="75" cy="${faceY - 3}" r="5.5" fill="#2B2D42" />
        <circle cx="73.2" cy="${faceY - 5}" r="2" fill="#FFFFFF" />
        <path d="M 51 ${faceY + 4} Q 60 ${faceY + 14} 69 ${faceY + 4}" fill="none" stroke="#2B2D42" stroke-width="4.5" stroke-linecap="round" />
      </svg>
    `;
  }

  function renderAvatar(shape, color) {
    if (avatarContainer) {
      avatarContainer.innerHTML = createAvatarSvg(shape, color, 120);
    }
    if (ctrlAvatar) {
      ctrlAvatar.innerHTML = createAvatarSvg(shape, color, 38);
    }
  }

  function renderPlayerJoined(player) {
    const rawColor = String(player.color || "#FF5964");
    const color = /^[#a-zA-Z0-9(),.\s%-]+$/.test(rawColor) ? rawColor : "#FF5964";
    const shape = player.shape || "circle";
    const number = player.number || 1;
    const name = player.name || `Jugador ${number}`;

    // Update Connected Screen
    if (playerCard) playerCard.style.setProperty("--player-accent", color);
    if (playerBadge) playerBadge.textContent = `JUGADOR #${number}`;
    if (playerNameDisplay) playerNameDisplay.textContent = name;
    if (pongFeedback) {
      pongFeedback.textContent = "¡Conectado a la tele! 📺";
      pongFeedback.classList.remove("is-pop");
    }

    // Update Controller Screen
    if (ctrlBadge) ctrlBadge.textContent = `JUGADOR #${number}`;
    if (ctrlName) ctrlName.textContent = name;
    renderAvatar(shape, color);

    const isCap = Boolean(player.is_capitan);
    if (ctrlCapitanBadge) ctrlCapitanBadge.hidden = !isCap;
    if (ctrlRoleBanner) {
      ctrlRoleBanner.hidden = false;
      ctrlRoleBanner.classList.toggle("is-capitan", isCap);
      if (isCap) {
        ctrlRoleBanner.textContent = "👑 Eres el Capitán";
      } else {
        ctrlRoleBanner.textContent = "Esperando al Capitán para iniciar...";
      }
    }

    // Direct controller activation
    connectScreen.hidden = true;
    if (connectedScreen) connectedScreen.hidden = true;
    controllerScreen.hidden = false;
    document.body.classList.add("has-controller-active");
    document.documentElement.classList.add("has-controller-active");

    showToast("¡Mando listo! 🎮", 1000);
  }

  function sendWs(payload) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload));
    }
  }

  // =========================================================================
  // Gamepad Input Logic (TASK-004)
  // =========================================================================

  function resetInputState() {
    currentDirection = "none";
    buttonStates.a = false;
    buttonStates.b = false;
    dpadTouchId = null;
    buttonTouches.clear();
    dpadButtons.forEach((btn) => btn.classList.remove("is-active"));
    if (btnA) btnA.classList.remove("is-active");
    if (btnB) btnB.classList.remove("is-active");
  }

  function setDpadDirection(newDir) {
    if (newDir === currentDirection) return;
    currentDirection = newDir;

    dpadButtons.forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.dir === currentDirection);
    });

    if (currentDirection !== "none") {
      vibrate(15);
    }

    sendWs({
      type: "input",
      action: "direction_change",
      direction: currentDirection,
    });
  }

  function calculateDpadDirection(clientX, clientY) {
    if (!dpad) return "none";
    const rect = dpad.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = clientX - cx;
    const dy = clientY - cy;

    // Deadzone in the center
    const deadzone = Math.min(rect.width, rect.height) * 0.16;
    if (Math.hypot(dx, dy) < deadzone) {
      return "none";
    }

    if (Math.abs(dx) > Math.abs(dy)) {
      return dx > 0 ? "right" : "left";
    } else {
      return dy > 0 ? "down" : "up";
    }
  }

  function setButtonState(button, isPressed) {
    if (button !== "a" && button !== "b") return;
    if (buttonStates[button] === isPressed) return;

    buttonStates[button] = isPressed;
    const targetBtn = button === "a" ? btnA : btnB;
    if (targetBtn) {
      targetBtn.classList.toggle("is-active", isPressed);
    }

    if (isPressed) {
      vibrate(18);
    }

    sendWs({
      type: "input",
      action: isPressed ? "press" : "release",
      button,
    });
  }

  // Multi-Touch Handlers for D-Pad
  if (dpad) {
    dpad.addEventListener("touchstart", (e) => {
      e.preventDefault();
      if (dpadTouchId === null && e.changedTouches.length > 0) {
        const touch = e.changedTouches[0];
        dpadTouchId = touch.identifier;
        setDpadDirection(calculateDpadDirection(touch.clientX, touch.clientY));
      }
    }, { passive: false });
  }

  // Prevent any scrolling gesture while controller screen is active
  if (controllerScreen) {
    controllerScreen.addEventListener("touchstart", (e) => {
      if (e.target.closest("#dpad") || e.target.closest(".action-cluster") || e.target.closest(".gamepad-surface")) {
        e.preventDefault();
      }
    }, { passive: false });

    controllerScreen.addEventListener("touchmove", (e) => {
      e.preventDefault();
    }, { passive: false });
  }

  window.addEventListener("touchmove", (e) => {
    if (controllerScreen && !controllerScreen.hidden) {
      e.preventDefault();
    }
    if (dpadTouchId === null) return;
    for (let i = 0; i < e.touches.length; i++) {
      const touch = e.touches[i];
      if (touch.identifier === dpadTouchId) {
        setDpadDirection(calculateDpadDirection(touch.clientX, touch.clientY));
        break;
      }
    }
  }, { passive: false });

  function handleTouchEndOrCancel(e) {
    if (dpadTouchId !== null) {
      for (let i = 0; i < e.changedTouches.length; i++) {
        if (e.changedTouches[i].identifier === dpadTouchId) {
          dpadTouchId = null;
          setDpadDirection("none");
          break;
        }
      }
    }

    for (let i = 0; i < e.changedTouches.length; i++) {
      const id = e.changedTouches[i].identifier;
      if (buttonTouches.has(id)) {
        const btnKey = buttonTouches.get(id);
        buttonTouches.delete(id);
        // Only release if no other touch is holding this button
        let stillHeld = false;
        for (const heldBtn of buttonTouches.values()) {
          if (heldBtn === btnKey) {
            stillHeld = true;
            break;
          }
        }
        if (!stillHeld) {
          setButtonState(btnKey, false);
        }
      }
    }
  }

  window.addEventListener("touchend", handleTouchEndOrCancel, { passive: true });
  window.addEventListener("touchcancel", handleTouchEndOrCancel, { passive: true });

  // Touch Handlers for Action Buttons A & B
  function setupActionButtonTouch(element, btnKey) {
    if (!element) return;
    element.addEventListener("touchstart", (e) => {
      e.preventDefault();
      for (let i = 0; i < e.changedTouches.length; i++) {
        const touch = e.changedTouches[i];
        buttonTouches.set(touch.identifier, btnKey);
      }
      setButtonState(btnKey, true);
    }, { passive: false });
  }

  setupActionButtonTouch(btnA, "a");
  setupActionButtonTouch(btnB, "b");

  // Mouse / Pointer fallback for D-Pad
  dpadButtons.forEach((btn) => {
    btn.addEventListener("mousedown", (e) => {
      e.preventDefault();
      setDpadDirection(btn.dataset.dir || "none");
    });
  });

  window.addEventListener("mouseup", () => {
    if (dpadTouchId === null && currentDirection !== "none") {
      setDpadDirection("none");
    }
    if (buttonStates.a && buttonTouches.size === 0) setButtonState("a", false);
    if (buttonStates.b && buttonTouches.size === 0) setButtonState("b", false);
  });

  // Mouse fallback for Action Buttons
  if (btnA) {
    btnA.addEventListener("mousedown", (e) => {
      e.preventDefault();
      setButtonState("a", true);
    });
  }
  if (btnB) {
    btnB.addEventListener("mousedown", (e) => {
      e.preventDefault();
      setButtonState("b", true);
    });
  }

  // Keyboard Desktop Fallback
  const KEY_DIR_MAP = {
    ArrowUp: "up",
    KeyW: "up",
    ArrowDown: "down",
    KeyS: "down",
    ArrowLeft: "left",
    KeyA: "left",
    ArrowRight: "right",
    KeyD: "right",
  };

  const KEY_BTN_MAP = {
    KeyJ: "a",
    KeyZ: "a",
    Space: "a",
    KeyK: "b",
    KeyX: "b",
  };

  window.addEventListener("keydown", (e) => {
    if (document.activeElement === nameInput) return;
    if (controllerScreen.hidden) return;

    if (KEY_DIR_MAP[e.code]) {
      e.preventDefault();
      if (!e.repeat) {
        setDpadDirection(KEY_DIR_MAP[e.code]);
      }
    } else if (KEY_BTN_MAP[e.code]) {
      e.preventDefault();
      if (!e.repeat) {
        setButtonState(KEY_BTN_MAP[e.code], true);
      }
    }
  });

  window.addEventListener("keyup", (e) => {
    if (document.activeElement === nameInput) return;
    if (controllerScreen.hidden) return;

    if (KEY_DIR_MAP[e.code] && currentDirection === KEY_DIR_MAP[e.code]) {
      setDpadDirection("none");
    } else if (KEY_BTN_MAP[e.code]) {
      setButtonState(KEY_BTN_MAP[e.code], false);
    }
  });

  // =========================================================================
  // Connection and Session Management
  // =========================================================================

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
      } catch (_) {}
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
      } else if (data.type === "role_update") {
        const isCap = Boolean(data.is_capitan);
        if (ctrlCapitanBadge) ctrlCapitanBadge.hidden = !isCap;
        if (ctrlRoleBanner) {
          ctrlRoleBanner.hidden = false;
          ctrlRoleBanner.classList.toggle("is-capitan", isCap);
          if (isCap) {
            ctrlRoleBanner.textContent = "👑 Eres el Capitán";
            vibrate(30);
            showToast("¡Ahora eres el Capitán! 👑", 1500);
          } else {
            ctrlRoleBanner.textContent = "Esperando al Capitán " + (data.capitan_name || "") + " para iniciar...";
          }
        }
      } else if (data.type === "pong") {
        if (pongFeedback) {
          pongFeedback.textContent = "¡Saludo enviado a la tele! ✨";
          pongFeedback.classList.add("is-pop");
        }
        showToast("¡Saludo enviado a la tele! 📺✨", 1000);
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

  function triggerPing() {
    vibrate(35);
    showToast("👋 ¡Saludando en la tele!", 900);
    sendWs({ type: "ping" });
  }

  if (ctrlPingBtn) ctrlPingBtn.addEventListener("click", triggerPing);
  if (pingBtn) pingBtn.addEventListener("click", triggerPing);

  function handleDisconnect() {
    intentionalClose = true;
    if (socket) {
      socket.close();
      socket = null;
    }
    showConnectScreen("¡Cambia tu apodo y vuelve cuando quieras!", false);
  }

  if (ctrlDisconnectBtn) ctrlDisconnectBtn.addEventListener("click", handleDisconnect);
  if (disconnectBtn) disconnectBtn.addEventListener("click", handleDisconnect);

  if (toGamepadBtn) {
    toGamepadBtn.addEventListener("click", () => {
      if (connectedScreen) connectedScreen.hidden = true;
      controllerScreen.hidden = false;
      document.body.classList.add("has-controller-active");
      document.documentElement.classList.add("has-controller-active");
    });
  }
})();
