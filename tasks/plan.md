# Plan de Implementación: TASK-004 — Mando Web Táctil (D-Pad + Botones A/B)

> **Estado**: Aprobado / En Ejecución  
> **Épica**: EPIC-02 (Mobile Web Controller)  
> **Prioridad**: P0  
> **Objetivo**: Construir el mando web táctil optimizado para smartphones con cruceta digital (D-pad), dos botones de acción grandes (A y B), soporte multi-touch sin bloqueos, retroalimentación háptica y envío de eventos en tiempo real al servidor WebSocket.

---

## 1. Decisiones Consolidadas
- **Flujo de Pantallas**: Vista de mando directa al conectarse. El jugador introduce su apodo y entra inmediatamente a la pantalla de control del juego (`#controller-screen`). La barra superior compacta contiene el avatar en miniatura, el apodo, el botón para cambiar de orientación (`🔄 Girar mando`), el botón para saludar en la tele ("👋 Saludar") y el botón para desconectar o cambiar de nombre.
- **Diseño del Mando**: Formato vertical ergonómico (estilo consola portátil retro / Game Boy) con D-Pad cruceta arriba y botones de acción A y B debajo. Toda la pantalla del móvil queda ocupada sin márgenes residuales ni desbordamientos.
- **Prevención de Scroll y Gestos**: Bloqueo absoluto de scroll, pull-to-refresh y zoom mediante `touch-action: none; overscroll-behavior: none;` en `html, body` y prevención de eventos táctiles (`touchmove`, `touchstart`) con `e.preventDefault()` en el controlador web.
- **Barra Superior**: Chip del jugador con avatar miniatura y apodo, botón para saludar en la tele ("👋 Saludar") y botón para desconectar ("✕").
- **D-Pad**: 4 direcciones cardinales clásicas (`up`, `down`, `left`, `right`, o `none` al soltar), permitiendo arrastre continuo del pulgar sobre la cruceta sin necesidad de levantar el dedo.
- **Botones de Acción**: Botones A y B ergonómicos en la zona derecha. Botón A destacado (estilo jump/confirm) y botón B (estilo run/cancel/action secondary).
- **Multi-Touch Real**: `Touch.identifier` independiente para el D-pad y para cada botón, garantizando que pulsar una dirección y un botón simultáneamente funcione sin retraso ni bloqueo.
- **Teclado en Desktop (Fallback de Desarrollo)**: `WASD` / Flechas para D-Pad, `J` / `Z` para Botón A, `K` / `X` para Botón B.
- **Feedback Háptico**: `navigator.vibrate(15)` en pulsaciones y cambios de dirección.
- **Protocolo WebSocket**:
  - `{"type": "input", "action": "press", "button": "a" | "b"}`
  - `{"type": "input", "action": "release", "button": "a" | "b"}`
  - `{"type": "input", "action": "direction_change", "direction": "up" | "down" | "left" | "right" | "none"}`

---

## 2. Tareas de Implementación

- [x] **Tarea 1: Backend (`src/state.py` y `src/server.py`)**
  - Añadir `input_state` y `last_input_at` al modelo `Player`.
  - Implementar `update_player_input` en `LobbyState`.
  - Procesar eventos `input` en el WebSocket handler de `server.py`.
  - Crear pruebas exhaustivas en `tests/test_server.py`.

- [x] **Tarea 2: Frontend HTML & CSS (`src/web/index.html` y `src/web/style.css`)**
  - Crear la vista `#controller-screen` con layout ergonómico (barra superior con micro-avatar, D-Pad a la izquierda, botones A y B a la derecha).
  - Estilos retro-cute con sombras duras, estados `:active` / `.is-active`, dimensiones táctiles mínimas adecuadas (>= 60px), prevención estricta de zoom/scroll (`touch-action: none`).
  - Adaptación responsive para pantallas verticales y horizontales (landscape mode).
  - Selector/botón de alternancia de orientación (`#ctrl-orientation-btn`).

- [x] **Tarea 3: Lógica del Mando en JavaScript (`src/web/app.js`)**
  - Manejo multi-touch con rastreo por `touch.identifier` para D-Pad y botones A/B.
  - Soporte de arrastre continuo en D-Pad.
  - Envío de eventos en tiempo real con WebSocket (`press`, `release`, `direction_change`).
  - Vibración háptica con `navigator.vibrate`.
  - Soporte para testing con teclado en desktop.
  - Lógica de alternancia entre modo horizontal y vertical persistida en `localStorage`.

- [x] **Tarea 4: Verificación, Tests y Cierre de la Tarea en el Harness**
  - Ejecutar `pytest` y verificar que todos los tests pasen (13 de 13 tests pasan).
  - Actualizar `harness/tasks/TASK-004-mobile-dpad-controller.md` y `tasks/todo.md`.
  - Verificar el estado en `harness.py status`.
