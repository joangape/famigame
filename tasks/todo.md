# Famigame Stage 1 — Task Checklist

## Task 1: Estado del Lobby y Servidor HTTP/WebSocket
**Description:** Crear el modelo de estado compartido (`LobbyState`, `Player`) y el servidor `aiohttp` que sirve la webapp móvil y gestiona las conexiones WebSocket en tiempo real (`/ws`).

**Acceptance criteria:**
- [x] `LobbyState` asigna número incremental, apodo por defecto (`"Jugador N"` si viene vacío, truncado a 16 caracteres), color sólido y forma geométrica de la paleta retro-cute.
- [x] El endpoint `/ws` acepta mensajes `{"type": "join", "name": "..."}`, responde con `{"type": "joined", "player": ...}`, procesa `{"type": "ping"}` actualizando `last_ping_at`, y elimina al jugador automáticamente al cerrarse el WebSocket.
- [x] `get_local_ip()` detecta la IP de la red local sin fallar si no hay red externa.

**Verification:**
- [x] Tests pass: `.venv/bin/pytest tests/test_server.py -v`

---

## Task 2: Webapp Móvil Retro-Cute
**Description:** Construir la aplicación web para smartphones (`src/web/index.html`, `src/web/style.css`, `src/web/app.js`) con estética retro/cute de formas sencillas y colores sólidos.

**Acceptance criteria:**
- [x] Muestra un campo de texto opcional para apodo (recordado en `localStorage`) y un botón grande "¡Conectarme!".
- [x] Al conectarse por WebSocket a `/ws`, muestra la tarjeta del jugador con su color asignado, su avatar geométrico con carita feliz en SVG, su nombre/número y un botón "¡Saludar en la tele!" que envía `{"type": "ping"}` y vibra ligeramente si el dispositivo lo soporta.
- [x] Si se desconecta o pulsa "Desconectar", vuelve limpiamente a la pantalla inicial conservando su apodo en el campo de texto.

**Verification:**
- [x] `GET /` y archivos estáticos se sirven correctamente desde `aiohttp`.
- [x] Verificación de estructura DOM, estilos retro-cute y protocolo WebSocket.

---

## Task 3: Pantalla Principal Pygame-CE (Lobby + QR + Lista Dinámica)
**Description:** Crear la interfaz gráfica en Pygame-CE (`src/host_ui.py` y `main.py`) con ventana 1280x720, código QR nítido con la URL local y lista dinámica de tarjetas de dispositivos conectados con personajes geométricos animados.

**Acceptance criteria:**
- [x] Ventana `1280x720` por defecto con estética retro-cute (fondo crema `#FFF8E7`, bordes gruesos `#2B2D42`, sombras sólidas) y atajo `F` / `F11` para alternar pantalla completa.
- [x] Panel izquierdo con código QR generado dinámicamente (`http://<ip>:<puerto>`) y texto de la URL visible debajo.
- [x] Panel derecho con lista dinámica sin límite fijo que muestra tarjetas con el color, nombre y personaje geométrico con carita de cada jugador conectado, animando un salto y bocadillo `"¡HOLA!"` cuando recibe un `ping`.

**Verification:**
- [x] Tests pass: `SDL_VIDEODRIVER=dummy .venv/bin/pytest tests/test_host_ui.py -v`
- [x] Smoke test de integración: `.venv/bin/python main.py --frames 5` termina con código 0.

---

## Checkpoint: After Tasks 1-3
- [x] Todos los tests pasan (`.venv/bin/pytest -v`)
- [x] `main.py` arranca servidor + ventana Pygame y responde a conexiones WebSocket en vivo

---

## Task 4: Mando Web Táctil (D-Pad + Botones A/B + Modos Horiz/Vert)
**Description:** Construir la interfaz del mando de juego táctil móvil con cruceta digital (D-pad), botones A y B, soporte multi-touch simultáneo, retroalimentación háptica, prevención de gestos y modos horizontal y vertical conmutables.

**Acceptance criteria:**
- [x] Multi-touch funcional: control de dirección y botones A/B simultáneamente sin interferencias ni bloqueos usando `Touch.identifier`.
- [x] Desactivación de gestos de zoom y rebote en iOS Safari y Android Chrome (`touch-action: none`, `user-select: none`, `preventDefault` en eventos táctiles).
- [x] Retroalimentación háptica (vibración sutil en pulsaciones con `navigator.vibrate`).
- [x] Envío de eventos en tiempo real al WebSocket del servidor (`press`, `release`, `direction_change`) y registro síncrono en `LobbyState`/`Player`.
- [x] Dos modos de presentación (Horizontal y Vertical) alternables mediante botón de orientación (`#ctrl-orientation-btn`).
- [x] Atajos de teclado para pruebas de desarrollo en desktop (WASD/Flechas + J/K/Z/X).

**Verification:**
- [x] Tests unitarios y de integración WebSocket pasan: `.venv/bin/pytest tests/test_server.py -v`.
- [x] Verificación de assets estáticos y elementos DOM del mando: `test_static_assets_serving_and_gamepad_dom`.


